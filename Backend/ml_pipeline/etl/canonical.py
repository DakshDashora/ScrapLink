"""Canonical source ingestion and normalization for ScrapLink ML data."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .mcx_mapping import MCX_TO_SCRAPLINK
from .pipeline_config import (
    CANONICAL_DIR,
    MCX_CANONICAL_PATH,
    MCX_DIR,
    RAW_CONSOLIDATED_PATH,
    SCRAP_CANONICAL_PATH,
    SCHEMA_VERSION,
)
from .yahoo import build_reference_canonical_dataset


SCRAP_COLUMNS = [
    "observation_date",
    "material",
    "scrap_type",
    "market",
    "source_price",
    "source_currency",
    "source_unit",
    "fx_rate_to_inr",
    "price_inr_per_kg",
    "source",
    "source_file",
    "source_hash",
    "ingestion_timestamp",
    "is_synthetic",
]

MCX_COLUMNS = [
    "observation_date",
    "commodity",
    "instrument",
    "segment",
    "traded_contract_lots",
    "total_value_lakhs",
    "avg_daily_turnover_lakhs",
    "premium_value_lakhs",
    "source",
    "source_file",
    "source_hash",
    "ingestion_timestamp",
]


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _material_mapping(name: str) -> tuple[str, str]:
    normalized = str(name).strip()
    lower = normalized.lower()
    if "copper" in lower:
        return "Copper", normalized
    if "alum" in lower:
        return "Aluminium", normalized
    if "brass" in lower:
        return "Brass", normalized
    if "zinc" in lower:
        return "Zinc", normalized
    if "lead" in lower:
        return "Lead", normalized
    if "steel" in lower or "hms" in lower or "iron" in lower:
        return "Steel", normalized
    return normalized, normalized


def _load_scrap_source(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Scrap source snapshot not found: {path}")

    raw = pd.read_csv(path)
    required = {"date", "commodity", "spot_price_inr_kg", "source"}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"Scrap source is missing required columns: {missing}")

    source_rows = raw[
        raw["source"].astype(str).eq("ScrapMonster_Live_Web")
        & raw["spot_price_inr_kg"].notna()
    ].copy()
    if source_rows.empty:
        raise ValueError("No ScrapMonster rows were found in the source snapshot")

    source_rows["spot_price_inr_kg"] = pd.to_numeric(
        source_rows["spot_price_inr_kg"], errors="coerce"
    )
    source_rows = source_rows[source_rows["spot_price_inr_kg"] > 0].copy()
    if source_rows.empty:
        raise ValueError("No valid positive ScrapMonster prices were found")

    source_hash = _file_hash(path)
    now = _timestamp()
    material_pairs = source_rows["commodity"].map(_material_mapping)
    result = pd.DataFrame(
        {
            "observation_date": pd.to_datetime(
                source_rows["date"], errors="coerce", utc=True
            ).dt.date.astype("string"),
            "material": material_pairs.map(lambda value: value[0]),
            "scrap_type": material_pairs.map(lambda value: value[1]),
            "market": pd.NA,
            "source_price": pd.to_numeric(
                source_rows["spot_price_inr_kg"], errors="coerce"
            ),
            "source_currency": "INR",
            "source_unit": "kg",
            "fx_rate_to_inr": 1.0,
            "price_inr_per_kg": pd.to_numeric(
                source_rows["spot_price_inr_kg"], errors="coerce"
            ),
            "source": "ScrapMonster",
            "source_file": str(path),
            "source_hash": source_hash,
            "ingestion_timestamp": now,
            "is_synthetic": False,
        }
    )
    return result[SCRAP_COLUMNS]


def _load_mcx_file(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    required = {
        "Instrument",
        "Date",
        "Segment",
        "Commodity",
        "Traded Contract (Lots)",
        "Total Value (Lakhs)",
        "Avg Daily Turnover(Lakhs)",
        "Premium Value (Lakhs)",
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"MCX file {path.name} is missing columns: {missing}")

    mapped = raw["Commodity"].astype(str).str.strip().str.upper().map(MCX_TO_SCRAPLINK)
    supported = mapped.notna()
    now = _timestamp()
    return pd.DataFrame(
        {
            "observation_date": pd.to_datetime(
                raw.loc[supported, "Date"], errors="coerce", utc=True
            ).dt.date.astype("string"),
            "commodity": mapped.loc[supported].map(lambda value: value["name"]),
            "instrument": raw.loc[supported, "Instrument"].astype("string"),
            "segment": raw.loc[supported, "Segment"].astype("string"),
            "traded_contract_lots": pd.to_numeric(
                raw.loc[supported, "Traded Contract (Lots)"], errors="coerce"
            ),
            "total_value_lakhs": pd.to_numeric(
                raw.loc[supported, "Total Value (Lakhs)"], errors="coerce"
            ),
            "avg_daily_turnover_lakhs": pd.to_numeric(
                raw.loc[supported, "Avg Daily Turnover(Lakhs)"], errors="coerce"
            ),
            "premium_value_lakhs": pd.to_numeric(
                raw.loc[supported, "Premium Value (Lakhs)"], errors="coerce"
            ),
            "source": "MCX",
            "source_file": str(path),
            "source_hash": _file_hash(path),
            "ingestion_timestamp": now,
        }
    )[MCX_COLUMNS]


def build_canonical_datasets() -> dict[str, Any]:
    """Build canonical ScrapMonster, MCX, and optional Yahoo reference datasets."""
    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)

    raw_snapshot = pd.read_csv(RAW_CONSOLIDATED_PATH)
    scrap_source_rows = raw_snapshot[
        raw_snapshot["source"].astype(str).eq("ScrapMonster_Live_Web")
    ]
    scrap_numeric = pd.to_numeric(
        scrap_source_rows["spot_price_inr_kg"], errors="coerce"
    )
    rejected_scrap_rows = int((scrap_numeric.isna() | (scrap_numeric <= 0)).sum())
    scrap = _load_scrap_source(RAW_CONSOLIDATED_PATH)
    mcx_files = sorted(MCX_DIR.glob("*.csv"))
    mcx_parts = [_load_mcx_file(path) for path in mcx_files]
    mcx = (
        pd.concat(mcx_parts, ignore_index=True)
        if mcx_parts
        else pd.DataFrame(columns=MCX_COLUMNS)
    )
    reference_result = build_reference_canonical_dataset()
    reference = reference_result["data"]

    scrap.to_csv(SCRAP_CANONICAL_PATH, index=False)
    mcx.to_csv(MCX_CANONICAL_PATH, index=False)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "scrap_rows": int(len(scrap)),
        "mcx_rows": int(len(mcx)),
        "scrap_source_files": sorted(scrap["source_file"].unique().tolist()),
        "mcx_source_files": sorted(mcx["source_file"].unique().tolist()),
        "reference": reference_result["manifest"],
        "scrap_rows_read": int(len(scrap_source_rows)),
        "scrap_rows_rejected": rejected_scrap_rows,
        "synthetic_rows_excluded": int(
            raw_snapshot.get("source", pd.Series(dtype="string"))
            .astype(str)
            .eq("Exchange_Baseline")
            .sum()
        ),
    }
    return {
        "scrap": scrap,
        "mcx": mcx,
        "reference": reference,
        "manifest": manifest,
        "paths": {
            "scrap": str(SCRAP_CANONICAL_PATH),
            "mcx": str(MCX_CANONICAL_PATH),
            "reference": reference_result["path"],
        },
    }
