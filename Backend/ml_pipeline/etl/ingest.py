import pandas as pd
from sqlalchemy import create_engine
import os
import sys

try:
    from dotenv import load_dotenv
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    root_dir = os.path.dirname(backend_dir)
    
    load_dotenv(os.path.join(backend_dir, ".env"))
    load_dotenv(os.path.join(root_dir, ".env"))
except ImportError:
    pass

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from logger import logger

def clean_and_ingest_data(raw_csv_path, processed_dir):
    """
    Cleans raw commodity data, fills missing values per commodity group,
    exports processed dataset, and ingests records into PostgreSQL.
    """
    os.makedirs(processed_dir, exist_ok=True)
    logger.info(f"[INGEST SEGMENT] Processing raw CSV file: {raw_csv_path}")

    if not os.path.exists(raw_csv_path):
        logger.error(f"[INGEST ERROR] Raw CSV file not found at: {raw_csv_path}")
        raise FileNotFoundError(f"[INGEST ERROR] Raw CSV file not found at: {raw_csv_path}")

    df = pd.read_csv(raw_csv_path)
    initial_len = len(df)

    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    numeric_cols = ['spot_price_inr_kg', 'futures_15d_inr_kg', 'trading_volume_mt']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Sort deterministically by commodity and date
    df = df.sort_values(by=['commodity', 'date']).reset_index(drop=True)

    # Per-commodity interpolation & forward/backward fill for price fields
    filled_dfs = []
    for comm, group in df.groupby('commodity'):
        g = group.copy()
        g['spot_price_inr_kg'] = g['spot_price_inr_kg'].ffill().bfill().round(2)
        g['futures_15d_inr_kg'] = g['futures_15d_inr_kg'].fillna(g['spot_price_inr_kg'] * 1.01).round(2)
        g['trading_volume_mt'] = g['trading_volume_mt'].fillna(1500).astype(int)
        filled_dfs.append(g)

    df_clean = pd.concat(filled_dfs, ignore_index=True)
    df_clean = df_clean.dropna(subset=['spot_price_inr_kg']).reset_index(drop=True)

    logger.info(f"[INGEST CLEAN] Retained {len(df_clean):,} of {initial_len:,} raw records after cleaning & interpolation.")

    # Save Processed CSV
    processed_csv = os.path.join(processed_dir, "merged_commodity_prices.csv")
    df_clean.to_csv(processed_csv, index=False)
    logger.info(f"[INGEST SUCCESS] Processed dataset saved to: {processed_csv} ({len(df_clean):,} records)")

    # Cleanup legacy SQLite file if present
    legacy_sqlite = os.path.join(os.path.dirname(processed_dir), "commodity_prices.db")
    if os.path.exists(legacy_sqlite):
        try:
            os.remove(legacy_sqlite)
            logger.info(f"[CLEANUP] Removed legacy SQLite file: {legacy_sqlite}")
        except Exception as e:
            logger.warning(f"[CLEANUP WARN] Could not remove legacy SQLite file: {e}")

    # Ingest into PostgreSQL if DATABASE_URL is set
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            engine = create_engine(db_url)
            df_clean.to_sql("commodity_prices", engine, if_exists="replace", index=False)
            logger.info(f"[POSTGRESQL DB SUCCESS] Ingested {len(df_clean):,} records into PostgreSQL table 'commodity_prices'")
        except Exception as e:
            logger.warning(f"[POSTGRESQL DB WARNING] PostgreSQL push skipped ({e}). Processed CSV preserved locally.")
    else:
        logger.info("[POSTGRESQL DB INFO] DATABASE_URL not set in .env. Local processed CSV saved.")

    return processed_csv

if __name__ == "__main__":
    raw_path = os.path.join(parent_dir, "data", "raw", "raw_commodity_prices.csv")
    proc_dir = os.path.join(parent_dir, "data", "processed")
    clean_and_ingest_data(raw_path, proc_dir)
