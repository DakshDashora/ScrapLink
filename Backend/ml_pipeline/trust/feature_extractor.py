"""Feature extraction for the ScrapLink baseline listing anomaly / trust model.

Extracts scoring-time features strictly using listing metadata and market price
benchmarks available at evaluation time (preventing future target leakage).
"""

from __future__ import annotations

import math
from typing import Any

# Default reference benchmark prices (INR/kg) for canonical categories/materials.
# Used when dynamic market benchmark isn't passed at scoring time.
DEFAULT_BENCHMARK_INR_PER_KG: dict[str, float] = {
    "steel": 35.0,
    "ms steel scrap": 35.0,
    "ms turnings": 28.0,
    "steel plates": 42.0,
    "stainless steel": 120.0,
    "ss 304 scrap": 120.0,
    "ss 316 scrap": 180.0,
    "aluminium": 140.0,
    "aluminium extrusion": 145.0,
    "aluminium cans": 95.0,
    "copper": 750.0,
    "copper wire": 760.0,
    "brass": 480.0,
    "zinc": 240.0,
    "lead": 180.0,
}

FEATURE_NAMES: list[str] = [
    "price_ratio_to_benchmark",
    "log_quantity_kg",
    "log_order_value_inr",
    "has_grade",
    "has_description",
    "description_length_capped",
    "has_coordinates",
    "is_standard_unit",
]


def _normalize_unit_to_kg(quantity: float, unit: str | None) -> float:
    """Normalize quantity to kilograms."""
    unit_str = (unit or "kg").strip().lower()
    if unit_str in ("tonne", "ton", "mt"):
        return quantity * 1000.0
    return quantity


def _resolve_benchmark(material_name: str, category: str | None) -> float:
    """Look up closest reference price in INR/kg."""
    mat_key = material_name.strip().lower()
    if mat_key in DEFAULT_BENCHMARK_INR_PER_KG:
        return DEFAULT_BENCHMARK_INR_PER_KG[mat_key]
    
    # Try substring match
    for k, v in DEFAULT_BENCHMARK_INR_PER_KG.items():
        if k in mat_key or mat_key in k:
            return v

    if category:
        cat_key = category.strip().lower()
        if cat_key in DEFAULT_BENCHMARK_INR_PER_KG:
            return DEFAULT_BENCHMARK_INR_PER_KG[cat_key]

    # Conservative default for scrap metals
    return 60.0


def extract_listing_features(
    material_name: str,
    asking_price: float | int | None,
    quantity: float | int,
    unit: str = "kg",
    category: str | None = None,
    grade: str | None = None,
    description: str | None = None,
    location: Any = None,
    benchmark_price: float | None = None,
) -> dict[str, float]:
    """Extract scoring-time numerical features for Isolation Forest anomaly detection.

    Returns a feature dictionary with strictly finite float values.
    """
    qty = max(0.1, float(quantity))
    qty_kg = _normalize_unit_to_kg(qty, unit)
    
    # Price per kg handling
    price = float(asking_price) if asking_price is not None and asking_price > 0 else 0.0
    unit_str = (unit or "kg").strip().lower()
    if unit_str in ("tonne", "ton", "mt"):
        price_per_kg = price / 1000.0 if price > 0 else 0.0
    else:
        price_per_kg = price

    bench = benchmark_price if (benchmark_price and benchmark_price > 0) else _resolve_benchmark(material_name, category)
    
    # Feature 1: Price ratio relative to benchmark
    if price_per_kg > 0 and bench > 0:
        price_ratio = min(10.0, max(0.01, price_per_kg / bench))
    else:
        price_ratio = 1.0  # neutral if unpriced

    # Feature 2: Log quantity in kg
    log_qty = math.log1p(qty_kg)

    # Feature 3: Log total order value (INR)
    total_val = price_per_kg * qty_kg
    log_order_val = math.log1p(max(0.0, total_val))

    # Feature 4: Has grade specified
    has_grade = 1.0 if (grade and str(grade).strip()) else 0.0

    # Feature 5 & 6: Description completeness
    desc_clean = (description or "").strip()
    has_desc = 1.0 if len(desc_clean) > 0 else 0.0
    desc_len_capped = float(min(500, len(desc_clean))) / 500.0

    # Feature 7: Has verified location coordinates
    has_coords = 0.0
    if isinstance(location, dict):
        if location.get("latitude") is not None and location.get("longitude") is not None:
            has_coords = 1.0
        elif location.get("lat") is not None and location.get("lng") is not None:
            has_coords = 1.0

    # Feature 8: Standard weight unit indicator
    is_standard = 1.0 if unit_str in ("kg", "tonne", "ton", "mt") else 0.0

    return {
        "price_ratio_to_benchmark": float(price_ratio),
        "log_quantity_kg": float(log_qty),
        "log_order_value_inr": float(log_order_val),
        "has_grade": float(has_grade),
        "has_description": float(has_desc),
        "description_length_capped": float(desc_len_capped),
        "has_coordinates": float(has_coords),
        "is_standard_unit": float(is_standard),
    }


def to_feature_vector(features: dict[str, float]) -> list[float]:
    """Convert feature dict into an ordered vector aligned with FEATURE_NAMES."""
    return [features[name] for name in FEATURE_NAMES]
