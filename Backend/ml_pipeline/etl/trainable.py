"""Leakage-safe feature generation for the future range-model training contract."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from .pipeline_config import (
    FEATURE_DICTIONARY_PATH,
    FEATURE_SCHEMA_PATH,
    FEATURES_DIR,
    FEATURE_VERSION,
    MCX_CANONICAL_PATH,
    SCRAP_CANONICAL_PATH,
    TRAINABLE_DATASET_PATH,
)
from .validation import leakage_audit


TARGET = "price_inr_per_kg"
FEATURE_COLUMNS = [
    "observation_day_of_week",
    "observation_month",
    "observation_quarter",
    "scrap_price_lag_1",
    "scrap_price_lag_7",
    "scrap_price_lag_14",
    "scrap_price_lag_30",
    "scrap_return_1",
    "scrap_return_7",
    "scrap_return_30",
    "scrap_ma_7",
    "scrap_ma_30",
    "scrap_volatility_7",
    "scrap_volatility_30",
    "mcx_activity_lag_1",
    "mcx_activity_lag_7",
    "mcx_activity_ma_7",
    "has_scrap_history",
    "has_mcx_history",
]


def _material_to_mcx(material: str) -> str | None:
    return {
        "Copper": "Copper",
        "Aluminium": "Aluminum",
        "Zinc": "Zinc",
        "Lead": "Lead",
        "Steel": "Steel",
    }.get(material)


def _add_scrap_features(group: pd.DataFrame) -> pd.DataFrame:
    group = group.sort_values("observation_date").copy()
    prices = group[TARGET]
    history = prices.shift(1)
    group["scrap_price_lag_1"] = history
    group["scrap_price_lag_7"] = prices.shift(7)
    group["scrap_price_lag_14"] = prices.shift(14)
    group["scrap_price_lag_30"] = prices.shift(30)
    group["scrap_return_1"] = history.pct_change(1, fill_method=None)
    group["scrap_return_7"] = history.pct_change(7, fill_method=None)
    group["scrap_return_30"] = history.pct_change(30, fill_method=None)
    group["scrap_ma_7"] = history.rolling(7, min_periods=7).mean()
    group["scrap_ma_30"] = history.rolling(30, min_periods=30).mean()
    prior_returns = history.pct_change(fill_method=None)
    group["scrap_volatility_7"] = prior_returns.rolling(7, min_periods=7).std()
    group["scrap_volatility_30"] = prior_returns.rolling(30, min_periods=30).std()
    group["has_scrap_history"] = group["scrap_price_lag_1"].notna().astype("int8")
    return group


def _add_mcx_features(scrap: pd.DataFrame, mcx: pd.DataFrame) -> pd.DataFrame:
    if mcx.empty:
        for column in [
            "mcx_activity_lag_1",
            "mcx_activity_lag_7",
            "mcx_activity_ma_7",
        ]:
            scrap[column] = pd.NA
        scrap["has_mcx_history"] = 0
        return scrap

    scrap = scrap.copy()
    scrap["observation_date"] = pd.to_datetime(scrap["observation_date"]).dt.normalize()
    scrap["material"] = scrap["material"].astype("string")
    mcx = mcx.copy()
    mcx["observation_date"] = pd.to_datetime(mcx["observation_date"]).dt.normalize()
    mcx["material"] = mcx["commodity"].map(
        {"Copper": "Copper", "Aluminum": "Aluminium", "Zinc": "Zinc", "Lead": "Lead", "Steel": "Steel"}
    ).astype("string")
    mcx = mcx.dropna(subset=["material"])
    mcx["activity_value"] = mcx[
        ["traded_contract_lots", "avg_daily_turnover_lakhs"]
    ].sum(axis=1, min_count=1)
    mcx = (
        mcx.groupby(["observation_date", "material"], as_index=False)["activity_value"]
        .sum()
        .sort_values(["material", "observation_date"])
    )
    mcx["mcx_activity_lag_1"] = mcx.groupby("material")["activity_value"].shift(1)
    mcx["mcx_activity_lag_7"] = mcx.groupby("material")["activity_value"].shift(7)
    mcx["mcx_activity_ma_7"] = mcx.groupby("material")["activity_value"].transform(
        lambda values: values.shift(1).rolling(7, min_periods=7).mean()
    )
    mcx = mcx[
        [
            "observation_date",
            "material",
            "mcx_activity_lag_1",
            "mcx_activity_lag_7",
            "mcx_activity_ma_7",
        ]
    ]
    # Merge each material independently. This avoids pandas' strict global
    # ordering requirements for merge_asof and keeps source dtypes explicit.
    merged_groups = []
    for material, scrap_group in scrap.groupby("material", dropna=False, sort=False):
        left = scrap_group.sort_values("observation_date").copy()
        right = mcx[mcx["material"].eq(material)].sort_values("observation_date").copy()
        if right.empty:
            left["mcx_activity_lag_1"] = pd.NA
            left["mcx_activity_lag_7"] = pd.NA
            left["mcx_activity_ma_7"] = pd.NA
        else:
            left = pd.merge_asof(
                left,
                right,
                on="observation_date",
                direction="backward",
                allow_exact_matches=False,
            )
        merged_groups.append(left)
    merged = pd.concat(merged_groups, ignore_index=True)
    merged["has_mcx_history"] = merged["mcx_activity_lag_1"].notna().astype("int8")
    return merged


def _feature_dictionary() -> dict[str, dict[str, Any]]:
    return {
        name: {
            "datatype": "float",
            "unit": "INR/kg" if name.startswith("scrap_") else "source units",
            "source": "ScrapMonster" if name.startswith("scrap_") else "MCX",
            "formula": "Prior observations only; current target excluded",
            "availability": "Available at prediction time from data on or before observation date",
            "leakage_risk": "None when generated by this module",
        }
        for name in FEATURE_COLUMNS
    }


def build_trainable_dataset() -> dict[str, Any]:
    scrap = pd.read_csv(SCRAP_CANONICAL_PATH)
    mcx = pd.read_csv(MCX_CANONICAL_PATH)
    scrap["observation_date"] = pd.to_datetime(scrap["observation_date"]).dt.normalize()
    scrap = scrap.sort_values(["material", "scrap_type", "observation_date"])
    feature_groups = []
    for (material, scrap_type), group in scrap.groupby(
        ["material", "scrap_type"], sort=False
    ):
        enriched = _add_scrap_features(group.copy())
        enriched["material"] = material
        enriched["scrap_type"] = scrap_type
        feature_groups.append(enriched)
    scrap = (
        pd.concat(feature_groups, ignore_index=True)
        if feature_groups
        else scrap.copy()
    )
    scrap = _add_mcx_features(scrap, mcx)
    scrap["material_mcx_reference"] = scrap["material"].map(_material_to_mcx)
    scrap["observation_day_of_week"] = scrap["observation_date"].dt.dayofweek
    scrap["observation_month"] = scrap["observation_date"].dt.month
    scrap["observation_quarter"] = scrap["observation_date"].dt.quarter

    output_columns = [
        "observation_date",
        "material",
        "scrap_type",
        "source",
        "source_file",
        "source_hash",
        "material_mcx_reference",
        TARGET,
        "is_synthetic",
        *FEATURE_COLUMNS,
    ]
    for column in output_columns:
        if column not in scrap:
            scrap[column] = pd.NA

    # MCX reference features are optional. Scrap history is mandatory; rows
    # without enough prior target observations remain in the diagnostic output
    # but are not eligible for supervised training.
    trainable = scrap.dropna(subset=[TARGET]).copy()
    trainable["observation_date"] = trainable["observation_date"].dt.strftime("%Y-%m-%d")
    trainable = trainable[output_columns].sort_values(
        ["observation_date", "material", "scrap_type"]
    )
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)
    trainable.to_csv(TRAINABLE_DATASET_PATH, index=False)

    schema = {
        "feature_version": FEATURE_VERSION,
        "target": TARGET,
        "feature_names": FEATURE_COLUMNS,
        "categorical_columns": ["material", "scrap_type", "material_mcx_reference"],
        "numeric_columns": [TARGET, *FEATURE_COLUMNS],
        "dataset_path": str(TRAINABLE_DATASET_PATH),
        "prediction_horizon": "Not finalized; features describe prior observations only",
    }
    FEATURE_SCHEMA_PATH.write_text(json.dumps(schema, indent=2), encoding="utf-8")
    FEATURE_DICTIONARY_PATH.write_text(
        json.dumps(_feature_dictionary(), indent=2), encoding="utf-8"
    )
    audit = leakage_audit(trainable, FEATURE_COLUMNS, TARGET)
    return {
        "dataset": trainable,
        "schema": schema,
        "leakage_audit": audit,
        "path": str(TRAINABLE_DATASET_PATH),
    }
