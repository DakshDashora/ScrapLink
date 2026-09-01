import pandas as pd
import numpy as np
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from logger import logger

def engineer_features(processed_csv_path, output_dir):
    """
    Engineers time-series features (Lags, Rolling Means, Rolling Volatility, Returns)
    for ML model consumption.
    """
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"[FEATURES SEGMENT] Starting time-series feature engineering on: {processed_csv_path}")

    if not os.path.exists(processed_csv_path):
        logger.error(f"[FEATURES ERROR] Processed CSV file not found at: {processed_csv_path}")
        raise FileNotFoundError(f"[FEATURES ERROR] Processed CSV file not found at: {processed_csv_path}")

    df = pd.read_csv(processed_csv_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(by=['commodity', 'date']).reset_index(drop=True)

    feature_dfs = []
    num_commodities = df['commodity'].nunique()
    logger.debug(f"[FEATURES PROCESS] Engineering features across {num_commodities} commodities...")

    for commodity, group in df.groupby('commodity'):
        g = group.copy()
        prices = g['spot_price_inr_kg']

        # 1. Historical Lag Features (1d, 7d, 14d, 30d)
        g['lag_1'] = prices.shift(1)
        g['lag_7'] = prices.shift(7)
        g['lag_14'] = prices.shift(14)
        g['lag_30'] = prices.shift(30)

        # 2. Rolling Moving Averages (7d & 30d)
        g['rolling_mean_7'] = prices.rolling(window=7, min_periods=1).mean().round(2)
        g['rolling_mean_30'] = prices.rolling(window=30, min_periods=1).mean().round(2)

        # 3. Rolling Volatility Standard Deviation (7d & 30d)
        g['rolling_std_7'] = prices.rolling(window=7, min_periods=1).std().fillna(0).round(2)
        g['rolling_std_30'] = prices.rolling(window=30, min_periods=1).std().fillna(0).round(2)

        # 4. Percentage Return Trends
        g['pct_change_7'] = prices.pct_change(periods=7).fillna(0).round(4)
        g['pct_change_30'] = prices.pct_change(periods=30).fillna(0).round(4)

        feature_dfs.append(g)

    # Combine all commodities
    final_df = pd.concat(feature_dfs, ignore_index=True)
    
    # Drop rows with lag_30 NaN to ensure 100% clean feature matrix for ML training
    final_df_clean = final_df.dropna(subset=['lag_30']).reset_index(drop=True)
    final_df_clean['date'] = final_df_clean['date'].dt.strftime('%Y-%m-%d')

    output_csv = os.path.join(output_dir, "engineered_commodity_features.csv")
    final_df_clean.to_csv(output_csv, index=False)

    logger.info(f"[FEATURES SUCCESS] Feature matrix generated at: {output_csv}")
    logger.info(f" -> Matrix dimensions: {final_df_clean.shape[0]:,} rows × {final_df_clean.shape[1]} columns")
    logger.debug(f" -> Columns created: {list(final_df_clean.columns)}")

    return output_csv

if __name__ == "__main__":
    proc_csv = os.path.join(parent_dir, "data", "processed", "merged_commodity_prices.csv")
    out_dir = os.path.join(parent_dir, "data", "processed")
    engineer_features(proc_csv, out_dir)
