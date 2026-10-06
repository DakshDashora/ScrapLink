"""Prior-only MCX market-context features.

MCX activity is never converted into a price target.  Exact-date rows are
excluded because the target is assumed to be predicted before that day's MCX
close is available.
"""

from __future__ import annotations

import pandas as pd

from .pipeline_config import MCX_ASOF_MAX_DAYS

MCX_FEATURE_COLUMNS = [
    "mcx_lots_lag_1", "mcx_lots_lag_7", "mcx_turnover_lag_1",
    "mcx_turnover_lag_7", "mcx_turnover_return_7", "mcx_turnover_ma_7",
    "mcx_turnover_ma_30", "mcx_activity_volatility_7", "has_mcx_history",
]

MATERIAL_MAP = {
    "Copper": "Copper", "Aluminum": "Aluminium", "Aluminium": "Aluminium",
    "Zinc": "Zinc", "Lead": "Lead", "Steel": "Steel",
}


def build_mcx_features(mcx: pd.DataFrame) -> pd.DataFrame:
    """Aggregate contracts by material/date and calculate prior-only metrics."""
    if mcx.empty:
        return pd.DataFrame(columns=["observation_date", "material", *MCX_FEATURE_COLUMNS])
    required = {"observation_date", "commodity", "traded_contract_lots", "avg_daily_turnover_lakhs"}
    missing = sorted(required - set(mcx.columns))
    if missing:
        raise ValueError(f"MCX features require columns: {missing}")
    data = mcx.copy()
    data["observation_date"] = pd.to_datetime(data["observation_date"], errors="coerce").dt.normalize()
    data["material"] = data["commodity"].map(MATERIAL_MAP)
    data = data.dropna(subset=["observation_date", "material"])
    for column in ["traded_contract_lots", "avg_daily_turnover_lakhs"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.groupby(["observation_date", "material"], as_index=False)[
        ["traded_contract_lots", "avg_daily_turnover_lakhs"]
    ].sum(min_count=1).sort_values(["material", "observation_date"])
    grouped = data.groupby("material", group_keys=False)
    data["mcx_lots_lag_1"] = grouped["traded_contract_lots"].shift(1)
    data["mcx_lots_lag_7"] = grouped["traded_contract_lots"].shift(7)
    data["mcx_turnover_lag_1"] = grouped["avg_daily_turnover_lakhs"].shift(1)
    data["mcx_turnover_lag_7"] = grouped["avg_daily_turnover_lakhs"].shift(7)
    data["mcx_turnover_return_7"] = grouped["avg_daily_turnover_lakhs"].transform(
        lambda values: values.shift(1).pct_change(7, fill_method=None)
    )
    data["mcx_turnover_ma_7"] = grouped["avg_daily_turnover_lakhs"].transform(
        lambda values: values.shift(1).rolling(7, min_periods=1).mean()
    )
    data["mcx_turnover_ma_30"] = grouped["avg_daily_turnover_lakhs"].transform(
        lambda values: values.shift(1).rolling(30, min_periods=1).mean()
    )
    data["mcx_activity_volatility_7"] = grouped["avg_daily_turnover_lakhs"].transform(
        lambda values: values.shift(1).rolling(7, min_periods=2).std()
    )
    data["has_mcx_history"] = data["mcx_lots_lag_1"].notna().astype("int8")
    return data[["observation_date", "material", *MCX_FEATURE_COLUMNS]]


def join_mcx_features(
    scrap: pd.DataFrame, mcx_features: pd.DataFrame
) -> pd.DataFrame:
    """Backward as-of join, independently sorted for each material."""
    output = scrap.copy()
    output["observation_date"] = pd.to_datetime(output["observation_date"], errors="coerce").dt.normalize()
    if mcx_features.empty:
        for column in MCX_FEATURE_COLUMNS:
            output[column] = 0 if column == "has_mcx_history" else pd.NA
        return output
    groups = []
    for material, left in output.groupby("material", dropna=False, sort=False):
        right = mcx_features[mcx_features["material"].eq(material)]
        left = left.sort_values("observation_date").copy()
        if right.empty:
            for column in MCX_FEATURE_COLUMNS:
                left[column] = 0 if column == "has_mcx_history" else pd.NA
        else:
            right = right.drop(columns="material")
            left = pd.merge_asof(
                left,
                right.sort_values("observation_date"),
                on="observation_date",
                direction="backward",
                allow_exact_matches=False,
                tolerance=pd.Timedelta(days=MCX_ASOF_MAX_DAYS),
            )
            left["has_mcx_history"] = left["mcx_lots_lag_1"].notna().astype("int8")
        groups.append(left)
    return pd.concat(groups, ignore_index=True)
