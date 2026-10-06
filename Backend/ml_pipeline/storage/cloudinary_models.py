"""Private Cloudinary storage for immutable ML model artifacts."""

from __future__ import annotations

import hashlib
import re
import tempfile
from threading import Lock
import time
from pathlib import Path
from typing import Any

import requests

from ..utils import (
    ML_CLOUDINARY_API_KEY,
    ML_CLOUDINARY_API_SECRET,
    ML_CLOUDINARY_CLOUD_NAME,
    ML_CLOUDINARY_MODEL_FOLDER,
)

REQUIRED_ARTIFACTS = {
    "metadata.json",
    "feature_schema.json",
    "metrics.json",
    "model_p10.joblib",
    "model_p50.joblib",
    "model_p90.joblib",
}
_DOWNLOAD_LOCK = Lock()


def _cloudinary():
    if not all((ML_CLOUDINARY_CLOUD_NAME, ML_CLOUDINARY_API_KEY, ML_CLOUDINARY_API_SECRET)):
        raise RuntimeError(
            "ML_CLOUDINARY_CLOUD_NAME, ML_CLOUDINARY_API_KEY, and "
            "ML_CLOUDINARY_API_SECRET must be configured to store model artifacts"
        )
    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError as exc:
        raise RuntimeError(
            "The cloudinary package must be installed in the ML service environment"
        ) from exc

    cloudinary.config(
        cloud_name=ML_CLOUDINARY_CLOUD_NAME,
        api_key=ML_CLOUDINARY_API_KEY,
        api_secret=ML_CLOUDINARY_API_SECRET,
        secure=True,
    )
    return cloudinary


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validated_version(version: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,96}", version):
        raise ValueError("Model version contains unsupported characters")
    return version


def _private_download_url(public_id: str) -> str:
    try:
        from cloudinary.utils import private_download_url
    except ImportError as exc:
        raise RuntimeError(
            "The installed cloudinary package does not provide private asset downloads"
        ) from exc
    return private_download_url(
        public_id,
        None,
        resource_type="raw",
        type="private",
        expires_at=int(time.time()) + 300,
    )


def upload_model_artifacts(
    version: str, directory: str | Path
) -> tuple[dict[str, str], dict[str, str]]:
    """Upload a complete model version as private raw assets."""
    cloudinary = _cloudinary()
    version = _validated_version(version)
    root = Path(directory)
    paths = sorted(path for path in root.rglob("*") if path.is_file())
    missing = REQUIRED_ARTIFACTS - {path.name for path in paths}
    if missing:
        raise FileNotFoundError(f"Cannot upload incomplete model artifacts: {sorted(missing)}")

    public_ids: dict[str, str] = {}
    checksums: dict[str, str] = {}
    for path in paths:
        if path.name in public_ids:
            raise ValueError(f"Duplicate model artifact filename: {path.name}")
        public_id = f"{ML_CLOUDINARY_MODEL_FOLDER}/{version}/{path.name}"
        result = cloudinary.uploader.upload(
            str(path),
            resource_type="raw",
            type="private",
            public_id=public_id,
            overwrite=False,
            unique_filename=False,
            use_filename=False,
        )
        if result.get("public_id") != public_id:
            raise RuntimeError(f"Cloudinary returned an unexpected public ID for {path.name}")
        public_ids[path.name] = public_id
        checksums[path.name] = _sha256(path)

    for filename, public_id in public_ids.items():
        response = requests.get(
            _private_download_url(public_id),
            stream=True,
            timeout=(10, 120),
        )
        response.raise_for_status()
        digest = hashlib.sha256()
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                digest.update(chunk)
        if digest.hexdigest() != checksums[filename]:
            raise ValueError(f"Uploaded model artifact verification failed: {filename}")
    return public_ids, checksums


def download_model_artifacts(metadata: dict[str, Any]) -> Path:
    """Serialize cache creation so concurrent predictions share one download."""
    with _DOWNLOAD_LOCK:
        return _download_model_artifacts(metadata)


def _download_model_artifacts(metadata: dict[str, Any]) -> Path:
    """Download and verify an active model version into an ephemeral cache."""
    version = _validated_version(str(metadata["version"]))
    public_ids = metadata.get("artifact_public_ids")
    checksums = metadata.get("artifact_checksums")
    if not isinstance(public_ids, dict) or not isinstance(checksums, dict):
        raise ValueError("Active model registry record has invalid artifact metadata")
    if set(public_ids) != set(checksums) or not REQUIRED_ARTIFACTS.issubset(public_ids):
        raise ValueError("Active model registry record is missing required model artifacts")
    for filename, public_id in public_ids.items():
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise ValueError(f"Invalid model artifact filename: {filename}")
        if not isinstance(public_id, str) or not public_id:
            raise ValueError(f"Invalid Cloudinary public ID for {filename}")
        if not isinstance(checksums[filename], str) or not re.fullmatch(
            r"[a-f0-9]{64}", checksums[filename]
        ):
            raise ValueError(f"Invalid model artifact checksum for {filename}")

    cache_root = Path(tempfile.gettempdir()) / "scraplink-model-cache"
    destination = cache_root / version
    if destination.exists():
        if all(
            (destination / filename).is_file()
            and _sha256(destination / filename) == checksum
            for filename, checksum in checksums.items()
        ):
            return destination
        for cached_file in destination.iterdir():
            if cached_file.is_file():
                cached_file.unlink()
        destination.rmdir()

    _cloudinary()

    cache_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache_root, prefix=f".{version}.") as temporary:
        staging = Path(temporary)
        for filename, public_id in public_ids.items():
            if Path(filename).name != filename:
                raise ValueError(f"Invalid model artifact filename: {filename}")
            url = _private_download_url(public_id)
            response = requests.get(url, stream=True, timeout=(10, 120))
            response.raise_for_status()
            path = staging / filename
            with path.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
            if _sha256(path) != checksums[filename]:
                raise ValueError(f"Downloaded model artifact checksum mismatch: {filename}")
        staging.replace(destination)
    return destination
