"""Trust and anomaly scoring service for marketplace scrap listings.

Transforms raw listing metadata into scoring-time features, runs inference
through the baseline Isolation Forest model, and returns an explainable
decision-support indicator with transparent flags and compliance disclaimers.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from .feature_extractor import (
    DEFAULT_BENCHMARK_INR_PER_KG,
    extract_listing_features,
    to_feature_vector,
)
from .model import load_baseline_isolation_forest

logger = logging.getLogger(__name__)


def _generate_explainable_flags(
    features: dict[str, float],
    asking_price: float | int | None,
) -> list[str]:
    """Identify rule-based explanatory flags to accompany the statistical anomaly score."""
    flags: list[str] = []

    price_ratio = features.get("price_ratio_to_benchmark", 1.0)
    if asking_price is not None and asking_price > 0:
        if price_ratio < 0.40:
            flags.append("PRICE_SIGNIFICANTLY_BELOW_MARKET_BENCHMARK")
        elif price_ratio > 2.50:
            flags.append("PRICE_SIGNIFICANTLY_ABOVE_MARKET_BENCHMARK")

    # High quantity flag (> 50,000 kg / 50 tonnes)
    log_qty = features.get("log_quantity_kg", 0.0)
    if log_qty > 10.8:  # ln(50000) ~ 10.82
        flags.append("UNUSUALLY_LARGE_VOLUME")

    if features.get("has_grade", 0.0) == 0.0:
        flags.append("MISSING_SPECIFIED_GRADE")

    if features.get("has_description", 0.0) == 0.0 or features.get("description_length_capped", 0.0) < 0.04:
        flags.append("MINIMAL_LISTING_DESCRIPTION")

    if features.get("has_coordinates", 0.0) == 0.0:
        flags.append("UNVERIFIED_LOCATION_COORDINATES")

    return flags


def evaluate_listing_trust(
    material_name: str,
    asking_price: float | int | None,
    quantity: float | int,
    unit: str = "kg",
    category: str | None = None,
    grade: str | None = None,
    description: str | None = None,
    location: Any = None,
    benchmark_price: float | None = None,
) -> dict[str, Any]:
    """Score a listing using the baseline Isolation Forest model and feature rules.

    Returns:
        Structured dictionary matching the Sprint 3 decision-support specification.
    """
    # 1. Extract scoring-time features
    features = extract_listing_features(
        material_name=material_name,
        asking_price=asking_price,
        quantity=quantity,
        unit=unit,
        category=category,
        grade=grade,
        description=description,
        location=location,
        benchmark_price=benchmark_price,
    )

    vec = to_feature_vector(features)
    X = np.array([vec], dtype=np.float64)

    # 2. Score with Isolation Forest
    model, metadata = load_baseline_isolation_forest()

    prediction = model.predict(X)[0]  # 1 = Normal, -1 = Anomaly
    raw_score = model.score_samples(X)[0]  # Higher score = more normal; lower = more abnormal

    # Normalize raw score to a 0.0 - 1.0 anomaly index (0 = very normal, 1 = extreme outlier)
    # IsolationForest raw_scores typically range from -0.7 (severe anomaly) to -0.35 (dense normal)
    # Normalizing: clip between -0.70 and -0.35
    clipped = max(-0.70, min(-0.35, float(raw_score)))
    anomaly_index = round((-0.35 - clipped) / 0.35, 4)

    is_anomaly = bool(prediction == -1 or anomaly_index >= 0.50)
    status_label = "UNUSUAL_PATTERN" if is_anomaly else "NORMAL_PATTERN"

    # 3. Transparent explainable flags
    flags = _generate_explainable_flags(features, asking_price)

    # Contextual buyer advice
    if is_anomaly:
        guidance = (
            "This listing displays price or volume characteristics that deviate from typical "
            "marketplace patterns. Buyers are advised to request sample inspection and verify "
            "seller credentials before proceeding."
        )
    else:
        guidance = (
            "Listing specifications, pricing ratios, and details conform to typical marketplace patterns."
        )

    return {
        "status": "success",
        "indicator": status_label,
        "is_unusual_pattern": is_anomaly,
        "anomaly_score": anomaly_index,
        "confidence_level": "BASELINE_HEURISTIC",
        "flags": flags,
        "buyer_guidance": guidance,
        "features_evaluated": features,
        "model_version": metadata.get("model_version", "isoforest-v1.0.0"),
        "estimate_type": "decision_support_anomaly_indicator",
        "is_fraud_probability": False,
        "disclaimer": (
            "This indicator is an automated decision-support signal based on statistical listing patterns. "
            "It does not represent a fraud probability or guaranteed verification."
        ),
    }
