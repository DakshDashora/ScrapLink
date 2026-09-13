"""Compatibility entry point for structured canonical EDA reports."""

from .canonical import build_canonical_datasets
from .pipeline_config import EDA_DIR
from .quality_reports import build_quality_reports


def perform_eda(processed_csv_path=None, reports_dir=None):
    """Generate non-overwriting data-quality reports for canonical datasets."""
    canonical = build_canonical_datasets()
    reports = build_quality_reports(
        canonical["scrap"],
        canonical["mcx"],
        EDA_DIR if reports_dir is None else reports_dir,
    )
    return reports["EDA.md"]
