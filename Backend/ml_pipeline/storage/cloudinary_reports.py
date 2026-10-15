"""Private Cloudinary storage for date-stamped ML analysis reports."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

import requests

from .cloudinary_models import _cloudinary, _private_download_url


REPORT_CATEGORIES = {"daily", "weekly", "monthly"}


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"Report value is not JSON serializable: {type(value).__name__}")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def upload_analysis_report(
    category: str,
    report_date: datetime,
    run_id: int,
    report: dict[str, Any],
) -> dict[str, str]:
    """Upload and verify one immutable, private JSON report."""
    if category not in REPORT_CATEGORIES:
        raise ValueError(f"Unsupported analysis report category: {category!r}")
    if run_id <= 0:
        raise ValueError("Report run ID must be positive")

    cloudinary = _cloudinary()
    date_path = report_date.astimezone(timezone.utc).strftime("%Y-%m-%d")
    generated_at = datetime.now(timezone.utc).isoformat()
    document = {
        "report_date_utc": date_path,
        "generated_at_utc": generated_at,
        "run_id": run_id,
        **report,
    }
    content = json.dumps(
        document,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
        default=_json_default,
    ).encode("utf-8")
    checksum = _sha256(content)
    public_id = f"reports/{category}/{date_path}-run-{run_id}.json"

    with tempfile.TemporaryDirectory(prefix="scraplink-report-") as temporary:
        report_file = Path(temporary) / f"{date_path}-run-{run_id}.json"
        report_file.write_bytes(content)
        result = cloudinary.uploader.upload(
            str(report_file),
            resource_type="raw",
            type="private",
            public_id=public_id,
            overwrite=False,
            unique_filename=False,
            use_filename=False,
        )
    if result.get("public_id") != public_id:
        raise RuntimeError("Cloudinary returned an unexpected report public ID")

    response = requests.get(
        _private_download_url(public_id),
        timeout=(10, 60),
    )
    response.raise_for_status()
    if _sha256(response.content) != checksum:
        raise ValueError("Uploaded analysis report checksum verification failed")

    return {
        "status": "uploaded",
        "category": category,
        "report_date_utc": date_path,
        "run_id": str(run_id),
        "public_id": public_id,
        "sha256": checksum,
        "format": "json",
    }


def download_analysis_report(reference: dict[str, Any]) -> dict[str, Any]:
    """Download and checksum-verify a report referenced by a pipeline run."""
    category = reference.get("category")
    public_id = reference.get("public_id")
    checksum = reference.get("sha256")
    if category not in REPORT_CATEGORIES or not isinstance(public_id, str):
        raise ValueError("Pipeline run has invalid analysis report metadata")
    expected_prefix = f"reports/{category}/"
    if not public_id.startswith(expected_prefix) or not public_id.endswith(".json"):
        raise ValueError("Analysis report public ID is outside the reports folder")
    if not isinstance(checksum, str) or len(checksum) != 64:
        raise ValueError("Pipeline run has an invalid analysis report checksum")

    response = requests.get(
        _private_download_url(public_id),
        timeout=(10, 60),
    )
    response.raise_for_status()
    if _sha256(response.content) != checksum:
        raise ValueError("Downloaded analysis report checksum verification failed")
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Downloaded analysis report has an invalid document shape")
    return payload
