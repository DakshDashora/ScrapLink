"""Train quantile groundwork only when genuine ScrapMonster history is sufficient."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline

from ..etl.pipeline_config import (
    FEATURE_VERSION, MIN_SCRAP_HISTORY_DAYS, MIN_TRAINING_ROWS,
    RANDOM_SEED,
)
from ..utils import PROMOTION_MAX_VALIDATION_MAE
from ..etl.trainable import FEATURE_COLUMNS, TARGET, build_trainable_dataset
from ..etl.validation import chronological_split
from .evaluate import quantile_metrics, regression_metrics
from .model_registry import (
    load_active_model_metadata,
    new_version_dir,
    write_active_pointer,
)


def _quantile_model(quantile: float):
    return make_pipeline(
        SimpleImputer(strategy="median", add_indicator=True),
        HistGradientBoostingRegressor(
            loss="quantile", quantile=quantile, random_state=RANDOM_SEED,
            max_iter=150, learning_rate=0.05, max_leaf_nodes=15,
        ),
    )


def retrain(dataset: pd.DataFrame | None = None) -> dict[str, Any]:
    result = build_trainable_dataset() if dataset is None else {"dataset": dataset, "path": "database"}
    data = result["dataset"]
    required = {"observation_date", TARGET, "is_trainable", *FEATURE_COLUMNS}
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"Training dataset is missing required columns: {missing}")
    dates = pd.to_datetime(data["observation_date"], errors="coerce")
    genuine_dates = int(dates.dropna().dt.date.nunique())
    eligible = data[data["is_trainable"].fillna(False)].copy()
    eligible[TARGET] = pd.to_numeric(eligible[TARGET], errors="coerce")
    if eligible[TARGET].isna().any() or not np.isfinite(eligible[TARGET]).all():
        raise ValueError("Eligible training targets must be finite numeric values")
    if genuine_dates < MIN_SCRAP_HISTORY_DAYS or len(eligible) < MIN_TRAINING_ROWS:
        return {
            "status": "skipped",
            "reason": "insufficient_scrapmonster_history",
            "collection_dates": genuine_dates,
            "minimum_collection_dates": MIN_SCRAP_HISTORY_DAYS,
            "eligible_rows": int(len(eligible)),
            "minimum_training_rows": MIN_TRAINING_ROWS,
        }
    splits = chronological_split(eligible)
    numeric = [column for column in FEATURE_COLUMNS if column in splits["train"]]
    if len(numeric) != len(FEATURE_COLUMNS):
        raise ValueError("Training dataset does not contain the complete feature contract")
    x_train, y_train = splits["train"][numeric], splits["train"][TARGET]
    x_val, y_val = splits["validation"][numeric], splits["validation"][TARGET]
    x_test, y_test = splits["test"][numeric], splits["test"][TARGET]
    models = {}
    predictions = {}
    for quantile in (0.1, 0.5, 0.9):
        model = _quantile_model(quantile)
        model.fit(x_train, y_train)
        models[quantile] = model
        predictions[quantile] = model.predict(x_val)
    # Enforce ordered intervals at inference/evaluation boundaries.
    ordered = np.sort(np.column_stack([predictions[0.1], predictions[0.5], predictions[0.9]]), axis=1)
    val_metrics = {
        "p50": regression_metrics(y_val, ordered[:, 1]),
        "quantiles": quantile_metrics(
            y_val, {0.1: ordered[:, 0], 0.5: ordered[:, 1], 0.9: ordered[:, 2]}
        ),
    }
    test_predictions = {
        quantile: model.predict(x_test)
        for quantile, model in models.items()
    }
    test_ordered = np.sort(
        np.column_stack([
            test_predictions[0.1], test_predictions[0.5], test_predictions[0.9]
        ]),
        axis=1,
    )
    test_metrics = {
        "p50": regression_metrics(y_test, test_ordered[:, 1]),
        "quantiles": quantile_metrics(
            y_test,
            {0.1: test_ordered[:, 0], 0.5: test_ordered[:, 1], 0.9: test_ordered[:, 2]},
        ),
    }
    metrics = {
        "validation": val_metrics,
        "test": test_metrics,
        "train_rows": len(splits["train"]), "validation_rows": len(splits["validation"]),
        "test_rows": len(splits["test"]), "feature_columns": numeric,
    }
    validation_mae = val_metrics["p50"]["mae"]
    if not np.isfinite(validation_mae):
        raise ValueError("Validation MAE must be finite")
    if validation_mae > PROMOTION_MAX_VALIDATION_MAE:
        return {
            "status": "skipped",
            "reason": "validation_mae_above_promotion_limit",
            "validation_mae": validation_mae,
            "maximum_validation_mae": PROMOTION_MAX_VALIDATION_MAE,
            "metrics": metrics,
        }

    active = load_active_model_metadata()
    if active:
        active_metrics_path = Path(active["path"]) / "metrics.json"
        active_metrics = json.loads(active_metrics_path.read_text(encoding="utf-8"))
        active_mae = active_metrics["validation"]["p50"]["mae"]
        if validation_mae > active_mae:
            return {
                "status": "skipped",
                "reason": "candidate_does_not_improve_active_model",
                "validation_mae": validation_mae,
                "active_validation_mae": active_mae,
                "metrics": metrics,
            }

    version = (
        f"v{datetime.now(timezone.utc):%Y%m%d%H%M%S}"
        f"-{uuid4().hex[:8]}"
    )
    directory = new_version_dir(version)
    for quantile, model in models.items():
        joblib.dump(model, directory / f"model_p{int(quantile * 100)}.joblib")
    directory.joinpath("metadata.json").write_text(json.dumps({
        "version": version,
        "target": TARGET,
        "quantiles": [0.1, 0.5, 0.9],
        "feature_version": FEATURE_VERSION,
        "dataset_path": result["path"],
        "genuine_collection_dates": genuine_dates,
    }, indent=2), encoding="utf-8")
    directory.joinpath("feature_schema.json").write_text(json.dumps({
        "feature_version": FEATURE_VERSION,
        "target": TARGET,
        "feature_names": numeric,
        "quantiles": [0.1, 0.5, 0.9],
    }, indent=2), encoding="utf-8")
    directory.joinpath("metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_active_pointer(version, directory)
    return {
        "status": "promoted",
        "version": version,
        "metrics": metrics,
        "promotion": {
            "validation_mae": validation_mae,
            "maximum_validation_mae": (
                PROMOTION_MAX_VALIDATION_MAE
                if np.isfinite(PROMOTION_MAX_VALIDATION_MAE)
                else None
            ),
            "compared_with_active": bool(active),
        },
    }


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
