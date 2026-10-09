"""Canonical paths and versions for the ML pipeline."""

from __future__ import annotations

from ..utils import (
    DATA_DIR,
    FEATURE_VERSION,
    MCX_DIR,
    MCX_ASOF_MAX_DAYS,
    MIN_SCRAP_HISTORY_DAYS,
    MIN_SOURCE_ROWS,
    MIN_TRAINING_ROWS,
    PIPELINE_VERSION,
    PREDICTION_HORIZON_DAYS,
    REFERENCE_FEATURE_VERSION,
    RAW_DIR,
    RANDOM_SEED,
    SCRAPMONSTER_DIR,
    SCHEMA_VERSION,
    TRAINING_WINDOW,
    YAHOO_PERIOD,
    YAHOO_DAILY_PERIOD,
    YAHOO_PRICE_FIELD,
    YAHOO_RAW_DIR,
    YAHOO_TICKERS,
)

STAGING_DIR = DATA_DIR / "staging"
PROCESSED_DIR = DATA_DIR / "processed"
CANONICAL_DIR = DATA_DIR / "canonical"
FEATURES_DIR = DATA_DIR / "features"
REPORTS_DIR = DATA_DIR / "reports"

RAW_CONSOLIDATED_PATH = RAW_DIR / "raw_commodity_prices.csv"
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
SOURCE_REGISTRY_PATH = REPORTS_DIR / "source_registry.csv"
