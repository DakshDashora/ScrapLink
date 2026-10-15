"""Shared ML-pipeline configuration and environment loading.

Only secrets belong in ``Backend/.env``. Non-secret pipeline defaults live in
this module so imports are deterministic and configuration is not scattered
across ETL modules.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


ML_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ML_DIR.parent
load_dotenv(BACKEND_DIR / ".env", override=False)


ML_JOB_TOKEN = os.getenv("ML_JOB_TOKEN", "").strip()
ML_DATABASE_URL = os.getenv("ML_DATABASE_URL", "").strip()
ML_CLOUDINARY_CLOUD_NAME = os.getenv("ML_CLOUDINARY_CLOUD_NAME", "").strip()
ML_CLOUDINARY_API_KEY = os.getenv("ML_CLOUDINARY_API_KEY", "").strip()
ML_CLOUDINARY_API_SECRET = os.getenv("ML_CLOUDINARY_API_SECRET", "").strip()
ML_CLOUDINARY_MODEL_FOLDER = os.getenv(
    "ML_CLOUDINARY_MODEL_FOLDER", "scraplink/models"
).strip().strip("/") or "scraplink/models"


def _configured_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if parsed < 0:
        raise ValueError(f"{name} must be non-negative")
    return parsed

def _configured_tickers() -> dict[str, str]:
    """Return the fixed public Yahoo ticker mapping used by the pipeline."""
    value = YAHOO_TICKERS_JSON
    if not value:
        return {}
    try:
        configured: Any = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError("YAHOO_TICKERS_JSON must contain valid JSON") from exc
    if not isinstance(configured, dict):
        raise ValueError("YAHOO_TICKERS_JSON must be a JSON object")
    return {str(ticker): str(material) for ticker, material in configured.items()}


# Non-secret global defaults.
PIPELINE_VERSION = "3.0.0"
SCHEMA_VERSION = "2.0.0"
FEATURE_VERSION = "3.0.0"
REFERENCE_FEATURE_VERSION = "1.0.0"
DATA_DIR = ML_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
SCRAPMONSTER_DIR = RAW_DIR / "ScrapMonster"
MCX_DIR = RAW_DIR / "MCX"
YAHOO_RAW_DIR = RAW_DIR / "Yahoo"
MIN_SCRAP_HISTORY_DAYS = 30
MIN_TRAINING_ROWS = 500
PREDICTION_HORIZON_DAYS = 1
TRAINING_WINDOW = "all"
MIN_SOURCE_ROWS = 1
MCX_ASOF_MAX_DAYS = 365
RANDOM_SEED = 42
PROMOTION_MAX_VALIDATION_MAE = _configured_float(
    "ML_PROMOTION_MAX_VALIDATION_MAE", float("inf")
)
YAHOO_TICKERS_JSON = '{"HG=F":"Copper","ALI=F":"Aluminium","ZNC=F":"Zinc"}'
YAHOO_TICKERS = _configured_tickers()
YAHOO_PERIOD = "max"
YAHOO_DAILY_PERIOD = "5d"
YAHOO_PRICE_FIELD = "Close"
