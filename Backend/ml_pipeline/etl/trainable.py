"""Leakage-safe ScrapMonster supervised dataset construction."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from .mcx_features import MCX_FEATURE_COLUMNS, build_mcx_features, join_mcx_features
from .pipeline_config import (
    FEATURE_DICTIONARY_PATH, FEATURE_SCHEMA_PATH, FEATURES_DIR, FEATURE_VERSION,
    MCX_CANONICAL_PATH, SCRAP_CANONICAL_PATH, TRAINABLE_DATASET_PATH,
    MIN_SCRAP_HISTORY_DAYS,
)
from .validation import leakage_audit

TARGET = "price_inr_per_kg"
FEATURE_COLUMNS = [
    "day_of_week", "month", "quarter",
    "scrap_price_lag_1", "scrap_price_lag_7", "scrap_price_lag_14",
    "scrap_price_lag_30", "scrap_price_return_1", "scrap_price_return_7",
    "scrap_price_return_30", "scrap_price_ma_7", "scrap_price_ma_30",
    "scrap_price_volatility_7", "scrap_price_volatility_30",
    *[column for column in MCX_FEATURE_COLUMNS if column != "has_mcx_history"],
    "has_scrap_history", "has_mcx_history",
]


def _add_scrap_features(group: pd.DataFrame) -> pd.DataFrame:
    group = group.sort_values("observation_date").copy()
    prices = pd.to_numeric(group[TARGET], errors="coerce")
    history = prices.shift(1)
    group["scrap_price_lag_1"] = history
    group["scrap_price_lag_7"] = prices.shift(7)
    group["scrap_price_lag_14"] = prices.shift(14)
    group["scrap_price_lag_30"] = prices.shift(30)
    group["scrap_price_return_1"] = history.pct_change(1, fill_method=None)
    group["scrap_price_return_7"] = history.pct_change(7, fill_method=None)
    group["scrap_price_return_30"] = history.pct_change(30, fill_method=None)
    group["scrap_price_ma_7"] = history.rolling(7, min_periods=7).mean()
    group["scrap_price_ma_30"] = history.rolling(30, min_periods=30).mean()
    prior_returns = history.pct_change(fill_method=None)
    group["scrap_price_volatility_7"] = prior_returns.rolling(7, min_periods=7).std()
    group["scrap_price_volatility_30"] = prior_returns.rolling(30, min_periods=30).std()
    group["scrap_history_rows"] = range(len(group))
    group["has_scrap_history"] = group["scrap_price_lag_1"].notna().astype("int8")
    return group


def _eligibility_report(dataset: pd.DataFrame, raw_rows: int) -> dict[str, Any]:
    valid_target = dataset[TARGET].notna() & dataset[TARGET].gt(0)
    valid_identity = dataset["observation_date"].notna() & dataset["material"].notna()
    prior = dataset["scrap_history_rows"].fillna(0)
    eligible = valid_target & valid_identity & prior.ge(1)
    reasons = {
        "invalid_target": int((~valid_target).sum()),
        "invalid_material_or_date": int((valid_target & ~valid_identity).sum()),
        "no_prior_scrap_observation": int((valid_target & valid_identity & prior.lt(1)).sum()),
    }
    dates = pd.to_datetime(dataset["observation_date"], errors="coerce")
    return {
        "raw_rows": int(raw_rows),
        "valid_target_rows": int(valid_target.sum()),
        "rows_with_one_prior_observation": int(prior.ge(1).sum()),
        "rows_with_seven_prior_observations": int(prior.ge(7).sum()),
        "rows_with_thirty_prior_observations": int(prior.ge(30).sum()),
        "eligible_rows": int(eligible.sum()),
        "excluded_rows": int((~eligible).sum()),
        "exclusion_reasons": reasons,
        "collection_dates": int(dates.dropna().dt.date.nunique()),
        "minimum_history_days_configured": MIN_SCRAP_HISTORY_DAYS,
        "status": "eligible_rows_available" if eligible.any() else "insufficient_history",
    }


def _feature_dictionary() -> dict[str, dict[str, str]]:
    return {
        name: {
            "datatype": "float",
            "source": (
                "ScrapMonster"
                if name.startswith("scrap_") or name in {"day_of_week", "month", "quarter", "has_scrap_history"}
                else "MCX"
            ),
            "formula": "Prior observations only; current target excluded",
            "availability": "Known before the prediction target",
        }
        for name in FEATURE_COLUMNS
    }


def build_trainable_dataset(
    scrap: pd.DataFrame | None = None,
    mcx: pd.DataFrame | None = None,
    *,
    persist_artifacts: bool = True,
) -> dict[str, Any]:
    if scrap is None:
        if not SCRAP_CANONICAL_PATH.exists():
            raise FileNotFoundError(
                f"Canonical ScrapMonster dataset not found: {SCRAP_CANONICAL_PATH}"
            )
        scrap = pd.read_csv(SCRAP_CANONICAL_PATH)
    if mcx is None:
        mcx = pd.read_csv(MCX_CANONICAL_PATH) if MCX_CANONICAL_PATH.exists() else pd.DataFrame()
    required = {"observation_date", "material", "scrap_type", TARGET}
    missing = sorted(required - set(scrap.columns))
    if missing:
        raise ValueError(f"Scrap canonical dataset missing columns: {missing}")
    scrap["observation_date"] = pd.to_datetime(scrap["observation_date"], errors="coerce").dt.normalize()
    scrap[TARGET] = pd.to_numeric(scrap[TARGET], errors="coerce")
    groups = [
        _add_scrap_features(group)
        for _, group in scrap.groupby(["material", "scrap_type"], sort=False, dropna=False)
    ]
    dataset = pd.concat(groups, ignore_index=True) if groups else scrap.copy()
    dataset = join_mcx_features(dataset, build_mcx_features(mcx))
    dataset["day_of_week"] = dataset["observation_date"].dt.dayofweek
    dataset["month"] = dataset["observation_date"].dt.month
    dataset["quarter"] = dataset["observation_date"].dt.quarter
    dataset["is_trainable"] = (
        dataset[TARGET].notna() & dataset[TARGET].gt(0)
        & dataset["material"].notna() & dataset["observation_date"].notna()
        & dataset["scrap_history_rows"].ge(1)
    )
    dataset["eligibility_reason"] = "eligible"
    dataset.loc[~dataset["scrap_history_rows"].ge(1), "eligibility_reason"] = "no_prior_scrap_observation"
    dataset.loc[dataset[TARGET].isna() | dataset[TARGET].le(0), "eligibility_reason"] = "invalid_target"
    output_columns = [
        "observation_date", "material", "scrap_type", "source", "source_file",
        "source_hash", "is_synthetic", TARGET, "scrap_history_rows",
        "is_trainable", "eligibility_reason", *FEATURE_COLUMNS,
    ]
    for column in output_columns:
        if column not in dataset:
            dataset[column] = pd.NA
    dataset = dataset[output_columns].sort_values(
        ["observation_date", "material", "scrap_type"], na_position="last"
    )
    report = _eligibility_report(dataset, len(scrap))
    schema = {
        "feature_version": FEATURE_VERSION, "target": TARGET,
        "feature_names": FEATURE_COLUMNS,
        "categorical_columns": ["material", "scrap_type"],
        "numeric_columns": [TARGET, *FEATURE_COLUMNS],
        "dataset_path": str(TRAINABLE_DATASET_PATH),
        "trainability_policy": "valid observed ScrapMonster target and at least one prior observation",
        "quantiles": [0.1, 0.5, 0.9],
    }
    if persist_artifacts:
        FEATURES_DIR.mkdir(parents=True, exist_ok=True)
        dataset.assign(
            observation_date=dataset["observation_date"].dt.strftime("%Y-%m-%d")
        ).to_csv(TRAINABLE_DATASET_PATH, index=False)
        FEATURE_SCHEMA_PATH.write_text(json.dumps(schema, indent=2), encoding="utf-8")
        FEATURE_DICTIONARY_PATH.write_text(
            json.dumps(_feature_dictionary(), indent=2), encoding="utf-8"
        )
    audit = leakage_audit(dataset, FEATURE_COLUMNS, TARGET)
    return {"dataset": dataset, "schema": schema, "leakage_audit": audit,
            "eligibility": report, "path": str(TRAINABLE_DATASET_PATH)}
