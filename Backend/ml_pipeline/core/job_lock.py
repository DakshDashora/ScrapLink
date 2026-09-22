"""PostgreSQL advisory locks for preventing overlapping ML jobs."""

from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256
from typing import Iterator

from sqlalchemy import text
from sqlalchemy.orm import Session


def _lock_key(job_type: str) -> int:
    value = int.from_bytes(sha256(job_type.encode("utf-8")).digest()[:8], "big")
    return value - (1 << 64) if value >= (1 << 63) else value


@contextmanager
def job_lock(db: Session, job_type: str) -> Iterator[None]:
    key = _lock_key(job_type)
    acquired = False
    try:
        acquired = bool(db.execute(
            text("SELECT pg_try_advisory_lock(:key)"),
            {"key": key},
        ).scalar_one())
        if not acquired:
            raise RuntimeError(f"{job_type} is already running")
        yield
    finally:
        if acquired:
            db.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
            db.commit()
