"""Prediction interface for active ScrapMonster quantile artifacts.

The service never retrains and never turns MCX activity into a price.  Legacy
arguments remain accepted so existing API callers can migrate gradually.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ..etl.pipeline_config import SCRAP_CANONICAL_PATH
from ..etl.trainable import FEATURE_COLUMNS, build_trainable_dataset
from ..training.model_registry import load_active_model_metadata

_MODEL_CACHE: dict[str, Any] = {}


def _latest_observation(commodity: str) -> dict[str, Any] | None:
    if not SCRAP_CANONICAL_PATH.exists():
        return None
    data = pd.read_csv(SCRAP_CANONICAL_PATH)
    data = data[data["material"].astype(str).str.casefold() == commodity.casefold()]
    if data.empty:
        return None
    row = data.sort_values("observation_date").iloc[-1]
    return {"price": float(row["price_inr_per_kg"]), "date": str(row["observation_date"])}


def _load_active() -> dict[str, Any] | None:
    metadata = load_active_model_metadata()
    if metadata is None:
        return None
    directory = Path(metadata["path"])
    if metadata.get("version") in _MODEL_CACHE:
        return _MODEL_CACHE[metadata["version"]]
    models = {}
    for quantile in (10, 50, 90):
        path = directory / f"model_p{quantile}.joblib"
        if not path.exists():
            raise FileNotFoundError(f"Active model is missing {path.name}")
        models[quantile] = joblib.load(path)
    schema_path = directory / "feature_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8")) if schema_path.exists() else {}
    loaded = {
        "version": metadata["version"],
        "models": models,
        "features": schema.get("feature_names", FEATURE_COLUMNS),
    }
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
) -> tuple[dict[str, float], str | None]:
    latest = _latest_observation(commodity)
    if latest is None and lag_1 is None:
        raise ValueError(
            f"No observed ScrapMonster price is available for {commodity!r}; "
            "collect a snapshot or supply an observed lag_1 value."
        )
    base = latest["price"] if latest else float(lag_1)
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
    return values, latest["date"] if latest else None


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
) -> dict[str, Any]:
    """Return ordered P10/P50/P90 estimates plus the legacy response fields."""
    feature_values, prediction_date = _legacy_features(
        commodity, lag_1, lag_7, lag_14, lag_30, rolling_mean_7,
        rolling_mean_30, rolling_std_7, rolling_std_30, pct_change_7, pct_change_30,
    )
    active = _load_active()
    if active:
        try:
            trainable = build_trainable_dataset()["dataset"]
            rows = trainable[trainable["material"].astype(str).str.casefold() == commodity.casefold()]
            if not rows.empty:
                feature_values.update(rows.sort_values("observation_date").iloc[-1].to_dict())
        except (FileNotFoundError, ValueError):
            pass
        vector = pd.DataFrame([{name: feature_values.get(name, np.nan) for name in active["features"]}])
        raw = [float(active["models"][quantile].predict(vector)[0]) for quantile in (10, 50, 90)]
        estimates = np.sort(np.asarray(raw, dtype=float))
        model_version = active["version"]
    else:
        raise RuntimeError(
            "No active price model is available; training history is insufficient"
        )
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
