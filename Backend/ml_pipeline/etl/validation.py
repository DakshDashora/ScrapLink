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
