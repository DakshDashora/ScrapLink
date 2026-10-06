"""Neon-backed active model registry with immutable Cloudinary artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..core.db_models import ModelVersion
from ..storage.cloudinary_models import upload_model_artifacts


def load_active_model_metadata(db: Session) -> dict[str, Any] | None:
    record = db.execute(
        select(ModelVersion)
        .where(ModelVersion.is_active.is_(True))
        .order_by(ModelVersion.created_at.desc(), ModelVersion.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if record is None:
        return None
    return {
        "version": record.version,
        "artifact_public_ids": record.artifact_public_ids,
        "artifact_checksums": record.artifact_checksums,
        "metrics": record.metrics,
        "feature_schema": record.feature_schema,
    }


def activate_model_version(
    db: Session,
    version: str,
    directory: str | Path,
    *,
    metrics: dict[str, Any],
    feature_schema: dict[str, Any],
) -> dict[str, Any]:
    """Upload a full candidate and atomically make it the active version."""
    artifact_public_ids, artifact_checksums = upload_model_artifacts(version, directory)
    record = ModelVersion(
        version=version,
        is_active=True,
        artifact_public_ids=artifact_public_ids,
        artifact_checksums=artifact_checksums,
        metrics=metrics,
        feature_schema=feature_schema,
    )
    try:
        db.execute(
            update(ModelVersion)
            .where(ModelVersion.is_active.is_(True))
            .values(is_active=False)
        )
        db.add(record)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {
        "version": record.version,
        "artifact_public_ids": artifact_public_ids,
        "artifact_checksums": artifact_checksums,
        "metrics": metrics,
        "feature_schema": feature_schema,
    }
