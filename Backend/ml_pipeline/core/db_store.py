"""Persistence helpers for the standalone ML pipeline database."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from .db_models import FeatureObservation, PipelineRun, SourceObservation
from ..etl.pipeline_config import FEATURE_VERSION


def start_run(db: Session, job_type: str) -> PipelineRun:
    run = PipelineRun(job_type=job_type, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def finish_run(
    db: Session,
    run: PipelineRun,
    status: str,
    *,
    details: dict[str, Any] | None = None,
    rows_read: int | None = None,
    rows_written: int | None = None,
    error_message: str | None = None,
) -> None:
    run.status = status
    run.details = details
    run.rows_read = rows_read
    run.rows_written = rows_written
    run.error_message = error_message
    run.completed_at = datetime.now(timezone.utc)
    db.commit()


def _value(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def persist_canonical_sources(db: Session, scrap: pd.DataFrame, mcx: pd.DataFrame, reference: pd.DataFrame) -> int:
    records: list[dict[str, Any]] = []
    frames = [
        ("ScrapMonster", scrap, "scrap"),
        ("MCX", mcx, "mcx"),
        ("YahooFinance", reference, "reference"),
    ]
    for source, frame, kind in frames:
        for row in frame.to_dict("records"):
            date = pd.to_datetime(row.get("observation_date"), errors="coerce")
            if pd.isna(date):
                continue
            values = {
                "source": source,
                "observation_date": date.date(),
                "material": _value(row.get("material")),
                "scrap_type": _value(row.get("scrap_type")),
                "commodity": _value(row.get("commodity")),
                "ticker": _value(row.get("ticker")),
                "price_inr_per_kg": _value(row.get("price_inr_per_kg")),
                "reference_price": _value(row.get("reference_price")),
                "source_currency": _value(row.get("source_currency")),
                "source_unit": _value(row.get("source_unit")),
                "traded_contract_lots": _value(row.get("traded_contract_lots")),
                "total_value_lakhs": _value(row.get("total_value_lakhs")),
                "avg_daily_turnover_lakhs": _value(row.get("avg_daily_turnover_lakhs")),
                "premium_value_lakhs": _value(row.get("premium_value_lakhs")),
                "source_file": str(row.get("source_file", "")),
                "source_hash": str(row.get("source_hash", "")),
            }
            records.append(values)
    if records:
        db.bulk_insert_mappings(SourceObservation, records)
    db.commit()
    return len(records)


def persist_features(db: Session, dataset: pd.DataFrame) -> int:
    records: list[dict[str, Any]] = []
    excluded = {
        "observation_date", "material", "scrap_type", "price_inr_per_kg",
        "source", "source_file", "source_hash", "is_synthetic",
    }
    for row in dataset.to_dict("records"):
        date = pd.to_datetime(row.get("observation_date"), errors="coerce")
        if pd.isna(date):
            continue
        material = str(row["material"])
        scrap_type = str(row.get("scrap_type", ""))
        features = {
            key: _value(value) for key, value in row.items() if key in dataset.columns and key not in excluded
        }
        records.append({
            target_source="ScrapMonster", observation_date=date.date(),
            material=material, scrap_type=scrap_type,
            target_price_inr_per_kg=_value(row.get("price_inr_per_kg")),
            feature_version=FEATURE_VERSION, features=features,
        })
    if records:
        db.bulk_insert_mappings(FeatureObservation, records)
    db.commit()
    return len(records)
