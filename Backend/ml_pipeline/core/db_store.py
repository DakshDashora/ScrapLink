"""Persistence helpers for the standalone ML pipeline database."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select, tuple_
from sqlalchemy.orm import Session

from .db_models import FeatureObservation, PipelineRun, SourceObservation
from ..etl.pipeline_config import FEATURE_VERSION
from ..etl.currency import convert_to_inr_per_kg


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
                "source_price": _value(row.get("source_price")),
                "price_inr_per_kg": _value(row.get("price_inr_per_kg")),
                "fx_rate_to_inr": _value(row.get("fx_rate_to_inr")),
                "fx_rate_date": (
                    pd.to_datetime(row.get("fx_rate_date"), errors="coerce").date()
                    if pd.notna(row.get("fx_rate_date"))
                    else None
                ),
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
    if not records:
        return {"attempted": 0, "inserted": 0, "updated": 0, "skipped": 0}

    key_columns = (
        SourceObservation.source,
        SourceObservation.observation_date,
        SourceObservation.material,
        SourceObservation.scrap_type,
        SourceObservation.commodity,
        SourceObservation.ticker,
        SourceObservation.source_hash,
    )
    inserted = 0
    updated = 0
    try:
        for source in ("ScrapMonster", "MCX", "YahooFinance"):
            source_records = [record for record in records if record["source"] == source]
            for offset in range(0, len(source_records), 400):
                batch = source_records[offset : offset + 400]
                batch_keys = [
                    tuple(record[column.key] for column in key_columns)
                    for record in batch
                ]
                existing = set(
                    db.execute(
                        select(*key_columns).where(tuple_(*key_columns).in_(batch_keys))
                    ).all()
                )
                statement = pg_insert(SourceObservation).values(batch)
                if source == "MCX":
                    statement = statement.on_conflict_do_nothing(
                        constraint="uq_ml_source_observation"
                    )
                else:
                    excluded = statement.excluded
                    statement = statement.on_conflict_do_update(
                        constraint="uq_ml_source_observation",
                        set_={
                            "source_price": excluded.source_price,
                            "price_inr_per_kg": excluded.price_inr_per_kg,
                            "fx_rate_to_inr": excluded.fx_rate_to_inr,
                            "fx_rate_date": excluded.fx_rate_date,
                            "reference_price": excluded.reference_price,
                            "source_currency": excluded.source_currency,
                            "source_unit": excluded.source_unit,
                            "traded_contract_lots": excluded.traded_contract_lots,
                            "total_value_lakhs": excluded.total_value_lakhs,
                            "avg_daily_turnover_lakhs": excluded.avg_daily_turnover_lakhs,
                            "premium_value_lakhs": excluded.premium_value_lakhs,
                            "source_file": excluded.source_file,
                        },
                    )
                result = db.execute(statement)
                affected = max(result.rowcount or 0, 0)
                if source == "MCX":
                    inserted += affected
                else:
                    updated += len(existing)
                    inserted += max(affected - len(existing), 0)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "attempted": len(records),
        "inserted": inserted,
        "updated": updated,
        "skipped": len(records) - inserted - updated,
    }


def backfill_scrap_price_conversions(db: Session) -> int:
    """Convert legacy ScrapMonster rows whose source price was stored unconverted."""
    rows = db.execute(
        select(SourceObservation).where(
            SourceObservation.source == "ScrapMonster",
            SourceObservation.source_price.is_(None),
        )
    ).scalars().all()
    updated = 0
    try:
        for row in rows:
            if row.price_inr_per_kg is None:
                raise ValueError(
                    f"ScrapMonster observation {row.id} has no price to normalize"
                )
            source_currency = (row.source_currency or "").strip()
            source_unit = (row.source_unit or "").strip()
            if not source_currency or not source_unit:
                raise ValueError(
                    f"ScrapMonster observation {row.id} has unknown source currency/unit; "
                    "refusing to assume INR/kg"
                )
            original_price = float(row.price_inr_per_kg)
            converted, rate, rate_date = convert_to_inr_per_kg(
                original_price,
                source_currency,
                source_unit,
                row.observation_date,
            )
            row.source_price = original_price
            row.price_inr_per_kg = converted
            row.fx_rate_to_inr = rate
            row.fx_rate_date = rate_date
            updated += 1
        if updated:
            db.commit()
    except Exception:
        db.rollback()
        raise
    return updated


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
    if not records:
        return {"attempted": 0, "inserted": 0, "updated": 0, "skipped": 0}

    key_columns = (
        FeatureObservation.target_source,
        FeatureObservation.observation_date,
        FeatureObservation.material,
        FeatureObservation.scrap_type,
        FeatureObservation.feature_version,
    )
    keys = [
        (
            record["target_source"],
            record["observation_date"],
            record["material"],
            record["scrap_type"],
            record["feature_version"],
        )
        for record in records
    ]
    existing = set(
        db.execute(select(*key_columns).where(tuple_(*key_columns).in_(keys))).all()
    )
    statement = pg_insert(FeatureObservation).values(records)
    excluded = statement.excluded
    statement = statement.on_conflict_do_update(
        constraint="uq_ml_feature_observation",
        set_={
            "target_price_inr_per_kg": excluded.target_price_inr_per_kg,
            "features": excluded.features,
        },
    )
    try:
        db.execute(statement)
        db.commit()
    except Exception:
        db.rollback()
        raise
    updated = len(existing)
    return {
        "attempted": len(records),
        "inserted": len(records) - updated,
        "updated": updated,
        "skipped": 0,
    }


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
        "source_price", "price_inr_per_kg", "fx_rate_to_inr", "fx_rate_date",
        "reference_price", "source_currency", "source_unit",
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
    scrap["market"] = pd.NA
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
