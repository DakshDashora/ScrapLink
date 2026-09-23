"""Immutable model versions and an explicit active-model pointer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..etl.pipeline_config import ACTIVE_MODEL_POINTER, MODEL_REGISTRY_DIR


def _checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_files(directory: Path) -> list[Path]:
    return sorted(path for path in directory.rglob("*") if path.is_file())


def write_active_pointer(version: str, version_dir: str | Path, *, pointer: Path = ACTIVE_MODEL_POINTER) -> Path:
    directory = Path(version_dir)
    required = [
        directory / "metadata.json",
        directory / "feature_schema.json",
        directory / "metrics.json",
        directory / "model_p10.joblib",
        directory / "model_p50.joblib",
        directory / "model_p90.joblib",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Cannot promote incomplete model artifact: {missing}")
    pointer.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": version,
        "path": str(directory),
        "artifact_checksums": {
            str(path.relative_to(directory)): _checksum(path)
            for path in _artifact_files(directory)
        },
    }
    temporary = pointer.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(pointer)
    return pointer


def load_active_model_metadata(pointer: Path = ACTIVE_MODEL_POINTER) -> dict[str, Any] | None:
    if not pointer.exists():
        return None
    payload = json.loads(pointer.read_text(encoding="utf-8"))
    directory = Path(payload["path"])
    if not directory.exists():
        raise FileNotFoundError(f"Active model directory does not exist: {directory}")
    expected = payload.get("artifact_checksums", {})
    actual_files = {
        str(path.relative_to(directory)): _checksum(path)
        for path in _artifact_files(directory)
    }
    if expected != actual_files:
        raise ValueError("Active model artifact checksums do not match the registry pointer")
    return payload


def new_version_dir(version: str) -> Path:
    path = MODEL_REGISTRY_DIR / version
    path.mkdir(parents=True, exist_ok=False)
    return path
