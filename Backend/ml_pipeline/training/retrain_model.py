"""Train, evaluate, and promote material-specific scrap price quantile models."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder
from sqlalchemy.orm import Session

from ..etl.pipeline_config import FEATURE_VERSION, MIN_SCRAP_HISTORY_DAYS, RANDOM_SEED
from ..etl.trainable import FEATURE_COLUMNS, TARGET, build_trainable_dataset
from ..etl.validation import chronological_split
from ..utils import MODEL_CONTRACT_VERSION, PROMOTION_MAX_VALIDATION_MAE
from .evaluate import quantile_metrics, regression_metrics
from .model_registry import activate_model_version, load_active_model_metadata

QUANTILES = (0.1, 0.5, 0.9)
MATERIAL_COLUMN = "material"
SCRAP_TYPE_COLUMN = "scrap_type"
MIN_MATERIAL_ROWS = 30
MIN_TRAIN_ROWS = 20
MIN_VALIDATION_ROWS = 5
MIN_TEST_ROWS = 5


def _quantile_model(quantile: float, numeric_features: list[str]):
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                make_pipeline(SimpleImputer(strategy="median", add_indicator=True)),
                numeric_features,
            ),
            (
                "scrap_type",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                [SCRAP_TYPE_COLUMN],
            ),
        ],
        remainder="drop",
    )
    estimator = HistGradientBoostingRegressor(
        loss="quantile",
        quantile=quantile,
        random_state=RANDOM_SEED,
        max_iter=150,
        learning_rate=0.05,
        max_leaf_nodes=15,
    )
    return make_pipeline(preprocessor, estimator)


def _ordered_predictions(
    predictions: dict[float, np.ndarray],
) -> dict[float, np.ndarray]:
    matrix = np.sort(
        np.column_stack([predictions[quantile] for quantile in QUANTILES]),
        axis=1,
    )
    return {quantile: matrix[:, index] for index, quantile in enumerate(QUANTILES)}


def _evaluate_predictions(
    targets: pd.Series | np.ndarray,
    predictions: dict[float, np.ndarray],
) -> dict[str, Any]:
    ordered = _ordered_predictions(predictions)
    return {
        "p50": regression_metrics(targets, ordered[0.5]),
        "quantiles": quantile_metrics(targets, ordered),
    }


def _evaluate_by_scrap_type(
    frame: pd.DataFrame,
    targets: np.ndarray,
    predictions: dict[float, np.ndarray],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    categories = frame[SCRAP_TYPE_COLUMN].astype(str).to_numpy()
    for category in sorted(set(categories)):
        mask = categories == category
        result[category] = {
            "rows": int(mask.sum()),
            **_evaluate_predictions(
                targets[mask],
                {quantile: values[mask] for quantile, values in predictions.items()},
            ),
        }
    return result


def _artifact_name(material: str, quantile: float) -> str:
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]
    return f"model_{digest}_p{int(quantile * 100)}.joblib"


def _verify_serialized_models(
    directory: Path,
    material_models: dict[str, dict[float, Any]],
    samples: dict[str, pd.DataFrame],
    expected: dict[str, dict[float, np.ndarray]],
) -> list[str]:
    artifact_files: list[str] = []
    for material, models in material_models.items():
        for quantile, model in models.items():
            filename = _artifact_name(material, quantile)
            path = directory / filename
            if not path.is_file() or path.stat().st_size == 0:
                raise RuntimeError(f"Training did not create model artifact {filename}")
            loaded = joblib.load(path)
            actual = np.asarray(loaded.predict(samples[material]), dtype=float)
            wanted = np.asarray(expected[material][quantile], dtype=float)
            if (
                actual.shape != wanted.shape
                or not np.isfinite(actual).all()
                or not np.allclose(actual, wanted)
            ):
                raise RuntimeError(f"Serialized model artifact failed validation: {filename}")
            artifact_files.append(filename)
    return sorted(artifact_files)


def _eligible_dataset(data: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    required = {
        "observation_date",
        MATERIAL_COLUMN,
        SCRAP_TYPE_COLUMN,
        TARGET,
        "is_trainable",
        *FEATURE_COLUMNS,
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Training dataset is missing required columns: {missing}")

    dates = pd.to_datetime(data["observation_date"], errors="coerce")
    genuine_dates = int(dates.dropna().dt.date.nunique())
    trainable = (
        data["is_trainable"]
        .astype("string")
        .str.strip()
        .str.lower()
        .isin({"true", "1", "yes"})
    )
    has_identity = data[MATERIAL_COLUMN].notna() & data[SCRAP_TYPE_COLUMN].notna()
    has_identity &= data[MATERIAL_COLUMN].astype("string").str.strip().ne("")
    has_identity &= data[SCRAP_TYPE_COLUMN].astype("string").str.strip().ne("")
    eligible = data.loc[trainable & dates.notna() & has_identity].copy()
    eligible["observation_date"] = dates.loc[eligible.index].dt.normalize()
    for column in (MATERIAL_COLUMN, SCRAP_TYPE_COLUMN):
        eligible[column] = eligible[column].astype("string").str.strip().astype(str)

    eligible[TARGET] = pd.to_numeric(eligible[TARGET], errors="coerce")
    if (
        eligible[TARGET].isna().any()
        or not np.isfinite(eligible[TARGET].to_numpy(dtype=float)).all()
        or eligible[TARGET].le(0).any()
    ):
        raise ValueError("Eligible training targets must be finite positive numeric values")

    for column in FEATURE_COLUMNS:
        values = pd.to_numeric(eligible[column], errors="coerce")
        eligible[column] = values.replace([np.inf, -np.inf], np.nan).astype(np.float64)
    return eligible, genuine_dates


def _split_material(frame: pd.DataFrame) -> dict[str, pd.DataFrame] | None:
    if frame["observation_date"].dt.normalize().nunique() < MIN_SCRAP_HISTORY_DAYS:
        return None
    try:
        splits = chronological_split(frame)
    except ValueError:
        return None
    if (
        len(splits["train"]) < MIN_TRAIN_ROWS
        or len(splits["validation"]) < MIN_VALIDATION_ROWS
        or len(splits["test"]) < MIN_TEST_ROWS
    ):
        return None
    return splits


def retrain(
    dataset: pd.DataFrame | None = None,
    *,
    db: Session | None = None,
) -> dict[str, Any]:
    result = (
        build_trainable_dataset()
        if dataset is None
        else {"dataset": dataset, "path": "database"}
    )
    eligible, genuine_dates = _eligible_dataset(result["dataset"])

    candidates: dict[str, dict[str, Any]] = {}
    skipped_materials: list[dict[str, Any]] = []
    all_validation_targets: list[np.ndarray] = []
    all_test_targets: list[np.ndarray] = []
    all_validation_predictions = {quantile: [] for quantile in QUANTILES}
    all_test_predictions = {quantile: [] for quantile in QUANTILES}

    for material, material_frame in eligible.groupby(MATERIAL_COLUMN, sort=True):
        material_frame = material_frame.sort_values("observation_date").copy()
        split = _split_material(material_frame)
        if len(material_frame) < MIN_MATERIAL_ROWS or split is None:
            skipped_materials.append({
                "material": material,
                "status": "insufficient_material_history",
                "rows": int(len(material_frame)),
                "dates": int(material_frame["observation_date"].nunique()),
            })
            continue

        train = split["train"]
        numeric_features = [
            column for column in FEATURE_COLUMNS if train[column].notna().any()
        ]
        if not numeric_features:
            skipped_materials.append({
                "material": material,
                "status": "no_observed_numeric_features",
                "rows": int(len(material_frame)),
            })
            continue

        model_features = [*numeric_features, SCRAP_TYPE_COLUMN]
        x_train = train[model_features]
        y_train = train[TARGET].to_numpy(dtype=float)
        validation = split["validation"]
        test = split["test"]
        x_validation = validation[model_features]
        y_validation = validation[TARGET].to_numpy(dtype=float)
        x_test = test[model_features]
        y_test = test[TARGET].to_numpy(dtype=float)

        evaluation_models: dict[float, Any] = {}
        validation_predictions: dict[float, np.ndarray] = {}
        test_predictions: dict[float, np.ndarray] = {}
        for quantile in QUANTILES:
            model = _quantile_model(quantile, numeric_features)
            model.fit(x_train, y_train)
            evaluation_models[quantile] = model
            validation_predictions[quantile] = np.asarray(
                model.predict(x_validation), dtype=float
            )
            test_predictions[quantile] = np.asarray(model.predict(x_test), dtype=float)

        material_metrics = {
            "rows": int(len(material_frame)),
            "dates": int(material_frame["observation_date"].nunique()),
            "train_rows": int(len(train)),
            "validation_rows": int(len(validation)),
            "test_rows": int(len(test)),
            "scrap_types": sorted(material_frame[SCRAP_TYPE_COLUMN].unique().tolist()),
            "validation": _evaluate_predictions(y_validation, validation_predictions),
            "validation_by_scrap_type": _evaluate_by_scrap_type(
                validation, y_validation, validation_predictions
            ),
            "test": _evaluate_predictions(y_test, test_predictions),
            "test_by_scrap_type": _evaluate_by_scrap_type(
                test, y_test, test_predictions
            ),
            "numeric_feature_columns": numeric_features,
            "input_feature_columns": model_features,
        }
        candidates[material] = {
            "frame": material_frame,
            "numeric_features": numeric_features,
            "metrics": material_metrics,
        }
        all_validation_targets.append(y_validation)
        all_test_targets.append(y_test)
        for quantile in QUANTILES:
            all_validation_predictions[quantile].append(
                validation_predictions[quantile]
            )
            all_test_predictions[quantile].append(test_predictions[quantile])

    if not candidates:
        return {
            "status": "skipped",
            "reason": "no_material_has_sufficient_history",
            "collection_dates": genuine_dates,
            "eligible_rows": int(len(eligible)),
            "materials_trained": 0,
            "materials_skipped": skipped_materials,
            "minimums": {
                "material_rows": MIN_MATERIAL_ROWS,
                "material_dates": MIN_SCRAP_HISTORY_DAYS,
                "train_rows": MIN_TRAIN_ROWS,
                "validation_rows": MIN_VALIDATION_ROWS,
                "test_rows": MIN_TEST_ROWS,
            },
        }

    validation_targets = np.concatenate(all_validation_targets)
    test_targets = np.concatenate(all_test_targets)
    validation_predictions = {
        quantile: np.concatenate(all_validation_predictions[quantile])
        for quantile in QUANTILES
    }
    test_predictions = {
        quantile: np.concatenate(all_test_predictions[quantile])
        for quantile in QUANTILES
    }
    metrics = {
        "validation": _evaluate_predictions(validation_targets, validation_predictions),
        "test": _evaluate_predictions(test_targets, test_predictions),
        "eligible_rows": int(len(eligible)),
        "genuine_collection_dates": genuine_dates,
        "materials": {
            material: candidate["metrics"]
            for material, candidate in candidates.items()
        },
        "skipped_materials": skipped_materials,
        "minimums": {
            "material_rows": MIN_MATERIAL_ROWS,
            "material_dates": MIN_SCRAP_HISTORY_DAYS,
            "train_rows": MIN_TRAIN_ROWS,
            "validation_rows": MIN_VALIDATION_ROWS,
            "test_rows": MIN_TEST_ROWS,
        },
    }
    validation_mae = metrics["validation"]["p50"]["mae"]
    if not np.isfinite(validation_mae):
        raise ValueError("Validation MAE must be finite")
    if validation_mae > PROMOTION_MAX_VALIDATION_MAE:
        return {
            "status": "skipped",
            "reason": "validation_mae_above_promotion_limit",
            "validation_mae": validation_mae,
            "maximum_validation_mae": PROMOTION_MAX_VALIDATION_MAE,
            "materials_trained": len(candidates),
            "materials_skipped": skipped_materials,
            "metrics": metrics,
        }

    owned_db = db is None
    if db is None:
        from ..core.database import SessionLocal
        db = SessionLocal()
    try:
        active = load_active_model_metadata(db)
        active_schema = active.get("feature_schema", {}) if active else {}
        active_is_compatible = (
            active is not None
            and active_schema.get("model_contract_version") == MODEL_CONTRACT_VERSION
            and active_schema.get("feature_version") == FEATURE_VERSION
        )
        if active_is_compatible:
            missing_active_materials = sorted(
                set(active_schema.get("materials", {})) - set(candidates)
            )
            if missing_active_materials:
                return {
                    "status": "skipped",
                    "reason": "candidate_missing_active_materials",
                    "missing_materials": missing_active_materials,
                    "materials_trained": len(candidates),
                    "materials_skipped": skipped_materials,
                    "metrics": metrics,
                }
            active_mae = active["metrics"]["validation"]["p50"]["mae"]
            if validation_mae > active_mae:
                return {
                    "status": "skipped",
                    "reason": "candidate_does_not_improve_active_model",
                    "validation_mae": validation_mae,
                    "active_validation_mae": active_mae,
                    "materials_trained": len(candidates),
                    "materials_skipped": skipped_materials,
                    "metrics": metrics,
                }

        version = (
            f"v{datetime.now(timezone.utc):%Y%m%d%H%M%S}"
            f"-{uuid4().hex[:8]}"
        )
        with tempfile.TemporaryDirectory(
            prefix=f"scraplink-model-{version}-"
        ) as temporary:
            directory = Path(temporary)
            material_models: dict[str, dict[float, Any]] = {}
            sample_features: dict[str, pd.DataFrame] = {}
            expected_predictions: dict[str, dict[float, np.ndarray]] = {}
            material_schema: dict[str, dict[str, Any]] = {}

            for material, candidate in candidates.items():
                frame = candidate["frame"]
                numeric_features = candidate["numeric_features"]
                input_features = [*numeric_features, SCRAP_TYPE_COLUMN]
                x_full = frame[input_features]
                y_full = frame[TARGET].to_numpy(dtype=float)
                trained_models: dict[float, Any] = {}
                expected: dict[float, np.ndarray] = {}
                sample = x_full.iloc[: min(20, len(x_full))]

                for quantile in QUANTILES:
                    model = _quantile_model(quantile, numeric_features)
                    model.fit(x_full, y_full)
                    trained_models[quantile] = model
                    filename = _artifact_name(material, quantile)
                    joblib.dump(model, directory / filename)
                    expected[quantile] = np.asarray(model.predict(sample), dtype=float)

                counts = frame[SCRAP_TYPE_COLUMN].value_counts()
                most_common = counts[counts == counts.max()].index.astype(str).tolist()
                material_models[material] = trained_models
                sample_features[material] = sample
                expected_predictions[material] = expected
                material_schema[material] = {
                    "artifact_files": {
                        f"p{int(quantile * 100)}": _artifact_name(material, quantile)
                        for quantile in QUANTILES
                    },
                    "scrap_types": sorted(frame[SCRAP_TYPE_COLUMN].unique().tolist()),
                    "default_scrap_type": sorted(most_common)[0],
                    "numeric_feature_columns": numeric_features,
                    "categorical_feature_columns": [SCRAP_TYPE_COLUMN],
                    "input_feature_columns": input_features,
                }

            artifact_files = _verify_serialized_models(
                directory,
                material_models,
                sample_features,
                expected_predictions,
            )
            metadata = {
                "version": version,
                "model_contract_version": MODEL_CONTRACT_VERSION,
                "feature_version": FEATURE_VERSION,
                "target": TARGET,
                "quantiles": list(QUANTILES),
                "model_scope": "one_quantile_model_set_per_material",
                "materials": sorted(material_schema),
                "dataset_path": result["path"],
            }
            feature_schema = {
                "model_contract_version": MODEL_CONTRACT_VERSION,
                "feature_version": FEATURE_VERSION,
                "target": TARGET,
                "material_column": MATERIAL_COLUMN,
                "categorical_feature_columns": [SCRAP_TYPE_COLUMN],
                "quantiles": list(QUANTILES),
                "materials": material_schema,
            }
            (directory / "metadata.json").write_text(
                json.dumps(metadata, indent=2), encoding="utf-8"
            )
            (directory / "feature_schema.json").write_text(
                json.dumps(feature_schema, indent=2), encoding="utf-8"
            )
            (directory / "metrics.json").write_text(
                json.dumps(metrics, indent=2), encoding="utf-8"
            )
            activate_model_version(
                db,
                version,
                directory,
                metrics=metrics,
                feature_schema=feature_schema,
            )

        return {
            "status": "promoted",
            "version": version,
            "artifact_files": artifact_files,
            "materials_trained": len(candidates),
            "materials_skipped": skipped_materials,
            "metrics": metrics,
            "promotion": {
                "validation_mae": validation_mae,
                "maximum_validation_mae": (
                    PROMOTION_MAX_VALIDATION_MAE
                    if np.isfinite(PROMOTION_MAX_VALIDATION_MAE)
                    else None
                ),
                "compared_with_active": active_is_compatible,
            },
        }
    finally:
        if owned_db:
            db.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    try:
        print(json.dumps(retrain(), indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
