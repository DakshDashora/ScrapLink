"""Idempotent daily source collection entry point (no deployment code)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ..etl.canonical import build_canonical_datasets
from ..etl.scrapers import discover_mcx_files, scrape_live_scrapmonster
from ..etl.yahoo import collect_daily_yahoo_history
from ..etl.pipeline_config import YAHOO_TICKERS
from ..etl.validation import validate_canonical_data


def run_collection(
    *,
    collect_scrapmonster: bool = True,
    collect_yahoo: bool = True,
) -> dict[str, Any]:
    snapshot = None
    yahoo_snapshot = None
    if collect_scrapmonster:
        snapshot = scrape_live_scrapmonster()
    if collect_yahoo and YAHOO_TICKERS:
        yahoo_snapshot = collect_daily_yahoo_history()
    canonical = build_canonical_datasets()
    validation = validate_canonical_data(canonical["scrap"], canonical["mcx"])
    return {
        "status": "passed",
        "snapshot": str(snapshot) if snapshot else None,
        "yahoo_snapshot": str(yahoo_snapshot) if yahoo_snapshot else None,
        "mcx_files_discovered": len(discover_mcx_files()),
        "canonical": canonical["manifest"],
        "validation": validation,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-scrapmonster", action="store_true")
    parser.add_argument("--skip-yahoo", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(run_collection(
            collect_scrapmonster=not args.skip_scrapmonster,
            collect_yahoo=not args.skip_yahoo,
        ), indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
