"""Yahoo Finance historical source connector and canonical reference ingestion.

Yahoo rows are market reference observations only.  This module never converts
currency or units and never fills missing observations.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .pipeline_config import (
    REFERENCE_CANONICAL_PATH,
    RAW_CONSOLIDATED_PATH,
    YAHOO_PERIOD,
    YAHOO_PRICE_FIELD,
    YAHOO_RAW_DIR,
    YAHOO_DAILY_PERIOD,
    YAHOO_TICKERS,
)


YAHOO_RAW_COLUMNS = [
    "observation_date",
    "ticker",
    "material",
    "Open",
    "High",
    "Low",
    "Close",
    "Adj Close",
    "Volume",
    "source_currency",
    "source_unit",
    "price_field",
    "source",
]

REFERENCE_COLUMNS = [
    "observation_date",
    "ticker",
    "material",
    "reference_price",
    "price_field",
    "source_currency",
    "source_unit",
    "source",
    "source_file",
    "source_hash",
    "ingestion_timestamp",
    "is_synthetic",
]


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _metadata(ticker: str) -> tuple[str | pd.NA, str]:
    """Read only Yahoo metadata; unknown values remain explicitly unknown."""
    import yfinance as yf

    try:
        info = dict(yf.Ticker(ticker).fast_info)
    except Exception:
        info = {}
    currency = info.get("currency", pd.NA)
    quote_type = str(info.get("quoteType", "")).upper()
    if quote_type == "EQUITY":
        unit = "share"
    elif quote_type in {"FUTURE", "INDEX"}:
        unit = "contract" if quote_type == "FUTURE" else "index_point"
    else:
        unit = "native_quote_unit"
    return currency, unit


def _configured_output(path: str | Path | None) -> Path:
    if path is not None:
        return Path(path)
    return YAHOO_RAW_DIR / f"yahoo_history_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.csv"


def _flatten_history(history: pd.DataFrame, tickers: dict[str, str]) -> pd.DataFrame:
    if history.empty:
        return pd.DataFrame(columns=YAHOO_RAW_COLUMNS)
    rows: list[pd.DataFrame] = []
    multi = isinstance(history.columns, pd.MultiIndex)
    for ticker, material in tickers.items():
        if multi:
            level = 0 if ticker in history.columns.get_level_values(0) else -1
            if ticker not in history.columns.get_level_values(level):
                continue
            part = history.xs(ticker, axis=1, level=level, drop_level=True).copy()
        else:
            part = history.copy()
        if part.empty:
            continue
        part = part.rename_axis("observation_date").reset_index()
        part["ticker"] = ticker
        part["material"] = material
        currency, unit = _metadata(ticker)
        part["source_currency"] = currency
        part["source_unit"] = unit
        part["price_field"] = YAHOO_PRICE_FIELD
        part["source"] = "YahooFinance"
        for column in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
            if column not in part:
                part[column] = pd.NA
        rows.append(part[YAHOO_RAW_COLUMNS])
    if not rows:
        return pd.DataFrame(columns=YAHOO_RAW_COLUMNS)
    result = pd.concat(rows, ignore_index=True)
    result["observation_date"] = pd.to_datetime(
        result["observation_date"], errors="coerce", utc=True
    ).dt.strftime("%Y-%m-%d")
    return result


def download_yahoo_history(
    output_path: str | Path | None = None,
    tickers: dict[str, str] | Iterable[str] | None = None,
    period: str | None = None,
) -> Path:
    """Download configured Yahoo history to a write-once raw CSV."""
    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError(
            "Yahoo ingestion requires the existing yfinance dependency. "
            "Install Backend requirements before downloading history."
        ) from exc
    ticker_map = (
        YAHOO_TICKERS
        if tickers is None
        else (
            tickers
            if isinstance(tickers, dict)
            else {str(ticker): str(ticker) for ticker in tickers}
        )
    )
    if not ticker_map:
        raise ValueError(
            "No Yahoo tickers configured. Set SCRAPLINK_YAHOO_TICKERS "
            "to JSON (e.g. {\"HG=F\":\"Copper\"}) or ticker:material pairs."
        )
    history = yf.download(
        tickers=list(ticker_map),
        period=period or YAHOO_PERIOD,
        auto_adjust=False,
        actions=False,
        group_by="ticker",
        progress=False,
        threads=False,
    )
    rows = _flatten_history(history, ticker_map)
    if rows.empty:
        raise ValueError("Yahoo returned no historical rows")
    path = _configured_output(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"Immutable Yahoo raw output already exists: {path}")
    rows.to_csv(path, index=False)
    return path


def _latest_raw_path(raw_dir: Path = YAHOO_RAW_DIR) -> Path | None:
    paths = sorted(raw_dir.glob("*.csv"))
    return paths[-1] if paths else None


def discover_yahoo_files(raw_dir: Path = YAHOO_RAW_DIR) -> list[Path]:
    """Return all immutable Yahoo snapshots in deterministic order."""
    return sorted(raw_dir.glob("*.csv"))


def collect_daily_yahoo_history() -> Path:
    """Collect a small recent Yahoo window for the daily source job."""
    return download_yahoo_history(period=YAHOO_DAILY_PERIOD)


def _legacy_consolidated_reference() -> pd.DataFrame:
    """Load the existing Yahoo snapshot when no dedicated raw snapshot exists.

    The legacy file is retained as an input for continuity, but its rows are
    marked with a stable legacy ticker because the old export did not preserve
    Yahoo ticker symbols.
    """
    if not RAW_CONSOLIDATED_PATH.exists():
        return pd.DataFrame(columns=REFERENCE_COLUMNS)
    raw = pd.read_csv(RAW_CONSOLIDATED_PATH)
    required = {"date", "commodity", "spot_price_inr_kg", "source"}
    if not required.issubset(raw.columns):
        return pd.DataFrame(columns=REFERENCE_COLUMNS)
    rows = raw[raw["source"].astype(str).eq("Yahoo_Finance_API")].copy()
    if rows.empty:
        return pd.DataFrame(columns=REFERENCE_COLUMNS)
    rows["reference_price"] = pd.to_numeric(rows["spot_price_inr_kg"], errors="coerce")
    rows = rows[rows["reference_price"].notna() & rows["reference_price"].gt(0)].copy()
    if rows.empty:
        return pd.DataFrame(columns=REFERENCE_COLUMNS)
    rows["observation_date"] = pd.to_datetime(
        rows["date"], errors="coerce", utc=True
    ).dt.strftime("%Y-%m-%d")
    rows["ticker"] = "legacy:" + rows["commodity"].astype(str).str.strip()
    rows["material"] = rows["commodity"].astype(str).str.strip()
    rows["price_field"] = "spot_price_inr_kg"
    rows["source_currency"] = "INR"
    rows["source_unit"] = "kg"
    rows["source"] = "YahooFinanceLegacySnapshot"
    rows["source_file"] = str(RAW_CONSOLIDATED_PATH)
    rows["source_hash"] = _file_hash(RAW_CONSOLIDATED_PATH)
    rows["ingestion_timestamp"] = _timestamp()
    rows["is_synthetic"] = False
    return rows[REFERENCE_COLUMNS]


def build_reference_canonical_dataset(
    raw_path: str | Path | None = None,
) -> dict[str, Any]:
    """Normalize verified Yahoo close rows without currency/unit conversion."""
    raw_paths = [Path(raw_path)] if raw_path is not None else discover_yahoo_files()
    raw_paths = [path for path in raw_paths if path.exists()]
    if not raw_paths:
        empty = pd.DataFrame(columns=REFERENCE_COLUMNS)
        return {
            "data": empty,
            "path": str(REFERENCE_CANONICAL_PATH),
            "manifest": {
                "status": "not_available",
                "rows": 0,
                "source": "YahooFinance",
                "limitation": "No dedicated Yahoo raw snapshot is available.",
            },
        }
    raw = pd.concat([pd.read_csv(source) for source in raw_paths], ignore_index=True)
    required = {"observation_date", "ticker", "material", YAHOO_PRICE_FIELD}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"Yahoo raw source is missing required columns: {missing}")
    result = raw.copy()
    result["reference_price"] = pd.to_numeric(result[YAHOO_PRICE_FIELD], errors="coerce")
    result["observation_date"] = pd.to_datetime(
        result["observation_date"], errors="coerce", utc=True
    ).dt.strftime("%Y-%m-%d")
    result = result[result["reference_price"].notna()].copy()
    result = result[result["reference_price"] > 0].copy()
    result["price_field"] = YAHOO_PRICE_FIELD
    result["source"] = "YahooFinance"
    result["source_file"] = result.get("source_file", pd.NA)
    result["source_hash"] = result.get("source_hash", pd.NA)
    if result["source_file"].isna().all():
        result["source_file"] = str(raw_paths[0]) if len(raw_paths) == 1 else "Yahoo:multiple_snapshots"
    if result["source_hash"].isna().all():
        result["source_hash"] = _file_hash(raw_paths[0]) if len(raw_paths) == 1 else "multiple_snapshot_hashes"
    result["ingestion_timestamp"] = _timestamp()
    result["is_synthetic"] = False
    for column in ["source_currency", "source_unit"]:
        if column not in result:
            result[column] = pd.NA
    canonical = result[REFERENCE_COLUMNS].sort_values(
        ["ticker", "observation_date"]
    ).reset_index(drop=True)
    REFERENCE_CANONICAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    canonical.to_csv(REFERENCE_CANONICAL_PATH, index=False)
    return {
        "data": canonical,
        "path": str(REFERENCE_CANONICAL_PATH),
        "manifest": {
            "status": "available",
            "rows": int(len(canonical)),
            "source": "YahooFinance",
            "source_files": [str(source) for source in raw_paths],
            "price_field": YAHOO_PRICE_FIELD,
            "currency_conversion": False,
            "unit_conversion": False,
        },
    }
