import os
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from logger import logger, LOG_FILE_PATH
from etl.scrapers import generate_full_historical_dataset
from etl.ingest import clean_and_ingest_data
from etl.eda import perform_eda
from etl.features import engineer_features

def run_full_ml_data_pipeline():
    start_time = time.time()
    logger.info("================================================================================")
    logger.info("  ScrapLink ML Data Pipeline — Sprint 1 Execution Started")
    logger.info("================================================================================")
    logger.info(f"Log File Location: {LOG_FILE_PATH}")

    base_dir = current_dir
    raw_dir = os.path.join(base_dir, "data", "raw")
    processed_dir = os.path.join(base_dir, "data", "processed")
    reports_dir = os.path.join(base_dir, "data", "reports")

    try:
        # Step 1: Scrape & Ingest Raw Prices
        logger.info("[STEP 1/4] Running Automated Market Data Ingestion & Live Web Scraping...")
        raw_csv = generate_full_historical_dataset(raw_dir)

        # Step 2: Clean, Normalize & Log to DB
        logger.info("[STEP 2/4] Cleaning, Normalizing Currency & Ingesting to Database...")
        processed_csv = clean_and_ingest_data(raw_csv, processed_dir)

        # Step 3: Exploratory Data Analysis (EDA)
        logger.info("[STEP 3/4] Conducting Exploratory Data Analysis (EDA)...")
        eda_report = perform_eda(processed_csv, reports_dir)

        # Step 4: Time-Series Feature Engineering
        logger.info("[STEP 4/4] Engineering Time-Series Features (Lags & Rolling Volatility)...")
        feature_csv = engineer_features(processed_csv, processed_dir)

        elapsed = round(time.time() - start_time, 2)
        logger.info("================================================================================")
        logger.info(f"  PIPELINE EXECUTION SUCCESS (Total Elapsed Time: {elapsed} seconds)")
        logger.info("================================================================================")
        logger.info(f"  [RAW DATA]       {raw_csv}")
        logger.info(f"  [PROCESSED DATA] {processed_csv}")
        logger.info(f"  [EDA REPORT]     {eda_report}")
        logger.info(f"  [FEATURE MATRIX] {feature_csv}")
        logger.info(f"  [LOG FILE]       {LOG_FILE_PATH}")
        logger.info("================================================================================\n")

    except Exception as e:
        logger.error(f"[FATAL PIPELINE FAILURE] Pipeline execution crashed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_full_ml_data_pipeline()
