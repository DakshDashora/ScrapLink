"""Canonical, reproducible data-pipeline entry point.

Run from the Backend directory with:
    python -m ml_pipeline.run_pipeline
"""

import json
import time

from .etl.canonical import build_canonical_datasets
from .etl.pipeline_config import (
    EDA_DIR,
    FEATURE_VERSION,
    LEAKAGE_AUDIT_PATH,
    REFERENCE_LEAKAGE_AUDIT_PATH,
    PIPELINE_MANIFEST_PATH,
    PIPELINE_VERSION,
)
from .etl.quality_reports import build_quality_reports
from .etl.reference_features import build_reference_price_dataset
from .etl.trainable import build_trainable_dataset
from .etl.validation import validate_canonical_data, validate_reference_data
from .logger import logger


def run_full_ml_data_pipeline() -> dict:
    started = time.time()
    logger.info("Starting ScrapLink canonical ML data pipeline")

    canonical = build_canonical_datasets()
    validation = validate_canonical_data(canonical["scrap"], canonical["mcx"])
    reference_validation = validate_reference_data(canonical["reference"])
    reports = build_quality_reports(
        canonical["scrap"], canonical["mcx"], EDA_DIR, canonical["reference"]
    )
    trainable = build_trainable_dataset()
    reference_trainable = build_reference_price_dataset()

    LEAKAGE_AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEAKAGE_AUDIT_PATH.write_text(
        json.dumps(trainable["leakage_audit"], indent=2), encoding="utf-8"
    )
    REFERENCE_LEAKAGE_AUDIT_PATH.write_text(
        json.dumps(reference_trainable["leakage_audit"], indent=2), encoding="utf-8"
    )
    manifest = {
        "pipeline_version": PIPELINE_VERSION,
        "feature_version": FEATURE_VERSION,
        "generation_seconds": round(time.time() - started, 3),
        "validation": validation,
        "reference_validation": reference_validation,
        "canonical": canonical["manifest"],
        "trainable_rows": int(len(trainable["dataset"])),
        "trainable_path": trainable["path"],
        "reference_dataset": reference_trainable.get("metadata", {}),
        "reference_dataset_path": reference_trainable["path"],
        "model_training": "not_run",
        "reports": reports,
    }
    PIPELINE_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PIPELINE_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info(
        "Pipeline complete: scrap=%s, mcx=%s, scrap_trainable=%s, reference_trainable=%s",
        len(canonical["scrap"]),
        len(canonical["mcx"]),
        len(trainable["dataset"]),
        len(reference_trainable["dataset"]),
    )
    return manifest


if __name__ == "__main__":
    run_full_ml_data_pipeline()
