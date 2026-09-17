"""Leakage-safe supervised features for Yahoo public-market references."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from .pipeline_config import (
    MCX_CANONICAL_PATH,
    REFERENCE_CANONICAL_PATH,
    REFERENCE_DATASET_PATH,
    REFERENCE_FEATURE_DICTIONARY_PATH,
    REFERENCE_FEATURE_SCHEMA_PATH,
    REFERENCE_FEATURE_VERSION,
    FEATURES_DIR,
)
from .validation import leakage_audit


TARGET = "reference_price"
FEATURE_COLUMNS = [
    "observation_day_of_week",
    "observation_month",
    "observation_quarter",
    "reference_price_lag_1",
    "reference_price_lag_7",
    "reference_price_lag_14",
    "reference_price_lag_30",
    "reference_return_1",
    "reference_return_7",
    "reference_return_30",
    "reference_ma_7",
    "reference_ma_30",
    "reference_volatility_7",
    "reference_volatility_30",
    "mcx_traded_contract_lots_lag_1",
    "mcx_traded_contract_lots_lag_7",
    "mcx_traded_contract_lots_ma_7",
    "mcx_avg_daily_turnover_lakhs_lag_1",
    "mcx_avg_daily_turnover_lakhs_lag_7",
    "mcx_avg_daily_turnover_lakhs_ma_7",
    "has_reference_history",
    "has_mcx_history",
]


def _add_reference_features(group: pd.DataFrame) -> pd.DataFrame:
    group = group.sort_values("observation_date").copy()
    prices = pd.to_numeric(group[TARGET], errors="coerce")
    history = prices.shift(1)
    group["reference_price_lag_1"] = history
    group["reference_price_lag_7"] = prices.shift(7)
    group["reference_price_lag_14"] = prices.shift(14)
    group["reference_price_lag_30"] = prices.shift(30)
    group["reference_return_1"] = history.pct_change(1, fill_method=None)
    group["reference_return_7"] = history.pct_change(7, fill_method=None)
    group["reference_return_30"] = history.pct_change(30, fill_method=None)
    group["reference_ma_7"] = history.rolling(7, min_periods=7).mean()
    group["reference_ma_30"] = history.rolling(30, min_periods=30).mean()
    prior_returns = history.pct_change(fill_method=None)
    group["reference_volatility_7"] = prior_returns.rolling(7, min_periods=7).std()
    group["reference_volatility_30"] = prior_returns.rolling(30, min_periods=30).std()
    group["has_reference_history"] = group["reference_price_lag_1"].notna().astype("int8")
    return group


def _mcx_asof_features(reference: pd.DataFrame, mcx: pd.DataFrame) -> pd.DataFrame:
    output_columns = [
        "mcx_traded_contract_lots_lag_1",
        "mcx_traded_contract_lots_lag_7",
        "mcx_traded_contract_lots_ma_7",
        "mcx_avg_daily_turnover_lakhs_lag_1",
        "mcx_avg_daily_turnover_lakhs_lag_7",
        "mcx_avg_daily_turnover_lakhs_ma_7",
    ]
    if mcx.empty:
        for column in output_columns:
            reference[column] = pd.NA
        reference["has_mcx_history"] = 0
        return reference

    reference = reference.copy()
    reference["observation_date"] = pd.to_datetime(
        reference["observation_date"], errors="coerce"
    ).dt.normalize()
    mcx = mcx.copy()
    mcx["observation_date"] = pd.to_datetime(
        mcx["observation_date"], errors="coerce"
    ).dt.normalize()
    material_map = {
        "Copper": "Copper",
        "Aluminum": "Aluminium",
        "Aluminium": "Aluminium",
        "Zinc": "Zinc",
        "Lead": "Lead",
        "Steel": "Steel",
    }
    mcx["material"] = mcx["commodity"].map(material_map)
    mcx = mcx.dropna(subset=["material"])
    mcx = mcx.groupby(["observation_date", "material"], as_index=False)[
        ["traded_contract_lots", "avg_daily_turnover_lakhs"]
    ].sum(min_count=1)
    mcx = mcx.sort_values(["material", "observation_date"])
    for source, prefix in [
        ("traded_contract_lots", "mcx_traded_contract_lots"),
        ("avg_daily_turnover_lakhs", "mcx_avg_daily_turnover_lakhs"),
    ]:
        mcx[f"{prefix}_lag_1"] = mcx.groupby("material")[source].shift(1)
        mcx[f"{prefix}_lag_7"] = mcx.groupby("material")[source].shift(7)
        mcx[f"{prefix}_ma_7"] = mcx.groupby("material")[source].transform(
            lambda values: values.shift(1).rolling(7, min_periods=7).mean()
        )

    groups: list[pd.DataFrame] = []
    for material, left in reference.groupby("material", dropna=False, sort=False):
        left = left.sort_values("observation_date").copy()
        right = mcx[mcx["material"].eq(material)].sort_values("observation_date")
        if right.empty:
            for column in output_columns:
                left[column] = pd.NA
        else:
            left = pd.merge_asof(
                left,
                right[["observation_date", "material", *output_columns]],
                on="observation_date",
                direction="backward",
                allow_exact_matches=False,
            )
        groups.append(left)
    result = pd.concat(groups, ignore_index=True)
    result["has_mcx_history"] = result["mcx_traded_contract_lots_lag_1"].notna().astype(
        "int8"
    )
    return result


def _feature_dictionary() -> dict[str, dict[str, str]]:
    return {
        name: {
            "datatype": "float",
            "unit": (
                "native Yahoo quote units"
                if name.startswith("reference_")
                else "native MCX source units"
            ),
            "source": "YahooFinance" if name.startswith("reference_") else "MCX",
            "formula": "Prior observations only; current target excluded",
            "availability": "As of the reference observation date, without exact-date MCX rows",
            "leakage_risk": "None when generated by this module",
        }
        for name in FEATURE_COLUMNS
    }


def build_reference_price_dataset() -> dict[str, Any]:
    """Build a separate supervised dataset for public-market reference prices."""
    empty = pd.DataFrame()
    if not REFERENCE_CANONICAL_PATH.exists():
        return {
            "dataset": empty,
            "schema": {"status": "not_available", "target": TARGET},
            "leakage_audit": {"status": "not_run", "reason": "No Yahoo canonical snapshot"},
            "path": str(REFERENCE_DATASET_PATH),
            "metadata": {"status": "not_available", "rows": 0},
        }
    reference = pd.read_csv(REFERENCE_CANONICAL_PATH)
    mcx = (
        pd.read_csv(MCX_CANONICAL_PATH)
        if MCX_CANONICAL_PATH.exists()
        else pd.DataFrame()
    )
    reference["observation_date"] = pd.to_datetime(
        reference["observation_date"], errors="coerce"
    ).dt.normalize()
    groups = []
    for ticker, group in reference.groupby("ticker", sort=False):
        enriched = _add_reference_features(group.copy())
        enriched["ticker"] = ticker
        groups.append(enriched)
    dataset = pd.concat(groups, ignore_index=True) if groups else reference
    dataset = _mcx_asof_features(dataset, mcx)
    dataset["observation_day_of_week"] = dataset["observation_date"].dt.dayofweek
    dataset["observation_month"] = dataset["observation_date"].dt.month
    dataset["observation_quarter"] = dataset["observation_date"].dt.quarter
    dataset["reference_history_rows"] = dataset.groupby("ticker").cumcount()
    output_columns = [
        "observation_date",
        "ticker",
        "material",
        "source",
        "source_file",
        "source_hash",
        "source_currency",
        "source_unit",
        "price_field",
        "reference_history_rows",
        TARGET,
        *FEATURE_COLUMNS,
    ]
    for column in output_columns:
        if column not in dataset:
            dataset[column] = pd.NA
    # A row is supervised when its target is observed. Early observations in a
    # series legitimately lack lag features; dropping them would discard real
    # labeled data. Tree models can route missing lag values, while the
    # history flag makes this cold-start condition explicit.
    supervised = dataset.dropna(subset=[TARGET]).copy()
    supervised["observation_date"] = supervised["observation_date"].dt.strftime("%Y-%m-%d")
    supervised = supervised[output_columns].sort_values(
        ["observation_date", "ticker"]
    )
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    supervised.to_csv(REFERENCE_DATASET_PATH, index=False)
    schema = {
        "feature_version": REFERENCE_FEATURE_VERSION,
        "dataset_kind": "public_market_reference_price",
        "target": TARGET,
        "target_definition": "Yahoo Finance verified Close field in native quote currency/unit",
        "feature_names": FEATURE_COLUMNS,
        "categorical_columns": ["ticker", "material", "source_currency", "source_unit"],
        "numeric_columns": [TARGET, *FEATURE_COLUMNS],
        "dataset_path": str(REFERENCE_DATASET_PATH),
        "currency_conversion": False,
        "unit_conversion": False,
        "scrapmonster_included": False,
        "mcx_turnover_as_price": False,
    }
    REFERENCE_FEATURE_SCHEMA_PATH.write_text(
        json.dumps(schema, indent=2), encoding="utf-8"
    )
    REFERENCE_FEATURE_DICTIONARY_PATH.write_text(
        json.dumps(_feature_dictionary(), indent=2), encoding="utf-8"
    )
    audit = leakage_audit(supervised, FEATURE_COLUMNS, TARGET)
    return {
        "dataset": supervised,
        "schema": schema,
        "leakage_audit": audit,
        "path": str(REFERENCE_DATASET_PATH),
        "metadata": {
            "status": "available",
            "source": "YahooFinance",
            "raw_rows": int(len(dataset)),
            "supervised_rows": int(len(supervised)),
            "rows_without_prior_history": int(
                dataset["reference_price_lag_1"].isna().sum()
            ),
            "rows_with_target": int(dataset[TARGET].notna().sum()),
            "rows_excluded_invalid_target": int(dataset[TARGET].isna().sum()),
        },
    }
