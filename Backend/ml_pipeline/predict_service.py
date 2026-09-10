"""
ScrapLink — ML Prediction Service Interface
============================================
Interface module for backend API developers to import and call model predictions.

Usage by Backend Developer in FastAPI router:
    from ml_pipeline.predict_service import get_price_prediction

    result = get_price_prediction(commodity="Copper", lag_1=645.0)
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(SCRIPT_DIR, "models")
PROCESSED_DIR = os.path.join(SCRIPT_DIR, "data", "processed")
FEATURE_CSV = os.path.join(PROCESSED_DIR, "engineered_commodity_features.csv")

# In-memory cache for fast sub-20ms inference
_MODEL_CACHE = {}


def load_model_artifacts(models_dir: str = None):
    """Loads and caches XGBoost model artifacts in memory if available."""
    global _MODEL_CACHE
    if _MODEL_CACHE:
        return _MODEL_CACHE

    target_dir = models_dir or MODELS_DIR

    logret_path  = os.path.join(target_dir, "xgboost_per_commodity_logreturn.pkl")
    xgb_path     = os.path.join(target_dir, "xgboost_price_model.pkl")
    encoder_path = os.path.join(target_dir, "label_encoder.pkl")

    if os.path.exists(logret_path):
        _MODEL_CACHE["type"] = "logreturn"
        _MODEL_CACHE["models"] = joblib.load(logret_path)
    elif os.path.exists(xgb_path) and os.path.exists(encoder_path):
        _MODEL_CACHE["type"] = "single"
        _MODEL_CACHE["model"] = joblib.load(xgb_path)
        _MODEL_CACHE["encoder"] = joblib.load(encoder_path)
    else:
        _MODEL_CACHE["type"] = "none"

    return _MODEL_CACHE


def _get_commodity_defaults(commodity: str) -> dict:
    """Loads latest known feature values for a commodity from dataset if missing."""
    if os.path.exists(FEATURE_CSV):
        try:
            df = pd.read_csv(FEATURE_CSV)
            sub = df[df["commodity"].str.lower() == commodity.lower()].sort_values("date")
            if not sub.empty:
                last = sub.iloc[-1]
                return {
                    "lag_1": float(last.get("lag_1", last["spot_price_inr_kg"])),
                    "lag_7": float(last.get("lag_7", last["spot_price_inr_kg"])),
                    "lag_14": float(last.get("lag_14", last["spot_price_inr_kg"])),
                    "lag_30": float(last.get("lag_30", last["spot_price_inr_kg"])),
                    "rolling_mean_7": float(last.get("rolling_mean_7", last["spot_price_inr_kg"])),
                    "rolling_mean_30": float(last.get("rolling_mean_30", last["spot_price_inr_kg"])),
                    "rolling_std_7": float(last.get("rolling_std_7", 5.0)),
                    "rolling_std_30": float(last.get("rolling_std_30", 15.0)),
                    "pct_change_7": float(last.get("pct_change_7", 0.0)),
                    "pct_change_30": float(last.get("pct_change_30", 0.0)),
                }
        except Exception:
            pass

    return {
        "lag_1": 200.0, "lag_7": 200.0, "lag_14": 200.0, "lag_30": 200.0,
        "rolling_mean_7": 200.0, "rolling_mean_30": 200.0,
        "rolling_std_7": 5.0, "rolling_std_30": 15.0,
        "pct_change_7": 0.0, "pct_change_30": 0.0,
    }


def get_price_prediction(
    commodity: str,
    lag_1: float = None,
    lag_7: float = None,
    lag_14: float = None,
    lag_30: float = None,
    rolling_mean_7: float = None,
    rolling_mean_30: float = None,
    rolling_std_7: float = None,
    rolling_std_30: float = None,
    pct_change_7: float = None,
    pct_change_30: float = None,
    models_dir: str = None,
    confidence_rmse: float = 15.0,
) -> dict:
    """
    Main interface function for Backend API routes.
    Returns structured price recommendation dictionary.
    """
    cache = load_model_artifacts(models_dir)
    defaults = _get_commodity_defaults(commodity)

    v_lag1   = lag_1 if lag_1 is not None else defaults["lag_1"]
    v_lag7   = lag_7 if lag_7 is not None else defaults["lag_7"]
    v_lag14  = lag_14 if lag_14 is not None else defaults["lag_14"]
    v_lag30  = lag_30 if lag_30 is not None else defaults["lag_30"]
    v_rm7    = rolling_mean_7 if rolling_mean_7 is not None else defaults["rolling_mean_7"]
    v_rm30   = rolling_mean_30 if rolling_mean_30 is not None else defaults["rolling_mean_30"]
    v_rstd7  = rolling_std_7 if rolling_std_7 is not None else defaults["rolling_std_7"]
    v_rstd30 = rolling_std_30 if rolling_std_30 is not None else defaults["rolling_std_30"]
    v_pct7   = pct_change_7 if pct_change_7 is not None else defaults["pct_change_7"]
    v_pct30  = pct_change_30 if pct_change_30 is not None else defaults["pct_change_30"]

    if cache["type"] == "logreturn":
        models = cache["models"]
        matched_key = None
        for k in models.keys():
            if k.lower() == commodity.lower():
                matched_key = k
                break

        if matched_key:
            m = models[matched_key]
            feats = np.array([[v_lag1, v_lag7, v_lag14, v_lag30, v_rm7, v_rm30, v_rstd7, v_rstd30, v_pct7, v_pct30]])
            log_ret = float(m.predict(feats)[0])
            pred_price = round(v_lag1 * np.exp(log_ret), 2)
        else:
            pred_price = round(v_lag1, 2)
    elif cache["type"] == "single":
        model = cache["model"]
        encoder = cache["encoder"]
        try:
            comm_enc = encoder.transform([commodity])[0]
        except ValueError:
            comm_enc = int(np.mean(encoder.transform(encoder.classes_)))

        feats = np.array([[comm_enc, v_lag1, v_lag7, v_lag14, v_lag30, v_rm7, v_rm30, v_rstd7, v_rstd30, v_pct7, v_pct30]])
        pred_price = round(float(model.predict(feats)[0]), 2)
    else:
        # Fallback if model artifacts are not yet generated
        pred_price = round(v_lag1, 2)

    lower_band = round(max(pred_price - (1.96 * confidence_rmse), 0.0), 2)
    upper_band = round(pred_price + (1.96 * confidence_rmse), 2)

    if pred_price > v_rm7 * 1.01:
        trend = "UPWARD"
    elif pred_price < v_rm7 * 0.99:
        trend = "DOWNWARD"
    else:
        trend = "STABLE"

    return {
        "status": "success",
        "commodity": commodity,
        "recommended_price": pred_price,
        "price_band": {"lower": lower_band, "upper": upper_band},
        "trend": trend,
        "unit": "INR/kg",
        "disclaimer": (
            "This is an AI-estimated reference price based on historical market benchmarks. "
            "It is not a guaranteed transaction price. Actual scrap prices depend on "
            "grade, condition, local demand, and negotiation."
        ),
    }


if __name__ == "__main__":
    res = get_price_prediction("Copper")
    print(json.dumps(res, indent=2))
