"""Source connectors used to create a raw source snapshot.

This module deliberately does not create synthetic prices or infer prices from
MCX turnover. Network collection is optional; committed/local source files are
the reproducible input for the canonical pipeline.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .pipeline_config import RAW_DIR
from ..logger import logger


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
    )
}


def scrape_live_scrapmonster(output_dir: Path = RAW_DIR) -> Path:
    """Save a raw ScrapMonster snapshot without inventing missing fields."""
    output_dir.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        "https://scrapmonster.com/scrap-prices",
        headers=HEADERS,
        timeout=20,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    rows: list[dict[str, Any]] = []
    for table in soup.find_all("table"):
        for row in table.find_all("tr")[1:]:
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
            if len(cells) < 2:
                continue
            price_text = cells[1].split("(")[0].replace(",", "").strip()
            try:
                price = float(price_text)
            except ValueError:
                logger.warning("Skipping non-numeric ScrapMonster price: %s", price_text)
                continue
            rows.append(
                {
                    "date": dt.date.today().isoformat(),
                    "commodity": cells[0],
                    "category": "Scrap",
                    "source_price": price,
                    "source_currency": "USD",
                    "source_unit": "lb",
                    "source": "ScrapMonster_Live_Web",
                }
            )
    if not rows:
        raise ValueError("ScrapMonster returned no parseable price rows")
    path = output_dir / f"scrapmonster_{dt.date.today():%Y%m%d}.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    logger.info("Saved %s ScrapMonster rows to %s", len(rows), path)
    return path


def discover_mcx_files(input_dir: Path | None = None) -> list[Path]:
    """Return deterministic MCX CSV snapshots available locally."""
    directory = input_dir or (RAW_DIR / "MCX")
    return sorted(directory.glob("*.csv"))


def generate_full_historical_dataset(raw_dir: str | Path = RAW_DIR) -> Path:
    """Build a raw snapshot from available local sources only.

    Unlike the legacy implementation, this function does not generate a
    synthetic market history, fabricate futures or volume values, or convert
    MCX turnover into a price.
    """
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    snapshot = raw_dir / "raw_commodity_prices.csv"
    if not snapshot.exists():
        raise FileNotFoundError(
            f"Raw snapshot not found at {snapshot}. Run a source connector first."
        )
    logger.info("Using existing immutable raw snapshot: %s", snapshot)
    return snapshot

