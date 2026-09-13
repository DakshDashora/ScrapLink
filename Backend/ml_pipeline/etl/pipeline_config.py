"""Shared paths and version information for the canonical data pipeline."""

import json
import os
from pathlib import Path


PIPELINE_VERSION = "2.1.0"
SCHEMA_VERSION = "1.1.0"
FEATURE_VERSION = "1.1.0"
REFERENCE_FEATURE_VERSION = "1.0.0"

ML_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ML_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
STAGING_DIR = DATA_DIR / "staging"
PROCESSED_DIR = DATA_DIR / "processed"
CANONICAL_DIR = DATA_DIR / "canonical"
FEATURES_DIR = DATA_DIR / "features"
REPORTS_DIR = DATA_DIR / "reports"

RAW_CONSOLIDATED_PATH = RAW_DIR / "raw_commodity_prices.csv"
MCX_DIR = RAW_DIR / "MCX"
YAHOO_RAW_DIR = RAW_DIR / "Yahoo"

SCRAP_CANONICAL_PATH = CANONICAL_DIR / "scrap_prices.csv"
MCX_CANONICAL_PATH = CANONICAL_DIR / "mcx_market_data.csv"
REFERENCE_CANONICAL_PATH = CANONICAL_DIR / "reference_prices.csv"
TRAINABLE_DATASET_PATH = FEATURES_DIR / "trainable_dataset.csv"
REFERENCE_DATASET_PATH = FEATURES_DIR / "reference_price_dataset.csv"
FEATURE_SCHEMA_PATH = FEATURES_DIR / "feature_schema.json"
FEATURE_DICTIONARY_PATH = FEATURES_DIR / "feature_dictionary.json"
REFERENCE_FEATURE_SCHEMA_PATH = FEATURES_DIR / "reference_feature_schema.json"
REFERENCE_FEATURE_DICTIONARY_PATH = FEATURES_DIR / "reference_feature_dictionary.json"
LEAKAGE_AUDIT_PATH = REPORTS_DIR / "leakage_audit.json"
REFERENCE_LEAKAGE_AUDIT_PATH = REPORTS_DIR / "reference_leakage_audit.json"
PIPELINE_MANIFEST_PATH = REPORTS_DIR / "pipeline_manifest.json"
EDA_DIR = REPORTS_DIR / "eda"


def _configured_tickers() -> dict[str, str]:
    """Return ticker-to-material mappings without requiring a network call."""
    value = os.getenv("SCRAPLINK_YAHOO_TICKERS", "").strip()
    if not value:
        return {}
    try:
        configured = json.loads(value)
        if isinstance(configured, dict):
            return {str(ticker): str(material) for ticker, material in configured.items()}
    except json.JSONDecodeError:
        pass
    return {
        item.split(":", 1)[0].strip(): item.split(":", 1)[1].strip()
        for item in value.split(",")
        if ":" in item and item.split(":", 1)[0].strip() and item.split(":", 1)[1].strip()
    }


YAHOO_TICKERS = _configured_tickers()
YAHOO_PERIOD = os.getenv("SCRAPLINK_YAHOO_PERIOD", "max")
YAHOO_PRICE_FIELD = os.getenv("SCRAPLINK_YAHOO_PRICE_FIELD", "Close")
