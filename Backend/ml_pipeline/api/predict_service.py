"""Inference interface for the active material-specific quantile models."""

from __future__ import annotations

from typing import Any

import joblib
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from ..core.db_store import load_source_dataframes
from ..etl.pipeline_config import FEATURE_VERSION
from ..etl.trainable import FEATURE_COLUMNS, build_trainable_dataset
from ..training.model_registry import load_active_model_metadata
from ..storage.cloudinary_models import download_model_artifacts
from ..utils import MODEL_CONTRACT_VERSION

_MODEL_CACHE: dict[str, Any] = {}
SCRAP_TYPE_COLUMN = "scrap_type"


def _load_active(db: Session) -> dict[str, Any] | None:
    metadata = load_active_model_metadata(db)
    if metadata is None:
        return None

    schema = metadata.get("feature_schema") or {}
    if (
        schema.get("model_contract_version") != MODEL_CONTRACT_VERSION
        or schema.get("feature_version") != FEATURE_VERSION
    ):
        raise RuntimeError(
            "The active model does not implement the material-specific prediction "
            "contract; run monthly model training before serving predictions"
        )
    version = metadata["version"]
    if version in _MODEL_CACHE:
        return _MODEL_CACHE[version]

    directory = download_model_artifacts(metadata)
    materials: dict[str, dict[str, Any]] = {}
    for material, definition in schema.get("materials", {}).items():
        if not isinstance(definition, dict):
            raise ValueError(f"Active model schema for {material!r} is invalid")
        artifact_files = definition.get("artifact_files", {})
        models: dict[int, Any] = {}
        for quantile in (10, 50, 90):
            filename = artifact_files.get(f"p{quantile}")
            if not isinstance(filename, str):
                raise ValueError(
                    f"Active model schema for {material!r} lacks P{quantile} artifact"
                )
            path = directory / filename
            if not path.is_file():
                raise FileNotFoundError(f"Active model is missing {filename}")
            models[quantile] = joblib.load(path)

        scrap_types = definition.get("scrap_types")
        numeric_features = definition.get("numeric_feature_columns")
        input_features = definition.get("input_feature_columns")
        default_scrap_type = definition.get("default_scrap_type")
        if (
            not isinstance(scrap_types, list)
            or not scrap_types
            or not all(isinstance(value, str) and value for value in scrap_types)
            or not isinstance(numeric_features, list)
            or not all(value in FEATURE_COLUMNS for value in numeric_features)
            or not isinstance(input_features, list)
            or input_features != [*numeric_features, "scrap_type"]
            or default_scrap_type not in scrap_types
        ):
            raise ValueError(f"Active model schema for {material!r} is incomplete")
        materials[material] = {
            "models": models,
            "scrap_types": scrap_types,
            "default_scrap_type": default_scrap_type,
            "numeric_features": numeric_features,
            "input_features": input_features,
        }

    if not materials:
        raise ValueError("Active model has no material-specific models")
    loaded = {"version": version, "materials": materials}
    _MODEL_CACHE.clear()
    _MODEL_CACHE[version] = loaded
    return loaded


def _resolve_category(value: str, categories: list[str], field: str) -> str:
    normalized = value.strip().casefold()
    match = next(
        (category for category in categories if category.strip().casefold() == normalized),
        None,
    )
    if match is None:
        raise ValueError(f"No trained {field} model exists for {value!r}")
    return match


def _legacy_features(
    commodity: str,
    lag_1: float | None,
    lag_7: float | None,
    lag_14: float | None,
    lag_30: float | None,
    rolling_mean_7: float | None,
    rolling_mean_30: float | None,
    rolling_std_7: float | None,
    rolling_std_30: float | None,
    pct_change_7: float | None,
    pct_change_30: float | None,
    latest_features: dict[str, Any] | None,
) -> tuple[dict[str, Any], str | None]:
    if latest_features is not None:
        return (
            {name: latest_features.get(name) for name in FEATURE_COLUMNS},
            str(latest_features["observation_date"]),
        )
    if lag_1 is None:
        raise ValueError(
            f"No observed ScrapMonster price is available for {commodity!r}; "
            "collect a snapshot or supply an observed lag_1 value."
        )
    base = float(lag_1)
    values = {
        "scrap_price_lag_1": base,
        "scrap_price_lag_7": lag_7 if lag_7 is not None else base,
        "scrap_price_lag_14": lag_14 if lag_14 is not None else base,
        "scrap_price_lag_30": lag_30 if lag_30 is not None else base,
        "scrap_price_ma_7": rolling_mean_7 if rolling_mean_7 is not None else base,
        "scrap_price_ma_30": rolling_mean_30 if rolling_mean_30 is not None else base,
        "scrap_price_volatility_7": rolling_std_7 if rolling_std_7 is not None else 0.0,
        "scrap_price_volatility_30": rolling_std_30 if rolling_std_30 is not None else 0.0,
        "scrap_price_return_7": pct_change_7 if pct_change_7 is not None else 0.0,
        "scrap_price_return_30": pct_change_30 if pct_change_30 is not None else 0.0,
        "scrap_price_return_1": 0.0,
        "day_of_week": 0.0,
        "month": 1.0,
        "quarter": 1.0,
        "has_scrap_history": 1.0,
        "has_mcx_history": 0.0,
    }
    return values, None


def _latest_database_features(
    db: Session,
    material: str,
    scrap_type: str | None,
    supported_scrap_types: list[str],
) -> dict[str, Any] | None:
    sources = load_source_dataframes(db)
    if sources["scrap"].empty:
        return None
    dataset = build_trainable_dataset(
        scrap=sources["scrap"],
        mcx=sources["mcx"],
        persist_artifacts=False,
    )["dataset"]
    rows = dataset[
        dataset["material"].astype(str).str.strip().str.casefold()
        == material.strip().casefold()
    ]
    rows = rows[rows["is_trainable"].fillna(False)]
    supported = {value.casefold() for value in supported_scrap_types}
    rows = rows[rows["scrap_type"].astype(str).str.strip().str.casefold().isin(supported)]
    if scrap_type is not None:
        rows = rows[
            rows["scrap_type"].astype(str).str.strip().str.casefold()
            == scrap_type.strip().casefold()
        ]
    if rows.empty:
        return None
    return rows.sort_values(
        ["observation_date", "scrap_type"], kind="stable"
    ).iloc[-1].to_dict()


def get_price_prediction(
    commodity: str,
    scrap_type: str | None = None,
    lag_1: float | None = None,
    lag_7: float | None = None,
    lag_14: float | None = None,
    lag_30: float | None = None,
    rolling_mean_7: float | None = None,
    rolling_mean_30: float | None = None,
    rolling_std_7: float | None = None,
    rolling_std_30: float | None = None,
    pct_change_7: float | None = None,
    pct_change_30: float | None = None,
    models_dir: str | None = None,
    confidence_rmse: float = 15.0,
    db: Session | None = None,
) -> dict[str, Any]:
    """Return a price band from the trained model for the requested material."""
    del models_dir, confidence_rmse
    if db is None:
        raise RuntimeError("A database session is required to load the active model")
    active = _load_active(db)
    if active is None:
        raise RuntimeError(
            "No active price model is available; monthly training has not promoted one"
        )

    material_key = _resolve_category(
        commodity, list(active["materials"]), "material"
    )
    material_model = active["materials"][material_key]
    requested_scrap_type = (
        _resolve_category(
            scrap_type, material_model["scrap_types"], "scrap type"
        )
        if scrap_type is not None
        else None
    )
    latest_features = _latest_database_features(
        db,
        material_key,
        requested_scrap_type,
        material_model["scrap_types"],
    )
    feature_values, prediction_date = _legacy_features(
        commodity,
        lag_1,
        lag_7,
        lag_14,
        lag_30,
        rolling_mean_7,
        rolling_mean_30,
        rolling_std_7,
        rolling_std_30,
        pct_change_7,
        pct_change_30,
        latest_features,
    )
    selected_scrap_type = (
        requested_scrap_type
        or (
            str(latest_features[SCRAP_TYPE_COLUMN])
            if latest_features is not None
            else material_model["default_scrap_type"]
        )
    )
    model_input = {}
    for name in material_model["numeric_features"]:
        value = pd.to_numeric(
            pd.Series([feature_values.get(name)]), errors="coerce"
        ).iloc[0]
        model_input[name] = (
            float(value) if pd.notna(value) and np.isfinite(value) else np.nan
        )
    model_input[SCRAP_TYPE_COLUMN] = selected_scrap_type
    vector = pd.DataFrame(
        [model_input], columns=material_model["input_features"]
    )
    raw = [
        float(material_model["models"][quantile].predict(vector)[0])
        for quantile in (10, 50, 90)
    ]
    estimates = np.sort(np.asarray(raw, dtype=float))
    if not np.isfinite(estimates).all() or (estimates < 0).any():
        raise ValueError("Model returned non-finite or negative price estimates")
    p10, p50, p90 = [round(float(value), 2) for value in estimates]

    trend_value = pd.to_numeric(
        pd.Series([feature_values.get("scrap_price_ma_7")]), errors="coerce"
    ).iloc[0]
    if not np.isfinite(trend_value):
        trend_value = pd.to_numeric(
            pd.Series([feature_values.get("scrap_price_lag_1")]), errors="coerce"
        ).iloc[0]
    if not np.isfinite(trend_value):
        trend_value = p50
    trend = (
        "UPWARD"
        if p50 > trend_value * 1.01
        else "DOWNWARD"
        if p50 < trend_value * 0.99
        else "STABLE"
    )
    return {
        "status": "success",
        "commodity": material_key,
        "scrap_type": selected_scrap_type,
        "estimated_price_p10_inr_per_kg": p10,
        "estimated_price_p50_inr_per_kg": p50,
        "estimated_price_p90_inr_per_kg": p90,
        "model_version": active["version"],
        "prediction_date": prediction_date,
        "estimate_type": "scrap_market_reference",
        "is_guaranteed_transaction_price": False,
        "recommended_price": p50,
        "price_band": {"lower": p10, "upper": p90},
        "trend": trend,
        "unit": "INR/kg",
        "disclaimer": (
            "This is an AI-estimated reference price based on observed "
            "ScrapMonster prices. It is not a guaranteed transaction price."
        ),
    }
