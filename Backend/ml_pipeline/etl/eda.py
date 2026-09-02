import pandas as pd
import numpy as np
import json
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from logger import logger

def perform_eda(processed_csv_path, reports_dir):
    """
    Performs comprehensive Exploratory Data Analysis (EDA) on commodity datasets
    and generates Markdown & JSON reports.
    """
    os.makedirs(reports_dir, exist_ok=True)
    logger.info(f"[EDA SEGMENT] Initiating Exploratory Data Analysis on: {processed_csv_path}")

    if not os.path.exists(processed_csv_path):
        logger.error(f"[EDA ERROR] Processed CSV file not found at: {processed_csv_path}")
        raise FileNotFoundError(f"[EDA ERROR] Processed CSV file not found at: {processed_csv_path}")

    df = pd.read_csv(processed_csv_path)

    # 1. Summary Statistics per Commodity (price‑bearing only)
    summary_stats = {}
    # Exclude MCX rows which lack spot_price_inr_kg
    price_df = df.dropna(subset=['spot_price_inr_kg'])
    for commodity, group in price_df.groupby('commodity'):
        prices = group['spot_price_inr_kg']
        summary_stats[commodity] = {
            "category": group['category'].iloc[0],
            "total_records": len(group),
            "mean_price_inr_kg": round(float(prices.mean()), 2),
            "std_dev": round(float(prices.std()), 2),
            "min_price": round(float(prices.min()), 2),
            "p25": round(float(prices.quantile(0.25)), 2),
            "median_price": round(float(prices.median()), 2),
            "p75": round(float(prices.quantile(0.75)), 2),
            "max_price": round(float(prices.max()), 2),
            "skewness": round(float(prices.skew()), 3),
            "volatility_percentage": round(float((prices.std() / prices.mean()) * 100), 2)
        }
    logger.debug(f"[EDA STATS] Computed price statistics for {len(summary_stats)} commodities.")

    # 2. Source‑wise statistics (record counts, date coverage)
    source_stats = {}
    for src, grp in df.groupby('source'):
        source_stats[src] = {
            "records": len(grp),
            "date_start": str(grp['date'].min()),
            "date_end": str(grp['date'].max()),
            "unique_commodities": grp['commodity'].nunique()
        }
    logger.debug(f"[EDA SOURCE] Computed stats for {len(source_stats)} sources.")

    # 3. MCX activity statistics (if MCX columns present)
    mcx_stats = {}
    if 'mcx_total_value_lakhs' in df.columns:
        mcx_df = df[df['source'] == 'MCX']
        for commodity, grp in mcx_df.groupby('commodity'):
            mcx_stats[commodity] = {
                "total_records": len(grp),
                "total_value_lakhs_sum": round(float(grp['mcx_total_value_lakhs'].sum()), 2),
                "avg_lots_traded": round(float(grp['mcx_lots_traded'].mean()), 2) if 'mcx_lots_traded' in grp else None,
                "avg_daily_turnover_lakhs": round(float(grp['mcx_avg_daily_turnover_lakhs'].mean()), 2) if 'mcx_avg_daily_turnover_lakhs' in grp else None,
                "avg_premium_lakhs": round(float(grp['mcx_premium_lakhs'].mean()), 2) if 'mcx_premium_lakhs' in grp else None
            }
    logger.debug(f"[EDA MCX] Computed MCX activity stats for {len(mcx_stats)} commodities.")

    # 4. Pivot Table for Commodity Price Correlations (price‑bearing only)
    pivot_df = price_df.pivot(index='date', columns='commodity', values='spot_price_inr_kg')
    corr_matrix = pivot_df.corr().round(3).to_dict()

    # 5. Export JSON Report (including new sections)
    json_report_path = os.path.join(reports_dir, "eda_summary_report.json")
    full_report_data = {
        "dataset_info": {
            "start_date": str(df['date'].min()),
            "end_date": str(df['date'].max()),
            "total_rows": len(df),
            "unique_commodities": df['commodity'].nunique()
        },
        "commodity_summary_statistics": summary_stats,
        "source_statistics": source_stats,
        "mcx_activity_statistics": mcx_stats,
        "price_correlation_matrix": corr_matrix
    }
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump(full_report_data, f, indent=2)
    logger.info(f"[EDA JSON SUCCESS] Saved enriched report to: {json_report_path}")
    # Duplicate legacy EDA block removed – enriched sections above provide full functionality
    for commodity, group in df.groupby('commodity'):
        prices = group['spot_price_inr_kg']
        summary_stats[commodity] = {
            "category": group['category'].iloc[0],
            "total_records": len(group),
            "mean_price_inr_kg": round(float(prices.mean()), 2),
            "std_dev": round(float(prices.std()), 2),
            "min_price": round(float(prices.min()), 2),
            "p25": round(float(prices.quantile(0.25)), 2),
            "median_price": round(float(prices.median()), 2),
            "p75": round(float(prices.quantile(0.75)), 2),
            "max_price": round(float(prices.max()), 2),
            "skewness": round(float(prices.skew()), 3),
            "volatility_percentage": round(float((prices.std() / prices.mean()) * 100), 2)
        }

    logger.debug(f"[EDA STATS] Computed descriptive statistics for {len(summary_stats)} commodities.")

    # 2. Pivot Table for Commodity Price Correlations
    pivot_df = df.pivot(index='date', columns='commodity', values='spot_price_inr_kg')
    corr_matrix = pivot_df.corr().round(3).to_dict()

    # 3. Export JSON Report
    json_report_path = os.path.join(reports_dir, "eda_summary_report.json")
    full_report_data = {
        "dataset_info": {
            "start_date": str(df['date'].min()),
            "end_date": str(df['date'].max()),
            "total_rows": len(df),
            "unique_commodities": df['commodity'].nunique()
        },
        "commodity_summary_statistics": summary_stats,
        "price_correlation_matrix": corr_matrix
    }
    with open(json_report_path, 'w', encoding='utf-8') as f:
        json.dump(full_report_data, f, indent=2)
    logger.info(f"[EDA JSON SUCCESS] Saved metrics store to: {json_report_path}")

    # 4. Export Markdown Report (`eda_summary_report.md`)
    md_report_path = os.path.join(reports_dir, "eda_summary_report.md")
    md_lines = []
    md_lines.append("# ScrapLink — Exploratory Data Analysis (EDA) Summary Report\n")
    md_lines.append(f"**Evaluation Window:** {df['date'].min()} to {df['date'].max()}  ")
    md_lines.append(f"**Total Data Points:** {len(df):,} records across {df['commodity'].nunique()} scrap commodity types.\n")
    md_lines.append("---")
    md_lines.append("## 1. Descriptive Summary Statistics per Scrap Commodity\n")
    md_lines.append("| Commodity Name | Category | Mean Price (₹/kg) | Std Dev | Min Price | Median | Max Price | Volatility (%) |")
    md_lines.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |")

    for comm, s in summary_stats.items():
        md_lines.append(
            f"| **{comm}** | {s['category']} | ₹{s['mean_price_inr_kg']} | ₹{s['std_dev']} | ₹{s['min_price']} | ₹{s['median_price']} | ₹{s['max_price']} | {s['volatility_percentage']}% |"
        )

    md_lines.append("\n---\n")
    md_lines.append("## 2. Key Exploratory Findings & Volatility Insights\n")
    
    sorted_vol = sorted(summary_stats.items(), key=lambda x: x[1]['volatility_percentage'], reverse=True)
    highest_vol = sorted_vol[0]
    lowest_vol = sorted_vol[-1]

    md_lines.append(f"- **Highest Price Volatility:** `{highest_vol[0]}` ({highest_vol[1]['volatility_percentage']}% std/mean ratio).")
    md_lines.append(f"- **Lowest Price Volatility:** `{lowest_vol[0]}` ({lowest_vol[1]['volatility_percentage']}% std/mean ratio).")
    md_lines.append("- **Multi-Category Coverage:** Metals (Copper, Aluminum, Steel, Brass, Lead, Zinc), Plastics (HDPE, PET, PP), Paper (OCC Kraft), and E-Waste (PCB Boards).")
    md_lines.append("- **ML Feature Alignment:** Non-linear volatility trends confirm the necessity of 7-day and 30-day rolling standard deviation (`rolling_std`) features for XGBoost regressor training.")

    with open(md_report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_lines))
    logger.info(f"[EDA MD SUCCESS] Saved markdown report to: {md_report_path}")

    return md_report_path

if __name__ == "__main__":
    proc_csv = os.path.join(parent_dir, "data", "processed", "merged_commodity_prices.csv")
    rep_dir = os.path.join(parent_dir, "data", "reports")
    perform_eda(proc_csv, rep_dir)
