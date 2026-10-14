"""Canonical ingestion for immutable ScrapMonster snapshots and MCX files."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .mcx_mapping import MCX_TO_SCRAPLINK
from .currency import convert_to_inr_per_kg
from .pipeline_config import (
    CANONICAL_DIR, MCX_CANONICAL_PATH, MCX_DIR, RAW_CONSOLIDATED_PATH,
    SCRAP_CANONICAL_PATH, SCRAPMONSTER_DIR, SCHEMA_VERSION,
)
from .scrapers import discover_mcx_files, discover_scrapmonster_files
from .yahoo import build_reference_canonical_dataset

SCRAP_COLUMNS = [
    "observation_date", "material", "scrap_type", "market", "source_price",
    "source_currency", "source_unit", "fx_rate_to_inr", "fx_rate_date",
    "price_inr_per_kg",
    "source", "source_file", "source_hash", "ingestion_timestamp", "is_synthetic",
]
MCX_COLUMNS = [
    "observation_date", "commodity", "instrument", "segment",
    "traded_contract_lots", "total_value_lakhs", "avg_daily_turnover_lakhs",
    "premium_value_lakhs", "source", "source_file", "source_hash",
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


def _material_mapping(name: Any) -> tuple[str, str]:
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
    if "steel" in lower or "hms" in lower or "iron" in lower or "bundle" in lower:
        return "Steel", normalized
    return normalized, normalized


def _load_scrap_source(path: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    raw = pd.read_csv(path)
    source_hash = _file_hash(path)
    # New scraper schema and the old consolidated export are both supported.
    date_col = "date" if "date" in raw else "observation_date"
    price_col = next(
        (col for col in ("source_price", "price_inr_per_kg", "spot_price_inr_kg")
         if col in raw),
        None,
    )
    if not {"commodity", date_col}.issubset(raw.columns) or price_col is None:
        raise ValueError(f"Scrap source {path.name} has no supported date/commodity/price schema")
    if "source" in raw:
        source_mask = raw["source"].astype(str).str.contains("ScrapMonster", case=False, na=False)
    else:
        source_mask = pd.Series(True, index=raw.index)
    prices = pd.to_numeric(raw[price_col], errors="coerce")
    valid_dates = pd.to_datetime(raw[date_col], errors="coerce", utc=True)
    valid = source_mask & prices.gt(0) & valid_dates.notna()
    accepted = raw.loc[valid].copy().reset_index(drop=True)
    if accepted.empty:
        return pd.DataFrame(columns=SCRAP_COLUMNS), {
            "read": int(len(raw)), "accepted": 0, "rejected": int(len(raw))
        }
    accepted_dates = valid_dates.loc[valid].reset_index(drop=True)
    accepted_prices = prices.loc[valid].reset_index(drop=True)
    pairs = accepted["commodity"].map(_material_mapping)
    if price_col == "source_price":
        if not {"source_currency", "source_unit"}.issubset(accepted.columns):
            raise ValueError(
                f"Scrap source {path.name} must specify source_currency and source_unit "
                "when it contains source_price"
            )
        currencies = accepted["source_currency"].astype(str).str.strip()
        units = accepted["source_unit"].astype(str).str.strip()
    else:
        currencies = pd.Series("INR", index=accepted.index)
        units = pd.Series("kg", index=accepted.index)
    converted = [
        convert_to_inr_per_kg(
            source_price,
            currency,
            unit,
            observation_date.date(),
        )
        for source_price, currency, unit, observation_date in zip(
            accepted_prices, currencies, units, accepted_dates
        )
    ]
    result = pd.DataFrame({
        "observation_date": accepted_dates.dt.date.astype("string"),
        "material": pairs.map(lambda pair: pair[0]),
        "scrap_type": pairs.map(lambda pair: pair[1]),
        "market": accepted.get("market", accepted.get("category", pd.Series(pd.NA, index=accepted.index))),
        "source_price": accepted_prices.astype(float),
        "source_currency": currencies,
        "source_unit": units,
        "fx_rate_to_inr": [item[1] for item in converted],
        "fx_rate_date": [item[2].isoformat() for item in converted],
        "price_inr_per_kg": [item[0] for item in converted],
        "source": "ScrapMonster",
        "source_file": str(path),
        "source_hash": source_hash,
        "ingestion_timestamp": _timestamp(),
        "is_synthetic": False,
    })
    return result[SCRAP_COLUMNS], {
        "read": int(len(raw)), "accepted": int(len(result)),
        "rejected": int(len(raw) - len(result)),
    }


def _load_mcx_file(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    aliases = {
        "Instrument": "instrument", "Date": "observation_date",
        "Segment": "segment", "Commodity": "commodity",
        "Traded Contract (Lots)": "traded_contract_lots",
        "Total Value (Lakhs)": "total_value_lakhs",
        "Avg Daily Turnover(Lakhs)": "avg_daily_turnover_lakhs",
        "Premium Value (Lakhs)": "premium_value_lakhs",
    }
    missing = sorted(set(aliases) - set(raw.columns))
    if missing:
        raise ValueError(f"MCX file {path.name} is missing columns: {missing}")
    mapped = raw["Commodity"].astype(str).str.strip().str.upper().map(MCX_TO_SCRAPLINK)
    supported = mapped.notna()
    def numeric(column: str) -> pd.Series:
        return pd.to_numeric(
            raw.loc[supported, column].astype(str).str.replace("-", "", regex=False),
            errors="coerce",
        )
    return pd.DataFrame({
        "observation_date": pd.to_datetime(raw.loc[supported, "Date"], errors="coerce", dayfirst=True).dt.date.astype("string"),
        "commodity": mapped.loc[supported].map(lambda value: value["name"]),
        "instrument": raw.loc[supported, "Instrument"].astype("string"),
        "segment": raw.loc[supported, "Segment"].astype("string"),
        "traded_contract_lots": numeric("Traded Contract (Lots)"),
        "total_value_lakhs": numeric("Total Value (Lakhs)"),
        "avg_daily_turnover_lakhs": numeric("Avg Daily Turnover(Lakhs)"),
        "premium_value_lakhs": numeric("Premium Value (Lakhs)"),
        "source": "MCX", "source_file": str(path), "source_hash": _file_hash(path),
        "ingestion_timestamp": _timestamp(),
    })[MCX_COLUMNS]


def _scrap_files() -> list[Path]:
    return discover_scrapmonster_files(SCRAPMONSTER_DIR)


def build_canonical_datasets() -> dict[str, Any]:
    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)
    scrap_parts: list[pd.DataFrame] = []
    source_stats: list[dict[str, Any]] = []
    for path in _scrap_files():
        part, stats = _load_scrap_source(path)
        scrap_parts.append(part)
        source_stats.append({"source_file": str(path), **stats})
    scrap = (
        pd.concat(scrap_parts, ignore_index=True)
        if scrap_parts else pd.DataFrame(columns=SCRAP_COLUMNS)
    )
    before_dedup = len(scrap)
    if not scrap.empty:
        scrap = scrap.drop_duplicates(
            ["observation_date", "material", "scrap_type", "source"], keep="last"
        ).sort_values(["observation_date", "material", "scrap_type"]).reset_index(drop=True)

    mcx_files = discover_mcx_files(MCX_DIR)
    mcx_parts = [_load_mcx_file(path) for path in mcx_files]
    mcx = pd.concat(mcx_parts, ignore_index=True) if mcx_parts else pd.DataFrame(columns=MCX_COLUMNS)
    if not mcx.empty:
        mcx = mcx.drop_duplicates(
            ["observation_date", "commodity", "instrument", "source_file"]
        ).reset_index(drop=True)
    reference_result = build_reference_canonical_dataset()
    scrap.to_csv(SCRAP_CANONICAL_PATH, index=False)
    mcx.to_csv(MCX_CANONICAL_PATH, index=False)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "scrap_rows": int(len(scrap)), "mcx_rows": int(len(mcx)),
        "scrap_source_files": sorted(scrap["source_file"].unique().tolist()) if not scrap.empty else [],
        "mcx_source_files": sorted(mcx["source_file"].unique().tolist()) if not mcx.empty else [],
        "scrap_rows_read": int(sum(item["read"] for item in source_stats)),
        "scrap_rows_rejected": int(sum(item["rejected"] for item in source_stats)),
        "scrap_duplicate_rows_removed": int(before_dedup - len(scrap)),
        "source_stats": source_stats,
        "reference": reference_result["manifest"],
        "synthetic_rows_excluded": 0,
    }
    return {
        "scrap": scrap, "mcx": mcx, "reference": reference_result["data"],
        "manifest": manifest,
        "paths": {"scrap": str(SCRAP_CANONICAL_PATH), "mcx": str(MCX_CANONICAL_PATH),
                  "reference": reference_result["path"]},
    }
