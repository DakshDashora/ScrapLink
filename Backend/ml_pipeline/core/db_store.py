"""Persistence helpers for the standalone ML pipeline database."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select
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


def _key_value(value: Any) -> str:
    value = _value(value)
    return "" if value is None else str(value)


def _insert_ignore_conflicts(
    db: Session,
    model: type[SourceObservation] | type[FeatureObservation],
    records: list[dict[str, Any]],
    constraint_name: str,
) -> dict[str, int]:
    if not records:
        return {"attempted": 0, "inserted": 0, "skipped": 0}

    statement = pg_insert(model).values(records).on_conflict_do_nothing(
        constraint=constraint_name
    )
    result = db.execute(statement)
    db.commit()
    inserted = result.rowcount if result.rowcount is not None and result.rowcount >= 0 else 0
    return {
        "attempted": len(records),
        "inserted": inserted,
        "skipped": len(records) - inserted,
    }


def persist_canonical_sources(
    db: Session,
    scrap: pd.DataFrame,
    mcx: pd.DataFrame,
    reference: pd.DataFrame,
) -> dict[str, int]:
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
                "material": _key_value(row.get("material")),
                "scrap_type": _key_value(row.get("scrap_type")),
                "commodity": _key_value(row.get("commodity")),
                "ticker": _key_value(row.get("ticker")),
                "price_inr_per_kg": _value(row.get("price_inr_per_kg")),
                "reference_price": _value(row.get("reference_price")),
                "source_currency": _value(row.get("source_currency")),
                "source_unit": _value(row.get("source_unit")),
                "traded_contract_lots": _value(row.get("traded_contract_lots")),
                "total_value_lakhs": _value(row.get("total_value_lakhs")),
                "avg_daily_turnover_lakhs": _value(row.get("avg_daily_turnover_lakhs")),
                "premium_value_lakhs": _value(row.get("premium_value_lakhs")),
                "source_file": str(row.get("source_file", "")),
                "source_hash": _key_value(row.get("source_hash", "")),
            }
            records.append(values)
    return _insert_ignore_conflicts(
        db,
        SourceObservation,
        records,
        "uq_ml_source_observation",
    )


def persist_features(db: Session, dataset: pd.DataFrame) -> dict[str, int]:
    records: list[dict[str, Any]] = []
    excluded = {
        "observation_date", "material", "scrap_type", "price_inr_per_kg",
        "source", "source_file", "source_hash", "is_synthetic",
    }
    for row in dataset.to_dict("records"):
        date = pd.to_datetime(row.get("observation_date"), errors="coerce")
        if pd.isna(date):
            continue
        material = _key_value(row["material"])
        scrap_type = _key_value(row.get("scrap_type", ""))
        features = {
            key: _value(value) for key, value in row.items() if key in dataset.columns and key not in excluded
        }
        records.append({
            "target_source": "ScrapMonster",
            "observation_date": date.date(),
            "material": material,
            "scrap_type": scrap_type,
            "target_price_inr_per_kg": _value(row.get("price_inr_per_kg")),
            "feature_version": FEATURE_VERSION,
            "features": features,
        })
    return _insert_ignore_conflicts(
        db,
        FeatureObservation,
        records,
        "uq_ml_feature_observation",
    )


def load_source_dataframes(db: Session) -> dict[str, pd.DataFrame]:
    """Load persisted source observations for database-first feature generation."""
    rows = db.execute(
        select(SourceObservation).order_by(
            SourceObservation.observation_date,
            SourceObservation.id,
        )
    ).scalars().all()
    source_columns = [
        "observation_date", "material", "scrap_type", "commodity", "ticker",
        "price_inr_per_kg", "reference_price", "source_currency", "source_unit",
        "traded_contract_lots", "total_value_lakhs", "avg_daily_turnover_lakhs",
        "premium_value_lakhs", "source_file", "source_hash",
    ]
    records = [
        {column: getattr(row, column) for column in source_columns}
        | {"source": row.source}
        for row in rows
    ]
    all_sources = pd.DataFrame(records, columns=["source", *source_columns])
    if all_sources.empty:
        return {
            "scrap": pd.DataFrame(),
            "mcx": pd.DataFrame(),
            "reference": pd.DataFrame(),
        }

    scrap = all_sources[all_sources["source"] == "ScrapMonster"].copy()
    scrap["is_synthetic"] = False
    scrap["source_price"] = scrap["price_inr_per_kg"]
    scrap["market"] = pd.NA
    scrap["fx_rate_to_inr"] = 1.0
    scrap["ingestion_timestamp"] = pd.NA

    mcx = all_sources[all_sources["source"] == "MCX"].copy()
    mcx["instrument"] = pd.NA
    mcx["segment"] = pd.NA
    mcx["ingestion_timestamp"] = pd.NA

    reference = all_sources[all_sources["source"] == "YahooFinance"].copy()
    reference["material"] = reference["material"].replace("", pd.NA)
    reference["ingestion_timestamp"] = pd.NA
    return {"scrap": scrap, "mcx": mcx, "reference": reference}


def load_feature_dataframe(db: Session) -> pd.DataFrame:
    """Load generated features from PostgreSQL for analysis and training."""
    rows = db.execute(
        select(FeatureObservation).order_by(
            FeatureObservation.observation_date,
            FeatureObservation.id,
        )
    ).scalars().all()
    records: list[dict[str, Any]] = []
    for row in rows:
        record = dict(row.features or {})
        record.update({
            "observation_date": row.observation_date,
            "material": row.material,
            "scrap_type": row.scrap_type,
            "price_inr_per_kg": row.target_price_inr_per_kg,
            "source": row.target_source,
            "is_synthetic": False,
        })
        records.append(record)
    return pd.DataFrame(records)
