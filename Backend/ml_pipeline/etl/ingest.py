"""Compatibility entry point for canonical source ingestion."""

from pathlib import Path

from .canonical import build_canonical_datasets


def clean_and_ingest_data(raw_csv_path: str | Path | None = None, processed_dir=None):
    """Build canonical ScrapMonster and MCX datasets.

    The legacy function name is retained for callers, but target prices are no
    longer filled, fabricated, or written with destructive database replacement.
    """
    result = build_canonical_datasets()
    return result["paths"]["scrap"]

