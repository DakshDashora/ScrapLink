"""Structured data-quality and coverage reports for canonical datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def _write(report_dir: Path, name: str, payload: dict[str, Any]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    def serializable(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): serializable(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [serializable(item) for item in value]
        if hasattr(value, "item"):
            return serializable(value.item())
        return value

    (report_dir / name).write_text(
        json.dumps(serializable(payload), indent=2, default=str),
        encoding="utf-8",
    )


def build_quality_reports(
    scrap: pd.DataFrame, mcx: pd.DataFrame, report_dir: Path, reference: pd.DataFrame | None = None
) -> dict[str, str]:
    report_dir.mkdir(parents=True, exist_ok=True)
    reference = reference if reference is not None else pd.DataFrame()
    scrap_dates = pd.to_datetime(scrap["observation_date"], errors="coerce")
    mcx_dates = pd.to_datetime(mcx["observation_date"], errors="coerce")

    quality = {
        "scrap_rows": int(len(scrap)),
        "mcx_rows": int(len(mcx)),
        "scrap_columns": int(len(scrap.columns)),
        "mcx_columns": int(len(mcx.columns)),
        "scrap_missing_values": scrap.isna().sum().to_dict(),
        "mcx_missing_values": mcx.isna().sum().to_dict(),
        "scrap_exact_duplicates": int(scrap.duplicated().sum()),
        "mcx_exact_duplicates": int(mcx.duplicated().sum()),
        "reference_rows": int(len(reference)),
        "reference_exact_duplicates": int(reference.duplicated().sum()),
    }
    source_summary = {
        "scrap_sources": scrap["source"].value_counts(dropna=False).to_dict(),
        "mcx_sources": mcx["source"].value_counts(dropna=False).to_dict(),
        "synthetic_scrap_rows": int(scrap["is_synthetic"].fillna(False).sum()),
        "reference_sources": (
            reference["source"].value_counts(dropna=False).to_dict()
            if "source" in reference
            else {}
        ),
    }
    coverage = {
        "scrap": {
            "first_observation": str(scrap_dates.min()) if not scrap.empty else None,
            "last_observation": str(scrap_dates.max()) if not scrap.empty else None,
            "materials": int(scrap["material"].nunique()),
            "scrap_types": int(scrap["scrap_type"].nunique()),
            "observations_by_material": scrap.groupby("material").size().to_dict(),
        },
        "mcx": {
            "first_observation": str(mcx_dates.min()) if not mcx.empty else None,
            "last_observation": str(mcx_dates.max()) if not mcx.empty else None,
            "commodities": int(mcx["commodity"].nunique()) if not mcx.empty else 0,
            "observations_by_commodity": (
                mcx.groupby("commodity").size().to_dict() if not mcx.empty else {}
            ),
        },
        "reference": {
            "first_observation": (
                str(pd.to_datetime(reference["observation_date"], errors="coerce").min())
                if not reference.empty
                else None
            ),
            "last_observation": (
                str(pd.to_datetime(reference["observation_date"], errors="coerce").max())
                if not reference.empty
                else None
            ),
            "tickers": (
                int(reference["ticker"].nunique()) if "ticker" in reference else 0
            ),
            "observations_by_ticker": (
                reference.groupby("ticker").size().to_dict()
                if "ticker" in reference
                else {}
            ),
        },
    }
    scrap_dates_set = set(scrap_dates.dropna().dt.date)
    mcx_dates_set = set(mcx_dates.dropna().dt.date)
    source_coverage = {
        "scrapmonster": {
            "collection_dates": sorted(str(value) for value in scrap_dates_set),
            "rows_per_collection_date": (
                scrap.groupby(scrap_dates.dt.date).size().to_dict() if not scrap.empty else {}
            ),
            "rows_per_material": scrap.groupby("material").size().to_dict() if not scrap.empty else {},
        },
        "mcx": {"date_count": len(mcx_dates_set)},
        "scrap_mcx_date_overlap": len(scrap_dates_set & mcx_dates_set),
        "scrap_mcx_material_overlap": sorted(
            set(scrap.get("material", pd.Series(dtype="string")).dropna().astype(str))
            & set(mcx.get("commodity", pd.Series(dtype="string")).dropna().astype(str))
        ),
    }
    distributions = {
        "scrap_price_inr_per_kg": (
            scrap["price_inr_per_kg"].describe(
                percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]
            ).to_dict()
            if not scrap.empty
            else {}
        )
    }
    reports = {
        "data_quality.json": quality,
        "source_summary.json": source_summary,
        "coverage.json": coverage,
        "missingness.json": {
            "scrap": quality["scrap_missing_values"],
            "mcx": quality["mcx_missing_values"],
                "reference": (
                    reference.isna().sum().to_dict() if not reference.empty else {}
                ),
        },
        "duplicates.json": {
            "scrap_exact": quality["scrap_exact_duplicates"],
            "mcx_exact": quality["mcx_exact_duplicates"],
            "reference_exact": quality["reference_exact_duplicates"],
        },
        "distribution_summary.json": distributions,
        "source_coverage.json": source_coverage,
    }
    for name, payload in reports.items():
        _write(report_dir, name, payload)
    eligibility = {
        "raw_rows": int(len(scrap)),
        "valid_target_rows": int(
            pd.to_numeric(scrap.get("price_inr_per_kg", pd.Series(dtype=float)), errors="coerce").gt(0).sum()
        ),
        "collection_dates": int(scrap_dates.dropna().dt.date.nunique()),
        "note": "Detailed prior-history eligibility is written by build_trainable_dataset.",
    }
    _write(report_dir, "training_eligibility.json", eligibility)

    markdown = [
        "# ScrapLink canonical data quality report",
        "",
        f"- Scrap observations: **{len(scrap):,}**",
        f"- MCX observations: **{len(mcx):,}**",
        f"- Yahoo reference observations: **{len(reference):,}**",
        f"- Scrap date range: **{coverage['scrap']['first_observation']}** to **{coverage['scrap']['last_observation']}**",
        f"- MCX date range: **{coverage['mcx']['first_observation']}** to **{coverage['mcx']['last_observation']}**",
        f"- Exact duplicate scrap rows: **{quality['scrap_exact_duplicates']}**",
        f"- Exact duplicate MCX rows: **{quality['mcx_exact_duplicates']}**",
        "",
        "Synthetic observations are excluded from the canonical production training dataset.",
        "MCX activity is retained as reference data and is never converted into a scrap target price.",
        "Yahoo reference prices retain their native currency/unit and are not treated as ScrapLink transaction prices.",
    ]
    (report_dir / "EDA.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    return {name: str(report_dir / name) for name in reports} | {
        "training_eligibility.json": str(report_dir / "training_eligibility.json"),
        "EDA.md": str(report_dir / "EDA.md")
    }
