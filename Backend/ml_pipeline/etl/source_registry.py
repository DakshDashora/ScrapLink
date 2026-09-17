"""Small append-only source manifest used for ingestion traceability."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .pipeline_config import SOURCE_REGISTRY_PATH

REGISTRY_COLUMNS = [
    "source_name", "source_file", "source_hash", "collection_time",
    "observation_start", "observation_end", "row_count", "accepted_rows",
    "rejected_rows", "status", "error_message",
]


def register_source(
    source_name: str,
    source_file: str | Path,
    source_hash: str,
    *,
    observation_start: Any = None,
    observation_end: Any = None,
    row_count: int = 0,
    accepted_rows: int = 0,
    rejected_rows: int = 0,
    status: str = "accepted",
    error_message: str = "",
    registry_path: str | Path = SOURCE_REGISTRY_PATH,
) -> dict[str, Any]:
    """Register a source once, keyed by its content hash."""
    path = Path(registry_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=REGISTRY_COLUMNS)
    if "source_hash" in existing and existing["source_hash"].astype(str).eq(source_hash).any():
        return {"duplicate": True, "source_hash": source_hash, "status": "duplicate"}
    row = {
        "source_name": source_name,
        "source_file": str(source_file),
        "source_hash": source_hash,
        "collection_time": datetime.now(timezone.utc).isoformat(),
        "observation_start": observation_start,
        "observation_end": observation_end,
        "row_count": int(row_count),
        "accepted_rows": int(accepted_rows),
        "rejected_rows": int(rejected_rows),
        "status": status,
        "error_message": error_message,
    }
    pd.concat([existing, pd.DataFrame([row])], ignore_index=True)[REGISTRY_COLUMNS].to_csv(
        path, index=False
    )
    return {"duplicate": False, **row}


def source_hashes(registry_path: str | Path = SOURCE_REGISTRY_PATH) -> set[str]:
    path = Path(registry_path)
    if not path.exists():
        return set()
    data = pd.read_csv(path)
    return set(data.get("source_hash", pd.Series(dtype="string")).dropna().astype(str))
