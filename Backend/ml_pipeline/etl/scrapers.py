"""Source connectors for immutable ScrapMonster and MCX inputs."""

from __future__ import annotations

import datetime as dt
import hashlib
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

from .pipeline_config import MCX_DIR, RAW_DIR, SCRAPMONSTER_DIR
from .source_registry import register_source
from ..core.logger import logger

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
    )
}
SCRAPMONSTER_URL = "https://scrapmonster.com/scrap-prices"
PARSER_VERSION = "scrapmonster-html-v2"


def _hash_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _next_immutable_path(directory: Path, stem: str, suffix: str) -> Path:
    candidate = directory / f"{stem}{suffix}"
    if not candidate.exists():
        return candidate
    index = 2
    while True:
        candidate = directory / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def scrape_live_scrapmonster(
    output_dir: Path = SCRAPMONSTER_DIR,
    *,
    session: requests.Session | None = None,
    url: str = SCRAPMONSTER_URL,
) -> Path:
    """Download and persist a dated, write-once ScrapMonster snapshot."""
    output_dir.mkdir(parents=True, exist_ok=True)
    client = session or requests.Session()
    response = client.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    body = response.content
    source_hash = _hash_bytes(body)
    soup = BeautifulSoup(response.text, "html.parser")
    rows: list[dict[str, Any]] = []
    rejected = 0
    read = 0
    for table in soup.find_all("table"):
        for row in table.find_all("tr")[1:]:
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
            if len(cells) < 2:
                continue
            read += 1
            price_text = cells[1].split("(")[0].replace(",", "").strip()
            try:
                price = float(price_text)
            except ValueError:
                rejected += 1
                continue
            rows.append({
                "date": dt.date.today().isoformat(),
                "commodity": cells[0],
                "category": "Scrap",
                "source_price": price,
                "source_currency": "USD",
                "source_unit": "lb",
                "source": "ScrapMonster_Live_Web",
                "collection_timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
                "source_url": url,
                "source_hash": source_hash,
                "parser_version": PARSER_VERSION,
            })
    if not rows:
        raise ValueError("ScrapMonster returned no parseable observed price rows")
    for existing in sorted(output_dir.glob("scrapmonster_*.csv")):
        try:
            existing_data = pd.read_csv(existing, nrows=1)
        except (OSError, pd.errors.ParserError):
            continue
        if existing_data.get("source_hash", pd.Series(dtype="string")).astype(str).eq(source_hash).any():
            logger.info("ScrapMonster response already stored at %s", existing)
            return existing
    path = _next_immutable_path(
        output_dir, f"scrapmonster_{dt.date.today():%Y%m%d}", ".csv"
    )
    pd.DataFrame(rows).to_csv(path, index=False)
    register_source(
        "ScrapMonster", path, source_hash,
        observation_start=dt.date.today().isoformat(),
        observation_end=dt.date.today().isoformat(),
        row_count=read, accepted_rows=len(rows), rejected_rows=rejected,
    )
    logger.info(
        "ScrapMonster snapshot %s: read=%s accepted=%s rejected=%s",
        path, read, len(rows), rejected,
    )
    return path


def discover_scrapmonster_files(input_dir: Path | None = None) -> list[Path]:
    return sorted((input_dir or SCRAPMONSTER_DIR).glob("*.csv"))


def discover_mcx_files(input_dir: Path | None = None) -> list[Path]:
    return sorted((input_dir or MCX_DIR).glob("*.csv"))


def generate_full_historical_dataset(raw_dir: str | Path = RAW_DIR) -> Path:
    """Compatibility entry point; returns an existing legacy input only."""
    snapshot = Path(raw_dir) / "raw_commodity_prices.csv"
    if not snapshot.exists():
        raise FileNotFoundError(f"Raw snapshot not found at {snapshot}")
    return snapshot
