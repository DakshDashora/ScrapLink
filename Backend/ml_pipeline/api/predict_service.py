"""Prediction interface for active ScrapMonster quantile artifacts.

The service never retrains and never turns MCX activity into a price.  Legacy
arguments remain accepted so existing API callers can migrate gradually.
"""

from __future__ import annotations

from typing import Any

import joblib
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from ..core.db_store import load_source_dataframes
from ..etl.trainable import FEATURE_COLUMNS, build_trainable_dataset
from ..training.model_registry import load_active_model_metadata
from ..storage.cloudinary_models import download_model_artifacts

_MODEL_CACHE: dict[str, Any] = {}


def _load_active(db: Session) -> dict[str, Any] | None:
    metadata = load_active_model_metadata(db)
    if metadata is None:
        return None
    if metadata.get("version") in _MODEL_CACHE:
        return _MODEL_CACHE[metadata["version"]]
    directory = download_model_artifacts(metadata)
    models = {}
    for quantile in (10, 50, 90):
        path = directory / f"model_p{quantile}.joblib"
        if not path.exists():
            raise FileNotFoundError(f"Active model is missing {path.name}")
        models[quantile] = joblib.load(path)
    loaded = {
        "version": metadata["version"],
        "models": models,
        "features": metadata["feature_schema"].get("feature_names", FEATURE_COLUMNS),
    }
    _MODEL_CACHE.clear()
    _MODEL_CACHE[metadata["version"]] = loaded
    return loaded


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
) -> tuple[dict[str, float], str | None]:
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
        "scrap_price_lag_1": lag_1 if lag_1 is not None else base,
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
        "day_of_week": 0.0, "month": 1.0, "quarter": 1.0,
        "has_scrap_history": 1.0, "has_mcx_history": 0.0,
    }
    return values, None


def _latest_database_features(db: Session, commodity: str) -> dict[str, Any] | None:
    sources = load_source_dataframes(db)
    if sources["scrap"].empty:
        return None
    trainable = build_trainable_dataset(
        scrap=sources["scrap"],
        mcx=sources["mcx"],
        persist_artifacts=False,
    )["dataset"]
    rows = trainable[
        trainable["material"].astype(str).str.casefold() == commodity.casefold()
    ]
    if rows.empty:
        return None
    return rows.sort_values("observation_date").iloc[-1].to_dict()


def get_price_prediction(
    commodity: str,
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
    """Return ordered P10/P50/P90 estimates plus the legacy response fields."""
    if db is None:
        raise RuntimeError("A database session is required to load the active model")
    active = _load_active(db)
    if active is None:
        raise RuntimeError(
            "No active price model is available; training history is insufficient"
        )
    feature_values, prediction_date = _legacy_features(
        commodity, lag_1, lag_7, lag_14, lag_30, rolling_mean_7,
        rolling_mean_30, rolling_std_7, rolling_std_30, pct_change_7, pct_change_30,
        _latest_database_features(db, commodity),
    )
    vector = pd.DataFrame([{name: feature_values.get(name, np.nan) for name in active["features"]}])
    raw = [float(active["models"][quantile].predict(vector)[0]) for quantile in (10, 50, 90)]
    estimates = np.sort(np.asarray(raw, dtype=float))
    model_version = active["version"]
    if not np.isfinite(estimates).all() or (estimates < 0).any():
        raise ValueError("Model returned non-finite or negative price estimates")
    p10, p50, p90 = [round(float(value), 2) for value in estimates]
    trend_base = float(feature_values["scrap_price_ma_7"])
    trend = "UPWARD" if p50 > trend_base * 1.01 else "DOWNWARD" if p50 < trend_base * 0.99 else "STABLE"
    return {
        "status": "success",
        "commodity": commodity,
        "estimated_price_p10_inr_per_kg": p10,
        "estimated_price_p50_inr_per_kg": p50,
        "estimated_price_p90_inr_per_kg": p90,
        "model_version": model_version,
        "prediction_date": prediction_date,
        "estimate_type": "scrap_market_reference",
        "is_guaranteed_transaction_price": False,
        # Existing API compatibility:
        "recommended_price": p50,
        "price_band": {"lower": p10, "upper": p90},
        "trend": trend,
        "unit": "INR/kg",
        "disclaimer": (
            "This is an AI-estimated reference price based on observed "
            "ScrapMonster prices. It is not a guaranteed transaction price."
        ),
    }
