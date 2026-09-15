"""Validation and leakage checks for canonical ScrapLink datasets."""

from __future__ import annotations

from typing import Any

import pandas as pd


def validate_canonical_data(scrap: pd.DataFrame, mcx: pd.DataFrame) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    required_scrap = {
        "observation_date",
        "material",
        "scrap_type",
        "price_inr_per_kg",
        "source",
        "source_file",
        "source_hash",
    }
    required_mcx = {
        "observation_date",
        "commodity",
        "source",
        "source_file",
        "source_hash",
    }
    missing_scrap = sorted(required_scrap - set(scrap.columns))
    missing_mcx = sorted(required_mcx - set(mcx.columns))
    if missing_scrap:
        errors.append(f"Scrap canonical dataset missing columns: {missing_scrap}")
    if missing_mcx:
        errors.append(f"MCX canonical dataset missing columns: {missing_mcx}")

    if not scrap.empty:
        dates = pd.to_datetime(scrap["observation_date"], errors="coerce")
        if dates.isna().any():
            errors.append(f"Scrap dataset contains {int(dates.isna().sum())} invalid dates")
        prices = pd.to_numeric(scrap["price_inr_per_kg"], errors="coerce")
        invalid_prices = prices.isna() | (prices <= 0)
        if invalid_prices.any():
            errors.append(
                f"Scrap dataset contains {int(invalid_prices.sum())} invalid/non-positive prices"
            )
        if bool(scrap["is_synthetic"].fillna(False).any()):
            errors.append("Synthetic observations are present in the canonical scrap dataset")
        if pd.to_numeric(scrap["price_inr_per_kg"], errors="coerce").isin([float("inf"), float("-inf")]).any():
            errors.append("Scrap dataset contains infinite prices")
        if scrap["source_hash"].astype(str).str.len().lt(16).any():
            warnings.append("Some ScrapMonster rows have unusually short source hashes")
        duplicates = scrap.duplicated(
            ["observation_date", "material", "scrap_type", "source"]
        ).sum()
        if duplicates:
            warnings.append(f"Scrap semantic duplicate rows: {int(duplicates)}")

    if not mcx.empty:
        dates = pd.to_datetime(mcx["observation_date"], errors="coerce")
        if dates.isna().any():
            errors.append(f"MCX dataset contains {int(dates.isna().sum())} invalid dates")
        duplicates = mcx.duplicated(
            ["observation_date", "commodity", "instrument", "source_file"]
        ).sum()
        if duplicates:
            warnings.append(f"MCX duplicate contract rows: {int(duplicates)}")

    if errors:
        raise ValueError("; ".join(errors))
    return {
        "status": "passed",
        "warnings": warnings,
        "scrap_rows": int(len(scrap)),
        "mcx_rows": int(len(mcx)),
    }


def validate_reference_data(reference: pd.DataFrame) -> dict[str, Any]:
    """Validate Yahoo reference rows without assuming INR/kg semantics."""
    if reference.empty:
        return {
            "status": "not_available",
            "rows": 0,
            "warnings": ["No Yahoo reference snapshot is available."],
        }
    required = {
        "observation_date",
        "ticker",
        "reference_price",
        "source_currency",
        "source_unit",
        "source_hash",
        "is_synthetic",
    }
    missing = sorted(required - set(reference.columns))
    if missing:
        raise ValueError(f"Reference dataset missing columns: {missing}")
    dates = pd.to_datetime(reference["observation_date"], errors="coerce")
    prices = pd.to_numeric(reference["reference_price"], errors="coerce")
    if dates.isna().any():
        raise ValueError(f"Reference dataset contains {int(dates.isna().sum())} invalid dates")
    if (prices.isna() | (prices <= 0)).any():
        raise ValueError("Reference dataset contains invalid/non-positive prices")
    if bool(reference["is_synthetic"].fillna(False).any()):
        raise ValueError("Synthetic rows are present in the Yahoo reference dataset")
    return {
        "status": "passed",
        "rows": int(len(reference)),
        "tickers": sorted(reference["ticker"].dropna().astype(str).unique().tolist()),
        "warnings": [
            "Reference prices retain Yahoo native currency/unit; no INR/kg conversion was applied."
        ],
    }


def leakage_audit(
    features: pd.DataFrame, feature_columns: list[str], target: str
) -> dict[str, Any]:
    forbidden = {target, "price_inr_per_kg", "spot_price_inr_kg"}
    leaked_columns = sorted(forbidden.intersection(feature_columns))
    if leaked_columns:
        raise ValueError(f"Target columns are present in features: {leaked_columns}")
    if target not in features.columns:
        raise ValueError(f"Target column is missing: {target}")
    if "is_synthetic" in features and bool(features["is_synthetic"].fillna(False).any()):
        raise ValueError("Synthetic rows are present in the trainable dataset")

    return {
        "status": "passed",
        "target": target,
        "feature_count": len(feature_columns),
        "checks": {
            "current_target_in_features": False,
            "future_target_in_features": False,
            "synthetic_rows_present": False,
        },
    }


def chronological_split(
    data: pd.DataFrame,
    date_column: str = "observation_date",
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> dict[str, pd.DataFrame]:
    """Split whole dates chronologically; no date can occur in two partitions."""
    if not 0 < train_fraction < 1 or not 0 <= validation_fraction < 1:
        raise ValueError("Split fractions must be between zero and one")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("Train and validation fractions must leave a test set")
    if date_column not in data:
        raise ValueError(f"Missing split date column: {date_column}")
    frame = data.copy()
    frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce")
    frame = frame.dropna(subset=[date_column]).sort_values(date_column)
    dates = sorted(frame[date_column].dt.normalize().unique())
    if len(dates) < 3:
        raise ValueError("At least three distinct dates are required for chronological splitting")
    train_end = max(1, int(len(dates) * train_fraction))
    validation_end = max(train_end + 1, int(len(dates) * (train_fraction + validation_fraction)))
    validation_end = min(validation_end, len(dates) - 1)
    train_dates = set(dates[:train_end])
    validation_dates = set(dates[train_end:validation_end])
    test_dates = set(dates[validation_end:])
    return {
        "train": frame[frame[date_column].dt.normalize().isin(train_dates)].copy(),
        "validation": frame[frame[date_column].dt.normalize().isin(validation_dates)].copy(),
        "test": frame[frame[date_column].dt.normalize().isin(test_dates)].copy(),
    }
