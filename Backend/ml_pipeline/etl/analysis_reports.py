"""Compact analytical summaries for scheduled ML pipeline jobs."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .pipeline_config import MIN_SCRAP_HISTORY_DAYS, MIN_TRAINING_ROWS

TARGET = "price_inr_per_kg"


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return round(result, 4) if np.isfinite(result) else None


def _date_bounds(frame: pd.DataFrame) -> dict[str, str | None]:
    if frame.empty or "observation_date" not in frame:
        return {"first": None, "latest": None}
    dates = pd.to_datetime(frame["observation_date"], errors="coerce").dropna()
    if dates.empty:
        return {"first": None, "latest": None}
    return {
        "first": dates.min().date().isoformat(),
        "latest": dates.max().date().isoformat(),
    }


def _source_summary(frame: pd.DataFrame) -> dict[str, Any]:
    bounds = _date_bounds(frame)
    if frame.empty:
        return {
            "rows": 0,
            "date_range": bounds,
            "observation_dates": 0,
            "missingness_pct": {},
        }
    dates = pd.to_datetime(frame["observation_date"], errors="coerce")
    missingness = {
        str(column): round(float(frame[column].isna().mean() * 100), 2)
        for column in frame.columns
        if frame[column].isna().any()
    }
    return {
        "rows": int(len(frame)),
        "date_range": bounds,
        "observation_dates": int(dates.dt.date.nunique()),
        "missingness_pct": missingness,
    }


def _scrap_analysis(scrap: pd.DataFrame) -> dict[str, Any]:
    if scrap.empty:
        return {
            "price_unit": "INR/kg",
            "materials": {},
            "price_changes_since_previous_observation": [],
            "fx": {"converted_rows": 0, "latest_rate_date": None},
        }
    frame = scrap.copy()
    frame["observation_date"] = pd.to_datetime(
        frame["observation_date"], errors="coerce"
    )
    frame[TARGET] = pd.to_numeric(frame.get(TARGET), errors="coerce")
    frame = frame.dropna(subset=["observation_date", TARGET])
    material_summary: dict[str, Any] = {}
    changes: list[dict[str, Any]] = []
    if not frame.empty:
        frame = frame.sort_values("observation_date")
        for material, group in frame.groupby("material", dropna=False, sort=True):
            prices = group[TARGET].dropna()
            latest = group.iloc[-1]
            material_summary[str(material)] = {
                "rows": int(len(group)),
                "latest_date": latest["observation_date"].date().isoformat(),
                "latest_price_inr_per_kg": _number(latest[TARGET]),
                "price_stats_inr_per_kg": {
                    "min": _number(prices.min()),
                    "median": _number(prices.median()),
                    "mean": _number(prices.mean()),
                    "max": _number(prices.max()),
                },
            }

        for (material, scrap_type), group in frame.groupby(
            ["material", "scrap_type"], dropna=False, sort=False
        ):
            group = group.sort_values("observation_date").tail(2)
            if len(group) < 2:
                continue
            previous, latest = group.iloc[-2], group.iloc[-1]
            previous_price = float(previous[TARGET])
            latest_price = float(latest[TARGET])
            change_pct = (
                ((latest_price - previous_price) / previous_price * 100)
                if previous_price
                else None
            )
            changes.append({
                "material": str(material),
                "scrap_type": str(scrap_type),
                "previous_date": previous["observation_date"].date().isoformat(),
                "latest_date": latest["observation_date"].date().isoformat(),
                "previous_price_inr_per_kg": _number(previous_price),
                "latest_price_inr_per_kg": _number(latest_price),
                "change_pct": _number(change_pct),
            })

    rates = pd.to_numeric(
        scrap.get("fx_rate_to_inr", pd.Series(index=scrap.index, dtype=float)),
        errors="coerce",
    )
    rate_dates = pd.to_datetime(
        scrap.get("fx_rate_date", pd.Series(index=scrap.index, dtype="string")),
        errors="coerce",
    )
    valid_rates = rates.dropna()
    return {
        "price_unit": "INR/kg",
        "materials": material_summary,
        "price_changes_since_previous_observation": changes,
        "fx": {
            "converted_rows": int(valid_rates.gt(1).sum()),
            "average_usd_to_inr_rate": _number(valid_rates.mean()) if not valid_rates.empty else None,
            "latest_rate_date": (
                rate_dates.max().date().isoformat()
                if not rate_dates.dropna().empty
                else None
            ),
        },
    }


def build_analytical_summary(
    sources: dict[str, pd.DataFrame],
    trainable: pd.DataFrame,
    persistence: dict[str, int],
    *,
    job_type: str,
    legacy_rows_converted: int = 0,
) -> dict[str, Any]:
    """Summarize source quality, price movement, and model-data readiness."""
    scrap = sources.get("scrap", pd.DataFrame())
    mcx = sources.get("mcx", pd.DataFrame())
    reference = sources.get("reference", pd.DataFrame())
    source_report = {
        "scrapmonster": _source_summary(scrap),
        "mcx": _source_summary(mcx),
        "reference": _source_summary(reference),
    }
    scrap_report = _scrap_analysis(scrap)
    duplicate_report = {
        "scrapmonster_exact": int(scrap.duplicated().sum()) if not scrap.empty else 0,
        "mcx_exact": int(mcx.duplicated().sum()) if not mcx.empty else 0,
        "reference_exact": (
            int(reference.duplicated().sum()) if not reference.empty else 0
        ),
    }
    eligibility: dict[str, Any] = {}
    if not trainable.empty:
        eligible_rows = int(trainable["is_trainable"].fillna(False).sum())
        collection_dates = int(
            pd.to_datetime(
                trainable["observation_date"], errors="coerce"
            ).dt.date.nunique()
        )
        eligibility = {
            "rows": int(len(trainable)),
            "eligible_rows": eligible_rows,
            "excluded_rows": int((~trainable["is_trainable"].fillna(False)).sum()),
            "collection_dates": collection_dates,
            "minimum_rows": MIN_TRAINING_ROWS,
            "minimum_collection_dates": MIN_SCRAP_HISTORY_DAYS,
            "rows_remaining": max(MIN_TRAINING_ROWS - eligible_rows, 0),
            "collection_dates_remaining": max(
                MIN_SCRAP_HISTORY_DAYS - collection_dates, 0
            ),
            "ready_to_train": (
                eligible_rows >= MIN_TRAINING_ROWS
                and collection_dates >= MIN_SCRAP_HISTORY_DAYS
            ),
            "exclusion_reasons": {
                str(reason): int(count)
                for reason, count in trainable.loc[
                    ~trainable["is_trainable"].fillna(False),
                    "eligibility_reason",
                ].value_counts(dropna=False).items()
            },
            "mcx_feature_coverage_pct": _number(
                trainable["has_mcx_history"].fillna(0).astype(bool).mean() * 100
            ) if "has_mcx_history" in trainable else 0.0,
        }
    else:
        eligibility = {
            "rows": 0,
            "eligible_rows": 0,
            "excluded_rows": 0,
            "collection_dates": 0,
            "minimum_rows": MIN_TRAINING_ROWS,
            "minimum_collection_dates": MIN_SCRAP_HISTORY_DAYS,
            "rows_remaining": MIN_TRAINING_ROWS,
            "collection_dates_remaining": MIN_SCRAP_HISTORY_DAYS,
            "ready_to_train": False,
            "exclusion_reasons": {},
            "mcx_feature_coverage_pct": 0.0,
        }

    insights = []
    if eligibility["eligible_rows"] == 0:
        insights.append("No ScrapMonster rows are currently eligible for supervised training.")
    if not eligibility["ready_to_train"]:
        insights.append(
            "Training gates are not both satisfied; see training_readiness for remaining rows and dates."
        )
    if duplicate_report["scrapmonster_exact"] or duplicate_report["mcx_exact"]:
        insights.append("Exact duplicate source rows remain in the analyzed dataset.")
    if legacy_rows_converted:
        insights.append(
            f"{legacy_rows_converted} legacy ScrapMonster rows were normalized to INR/kg."
        )
    if not scrap.empty and "fx_rate_to_inr" in scrap:
        usd_rows = scrap["source_currency"].astype(str).str.upper().eq("USD")
        missing_fx = int(
            (
                usd_rows
                & pd.to_numeric(scrap["fx_rate_to_inr"], errors="coerce").isna()
            ).sum()
        )
        if missing_fx > 0:
            insights.append(f"{missing_fx} USD ScrapMonster rows have no recorded FX rate.")
    for change in scrap_report["price_changes_since_previous_observation"]:
        if change["change_pct"] is not None and abs(change["change_pct"]) >= 10:
            insights.append(
                f"{change['material']} {change['scrap_type']} price moved "
                f"{change['change_pct']}% between its latest two observations."
            )

    return {
        "report_version": "1.0",
        "job_type": job_type,
        "sources": source_report,
        "scrap_prices": scrap_report,
        "data_quality": {
            "exact_duplicates": duplicate_report,
            "persistence": persistence,
        },
        "training_readiness": eligibility,
        "legacy_scrap_rows_converted": legacy_rows_converted,
        "insights": insights,
    }
