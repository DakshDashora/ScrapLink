import pandas as pd
from sqlalchemy import create_engine
import os
import sys

# Load .env environment variables automatically
try:
    from dotenv import load_dotenv
    # Search for .env in Backend folder or root ScrapLink folder
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
    Cleans raw commodity data, standardizes formats, exports processed dataset,
    and logs records permanently into the PostgreSQL database table 'commodity_prices'.
    """
    os.makedirs(processed_dir, exist_ok=True)
    logger.info(f"[INGEST SEGMENT] Processing raw CSV file: {raw_csv_path}")

    if not os.path.exists(raw_csv_path):
        logger.error(f"[INGEST ERROR] Raw CSV file not found at: {raw_csv_path}")
        raise FileNotFoundError(f"[INGEST ERROR] Raw CSV file not found at: {raw_csv_path}")

    df = pd.read_csv(raw_csv_path)

    # 1. Cleaning & Validation
    initial_len = len(df)
    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
    df = df.dropna(subset=['spot_price_inr_kg'])
    df['spot_price_inr_kg'] = df['spot_price_inr_kg'].round(2)
    df['futures_15d_inr_kg'] = df['futures_15d_inr_kg'].round(2)
    df['trading_volume_mt'] = df['trading_volume_mt'].astype(int)

    # Sort deterministically
    df = df.sort_values(by=['commodity', 'date']).reset_index(drop=True)
    logger.debug(f"[INGEST CLEAN] Cleaned {initial_len} records down to {len(df)} valid records.")

    # 2. Save Processed CSV
    processed_csv = os.path.join(processed_dir, "merged_commodity_prices.csv")
    df.to_csv(processed_csv, index=False)
    logger.info(f"[INGEST SUCCESS] Processed dataset saved to: {processed_csv} ({len(df):,} records)")

    # 3. Clean up any leftover legacy SQLite files
    legacy_sqlite = os.path.join(os.path.dirname(processed_dir), "commodity_prices.db")
    if os.path.exists(legacy_sqlite):
        try:
            os.remove(legacy_sqlite)
            logger.info(f"[CLEANUP] Removed legacy SQLite file: {legacy_sqlite}")
        except Exception as e:
            logger.warning(f"[CLEANUP WARN] Could not remove legacy SQLite file: {e}")

    # 4. Ingest permanently into PostgreSQL Database via DATABASE_URL
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            engine = create_engine(db_url)
            df.to_sql("commodity_prices", engine, if_exists="replace", index=False)
            logger.info(f"[POSTGRESQL DB SUCCESS] Ingested {len(df):,} records into PostgreSQL table 'commodity_prices' via SQLAlchemy")
        except Exception as e:
            logger.warning(f"[POSTGRESQL DB WARNING] PostgreSQL connection skipped ({e}). Processed CSV dataset saved permanently for ML pipeline.")
    else:
        logger.info("[POSTGRESQL DB INFO] DATABASE_URL not set in .env. Skipping cloud DB push and preserving local processed CSV.")

    return processed_csv

if __name__ == "__main__":
    raw_path = os.path.join(parent_dir, "data", "raw", "raw_commodity_prices.csv")
    proc_dir = os.path.join(parent_dir, "data", "processed")
    clean_and_ingest_data(raw_path, proc_dir)
