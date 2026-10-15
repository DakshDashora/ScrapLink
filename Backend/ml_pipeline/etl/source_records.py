"""Helpers for preparing canonical source rows for database upserts."""

from __future__ import annotations

from typing import Any


def deduplicate_source_records(
    records: list[dict[str, Any]],
    key_fields: tuple[str, ...],
) -> tuple[list[dict[str, Any]], int]:
    """Keep the last row per database unique key to make bulk upserts safe."""
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for record in records:
        key = tuple(record[field] for field in key_fields)
        unique[key] = record
    return list(unique.values()), len(records) - len(unique)
