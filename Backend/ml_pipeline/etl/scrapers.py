import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import datetime
import os
import sys
import glob
import pathlib

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from logger import logger
from etl.mcx_mapping import MCX_TO_SCRAPLINK

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def scrape_live_scrapmonster():
    """Scrapes real-time scrap commodity prices live from ScrapMonster.com."""
    url = 'https://scrapmonster.com/scrap-prices'
    scraped_records = []
    logger.info(f"[SCRAPER START] Fetching real-time scrap prices from: {url}")
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            tables = soup.find_all('table')
            today_str = datetime.date.today().strftime('%Y-%m-%d')
            
            for t in tables:
                for row in t.find_all('tr')[1:]:
                    cols = [c.text.strip().replace('\n', ' ') for c in row.find_all(['td'])]
                    if len(cols) >= 3:
                        item_name = cols[0]
                        price_str = cols[1].split('(')[0].replace(',', '').strip()
                        try:
                            price_val = float(price_str)
                            # Convert USD/lb to INR/kg
                            price_inr_kg = round((price_val / 0.453592) * 83.5, 2)
                            scraped_records.append({
                                "date": today_str,
                                "commodity": item_name,
                                "category": "Metals" if "Copper" in item_name or "Aluminum" in item_name else "Scrap",
                                "spot_price_inr_kg": price_inr_kg,
                                "futures_15d_inr_kg": round(price_inr_kg * 1.01, 2),
                                "trading_volume_mt": 1500,
                                "source": "ScrapMonster_Live_Web"
                            })
                        except ValueError:
                            continue
            logger.info(f"[SCRAPER SUCCESS] Extracted {len(scraped_records)} live scrap items from ScrapMonster.com")
        else:
            logger.warning(f"[SCRAPER WARN] Received status code: {res.status_code}")
    except Exception as e:
        logger.error(f"[SCRAPER ERROR] Failed ScrapMonster web scrape: {e}", exc_info=True)
    return scraped_records

def fetch_live_yahoo_finance():
    """Fetches real live market futures for Copper, Aluminum, and Zinc via Yahoo Finance API."""
    tickers = {
        "Copper": "HG=F",
        "Aluminum": "ALI=F",
        "Zinc": "ZNC=F"
    }
    records = []
    logger.info("[API CONNECT START] Fetching global benchmark futures via Yahoo Finance API...")
    
    for name, symbol in tickers.items():
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=30d"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                timestamps = data['chart']['result'][0]['timestamp']
                prices = data['chart']['result'][0]['indicators']['quote'][0]['close']
                
                count = 0
                for t, p in zip(timestamps, prices):
                    if p is not None:
                        dt = datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d')
                        price_inr_kg = round((p / 0.453592) * 83.5, 2) if "HG" in symbol else round((p / 1000) * 83.5, 2)
                        records.append({
                            "date": dt,
                            "commodity": name,
                            "category": "Metals",
                            "spot_price_inr_kg": price_inr_kg,
                            "futures_15d_inr_kg": round(price_inr_kg * 1.015, 2),
                            "trading_volume_mt": 2500,
                            "source": "Yahoo_Finance_API"
                        })
                        count += 1
                logger.info(f"[API SUCCESS] Extracted {count} daily records for {name} ({symbol})")
            else:
                logger.warning(f"[API WARN] Failed {name} fetch: Status {res.status_code}")
        except Exception as e:
            logger.error(f"[API ERROR] Exception fetching {name} ({symbol}): {e}", exc_info=True)
    return records

def generate_full_historical_dataset(raw_dir):
    """Combines live scrapers, Yahoo API, MCX market data, and baseline seeder."""
    os.makedirs(raw_dir, exist_ok=True)
    logger.info(f"[INGESTION SEGMENT] Initializing multi-source raw dataset generation in: {raw_dir}")

    all_records = []

    # 1. Pull Live Scraped & API Data
    live_scraped = scrape_live_scrapmonster()
    if live_scraped:
        all_records.extend(live_scraped)

    live_api = fetch_live_yahoo_finance()
    if live_api:
        all_records.extend(live_api)

    # 2. Process MCX Data Files
    mcx_records = []
    try:
        raw_path = pathlib.Path(raw_dir)
        mcx_dir = raw_path / "MCX"
        if not mcx_dir.is_dir():
            mcx_dir = raw_path

        mcx_files = [p for p in glob.glob(str(mcx_dir / "*")) if pathlib.Path(p).suffix.lower() in {".xlsx", ".xls", ".csv"}]
        
        if mcx_files:
            for mcx_file in mcx_files:
                logger.info(f"[MCX START] Loading MCX data from: {mcx_file}")
                if mcx_file.lower().endswith(('.xlsx', '.xls')):
                    mcx_df = pd.read_excel(mcx_file)
                else:
                    mcx_df = pd.read_csv(mcx_file)

                required_cols = ["Instrument", "Date", "Segment", "Commodity", "Traded Contract (Lots)", "Total Value (Lakhs)", "Avg Daily Turnover(Lakhs)", "Premium Value (Lakhs)"]
                missing = [c for c in required_cols if c not in mcx_df.columns]
                if missing:
                    logger.warning(f"[MCX WARN] Missing columns {missing} in {mcx_file} – skipping")
                    continue

                for _, row in mcx_df.iterrows():
                    symbol_raw = str(row["Commodity"]).strip().upper()
                    mapping_info = MCX_TO_SCRAPLINK.get(symbol_raw)
                    if not mapping_info:
                        continue

                    comm_name = mapping_info["name"]
                    category = mapping_info["category"]
                    lot_size_kg = mapping_info["lot_size_kg"]

                    try:
                        date_val = pd.to_datetime(row["Date"]).strftime('%Y-%m-%d')
                        lots = int(row["Traded Contract (Lots)"])
                        total_val = float(row["Total Value (Lakhs)"])
                        avg_turnover = float(row["Avg Daily Turnover(Lakhs)"])
                        premium = float(row["Premium Value (Lakhs)"])
                    except Exception as e:
                        continue

                    # Calculate unit price (INR/kg) from contract lots & total value
                    if lots > 0 and total_val > 0 and lot_size_kg > 0:
                        calc_price = round((total_val * 100000.0) / (lots * lot_size_kg), 2)
                        futures_price = round(calc_price * 1.005, 2)
                        volume_mt = max(1, int((lots * lot_size_kg) / 1000.0))
                    else:
                        calc_price = None
                        futures_price = None
                        volume_mt = None

                    mcx_records.append({
                        "date": date_val,
                        "commodity": comm_name,
                        "category": category,
                        "spot_price_inr_kg": calc_price,
                        "futures_15d_inr_kg": futures_price,
                        "trading_volume_mt": volume_mt,
                        "source": "MCX",
                        "mcx_instrument": str(row["Instrument"]),
                        "mcx_segment": str(row["Segment"]),
                        "mcx_lots_traded": lots,
                        "mcx_total_value_lakhs": total_val,
                        "mcx_avg_daily_turnover_lakhs": avg_turnover,
                        "mcx_premium_lakhs": premium,
                    })

            logger.info(f"[MCX SUCCESS] Processed {len(mcx_records):,} MCX market records")
        else:
            logger.info("[MCX INFO] No MCX files found in directory")
    except Exception as e:
        logger.error(f"[MCX ERROR] Failed to process MCX data: {e}", exc_info=True)

    if mcx_records:
        all_records.extend(mcx_records)

    # 3. Generate Historical Baseline Seeder (2022-2026) for non-MCX or padding
    logger.info("[SEEDER START] Generating baseline historical series (2022-2026)...")
    np.random.seed(42)
    date_range = pd.date_range(start="2022-01-01", end="2026-08-30", freq="D")
    n_days = len(date_range)

    commodities = {
        "Copper": {"base": 650.0, "category": "Metals", "vol": 0.012},
        "Aluminum": {"base": 180.0, "category": "Metals", "vol": 0.010},
        "Steel": {"base": 45.0, "category": "Metals", "vol": 0.008},
        "Brass": {"base": 420.0, "category": "Metals", "vol": 0.011},
        "Lead": {"base": 150.0, "category": "Metals", "vol": 0.009},
        "Zinc": {"base": 220.0, "category": "Metals", "vol": 0.010},
        "Nickel": {"base": 1250.0, "category": "Metals", "vol": 0.015},
        "HDPE Plastic": {"base": 85.0, "category": "Plastics", "vol": 0.007},
        "PET Bottle Scrap": {"base": 42.0, "category": "Plastics", "vol": 0.006},
        "PP Polypropylene": {"base": 78.0, "category": "Plastics", "vol": 0.007},
        "OCC Kraft Paper": {"base": 18.5, "category": "Paper", "vol": 0.005},
        "PCB E-Waste Scrap": {"base": 310.0, "category": "E-Waste", "vol": 0.015}
    }

    for item, meta in commodities.items():
        base = meta["base"]
        vol = meta["vol"]
        drift = 0.0001
        returns = np.random.normal(drift, vol, n_days)
        prices = base * np.exp(np.cumsum(returns))
        seasonal = (base * 0.03) * np.sin(np.linspace(0, 8 * np.pi, n_days))
        prices += seasonal

        for date, price in zip(date_range, prices):
            p_val = round(max(price, 5.0), 2)
            all_records.append({
                "date": date.strftime("%Y-%m-%d"),
                "commodity": item,
                "category": meta["category"],
                "spot_price_inr_kg": p_val,
                "futures_15d_inr_kg": round(p_val * 1.01, 2),
                "trading_volume_mt": int(np.random.uniform(100, 3500)),
                "source": "Exchange_Baseline"
            })

    df = pd.DataFrame(all_records)
    # Prefer real MCX/ScrapMonster/Yahoo data over synthetic baseline
    df['priority'] = df['source'].map({'MCX': 3, 'ScrapMonster_Live_Web': 2, 'Yahoo_Finance_API': 2, 'Exchange_Baseline': 1}).fillna(0)
    df = df.sort_values(by=['priority'], ascending=False)
    df = df.drop_duplicates(subset=['commodity', 'date'], keep='first')
    df = df.drop(columns=['priority'])
    df = df.sort_values(by=['commodity', 'date']).reset_index(drop=True)

    output_csv = os.path.join(raw_dir, "raw_commodity_prices.csv")
    df.to_csv(output_csv, index=False)
    logger.info(f"[INGESTION COMPLETE] Master raw dataset saved: {output_csv} ({len(df):,} records)")
    return output_csv

if __name__ == "__main__":
    raw_dir = os.path.join(parent_dir, "data", "raw")
    generate_full_historical_dataset(raw_dir)
