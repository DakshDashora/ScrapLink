"""ML Client helper for main FastAPI backend (Sprint 3 integration).

Enables backend route handlers (Arman) to request Sentence-BERT embeddings,
ranked semantic matches, and Isolation Forest trust indicators seamlessly.
"""

from __future__ import annotations

import logging
from typing import Any
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def request_embedding(
    material_name: str,
    category: str | None = None,
    grade: str | None = None,
    description: str | None = None,
    quantity: float | None = None,
    unit: str | None = None,
    location: Any = None,
) -> list[float]:
    """Call the ML Service /embed endpoint to retrieve 384-dim Sentence-BERT vector."""
    if not settings.ML_SERVICE_URL or not settings.ML_JOB_TOKEN:
        # Fallback to local import if standalone service URL is not configured
        from ml_pipeline.matching.text_normalizer import build_matching_text
        from ml_pipeline.matching.embedding_engine import generate_embedding
        text = build_matching_text(material_name, category, grade, description, quantity, unit, location)
        return generate_embedding(text)

    url = f"{settings.ML_SERVICE_URL.rstrip('/')}/embed"
    payload = {
        "material_name": material_name,
        "category": category,
        "grade": grade,
        "description": description,
        "quantity": quantity,
        "unit": unit,
        "location": location,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"X-ML-Job-Token": settings.ML_JOB_TOKEN, "Content-Type": "application/json"},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("embedding", [])
    except Exception as exc:
        logger.warning("ML Service /embed remote call failed (%s); using in-process fallback.", exc)

    # Local fallback
    from ml_pipeline.matching.text_normalizer import build_matching_text
    from ml_pipeline.matching.embedding_engine import generate_embedding
    text = build_matching_text(material_name, category, grade, description, quantity, unit, location)
    return generate_embedding(text)


async def request_trust_indicator(
    material_name: str,
    asking_price: float | None,
    quantity: float,
    unit: str = "kg",
    category: str | None = None,
    grade: str | None = None,
    description: str | None = None,
    location: Any = None,
) -> dict[str, Any]:
    """Call the ML Service /trust/score endpoint to get the listing anomaly/trust signal."""
    if not settings.ML_SERVICE_URL or not settings.ML_JOB_TOKEN:
        from ml_pipeline.trust.trust_service import evaluate_listing_trust
        return evaluate_listing_trust(
            material_name=material_name,
            asking_price=asking_price,
            quantity=quantity,
            unit=unit,
            category=category,
            grade=grade,
            description=description,
            location=location,
        )

    url = f"{settings.ML_SERVICE_URL.rstrip('/')}/trust/score"
    payload = {
        "material_name": material_name,
        "asking_price": asking_price,
        "quantity": quantity,
        "unit": unit,
        "category": category,
        "grade": grade,
        "description": description,
        "location": location,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                json=payload,
                headers={"X-ML-Job-Token": settings.ML_JOB_TOKEN, "Content-Type": "application/json"},
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as exc:
        logger.warning("ML Service /trust/score call failed (%s); using in-process fallback.", exc)

    from ml_pipeline.trust.trust_service import evaluate_listing_trust
    return evaluate_listing_trust(
        material_name=material_name,
        asking_price=asking_price,
        quantity=quantity,
        unit=unit,
        category=category,
        grade=grade,
        description=description,
        location=location,
    )
