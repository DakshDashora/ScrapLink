"""Standard text normalization and prompt construction for semantic matching.

Ensures identical preprocessing and text representations for both Scrap Listings
and Buyer Requirements before Sentence-BERT embedding generation.
"""

from __future__ import annotations

import re
from typing import Any


def _clean_text(val: Any) -> str:
    """Strip extra whitespaces and standardize special characters."""
    if val is None:
        return ""
    cleaned = re.sub(r"\s+", " ", str(val)).strip()
    return cleaned


def _format_location(location: Any) -> str:
    """Format location input (dict or string) into a clean 'City, State' string."""
    if not location:
        return ""
    if isinstance(location, dict):
        city = _clean_text(location.get("city") or location.get("address"))
        state = _clean_text(location.get("state") or location.get("region"))
        if city and state:
            return f"{city}, {state}"
        return city or state or ""
    return _clean_text(str(location))


def build_matching_text(
    material_name: str,
    category: str | None = None,
    grade: str | None = None,
    quantity: float | int | str | None = None,
    unit: str | None = None,
    description: str | None = None,
    location: Any = None,
) -> str:
    """Build a deterministic, standardized text representation for Sentence-BERT encoding.

    Both ScrapListing and BuyerRequirement instances must pass through this function
    to ensure vector alignment in the embedding space.

    Example Output:
        "Material: MS Steel Scrap. Category: Steel. Grade: Heavy Melting. Quantity: 5000 kg. Location: Mumbai, Maharashtra. Details: Clean scrap."
    """
    parts: list[str] = []

    clean_mat = _clean_text(material_name)
    if clean_mat:
        parts.append(f"Material: {clean_mat}")

    clean_cat = _clean_text(category)
    if clean_cat:
        parts.append(f"Category: {clean_cat}")

    clean_grade = _clean_text(grade)
    if clean_grade:
        parts.append(f"Grade: {clean_grade}")

    # Parse quantity safely
    numeric_qty: float | None = None
    if quantity is not None:
        try:
            numeric_qty = float(quantity)
        except (ValueError, TypeError):
            numeric_qty = None

    if numeric_qty is not None and numeric_qty > 0:
        clean_unit = _clean_text(unit) or "kg"
        formatted_qty = int(numeric_qty) if numeric_qty.is_integer() else f"{numeric_qty:.2f}"
        parts.append(f"Quantity: {formatted_qty} {clean_unit}")

    loc_str = _format_location(location)
    if loc_str:
        parts.append(f"Location: {loc_str}")

    clean_desc = _clean_text(description)
    if clean_desc:
        parts.append(f"Details: {clean_desc}")

    return ". ".join(parts) + ("." if parts else "")
