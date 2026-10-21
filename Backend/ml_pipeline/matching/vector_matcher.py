"""Vector similarity search and marketplace constraint filtering.

Implements cosine similarity matching combined with marketplace business constraints:
- Hard filter: availability_status must be 'Active'
- Hard filter: material/category compatibility
- Top-K ranked candidate generation with interpretable similarity labels
"""

from __future__ import annotations

import math
from typing import Any


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for a, b in zip(vec_a, vec_b):
        dot += a * b
        norm_a += a * a
        norm_b += b * b

    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0

    sim = dot / (math.sqrt(norm_a) * math.sqrt(norm_b))
    # Bound to [-1.0, 1.0] to prevent floating point inaccuracies
    return max(-1.0, min(1.0, float(sim)))


def _classify_similarity(score: float) -> str:
    """Assign human-readable match quality label based on cosine similarity."""
    if score >= 0.82:
        return "EXCELLENT_MATCH"
    if score >= 0.70:
        return "STRONG_MATCH"
    if score >= 0.55:
        return "MODERATE_MATCH"
    return "WEAK_MATCH"


def rank_candidates(
    requirement_vector: list[float],
    candidate_listings: list[dict[str, Any]],
    top_k: int = 10,
    min_similarity: float = 0.40,
    enforce_active_only: bool = True,
    enforce_category_match: bool = False,
    target_category: str | None = None,
) -> list[dict[str, Any]]:
    """Rank candidate scrap listings for a requirement based on vector similarity and hard rules.

    Each candidate dict is expected to contain:
        - id: str or UUID
        - embedding: list[float]
        - material_name: str
        - category: str (optional)
        - availability_status: str (e.g. 'Active', 'Sold', 'Reserved')
        - quantity: float
        - unit: str
        - asking_price: float (optional)
        - location: dict or str (optional)

    Returns:
        Sorted list of top-K matching records with similarity scores and ranking metadata.
    """
    scored_candidates = []

    for listing in candidate_listings:
        # Rule 1: Hard filter on availability
        status = str(listing.get("availability_status") or "Active").strip().title()
        if enforce_active_only and status != "Active":
            continue

        # Rule 2: Hard filter on category/material compatibility if enabled
        if enforce_category_match and target_category:
            listing_cat = str(listing.get("category") or "").strip().lower()
            target_cat = target_category.strip().lower()
            if target_cat not in listing_cat and listing_cat not in target_cat:
                continue

        listing_vec = listing.get("embedding")
        if not listing_vec:
            continue

        similarity = cosine_similarity(requirement_vector, listing_vec)
        if similarity < min_similarity:
            continue

        match_record = {
            "listing_id": str(listing.get("id")),
            "material_name": listing.get("material_name"),
            "category": listing.get("category"),
            "grade": listing.get("grade"),
            "quantity": listing.get("quantity"),
            "unit": listing.get("unit"),
            "asking_price": listing.get("asking_price"),
            "location": listing.get("location"),
            "similarity_score": round(similarity, 4),
            "match_quality": _classify_similarity(similarity),
            "hard_constraints_passed": True,
        }
        scored_candidates.append(match_record)

    # Sort descending by similarity score
    scored_candidates.sort(key=lambda x: x["similarity_score"], reverse=True)

    # Return top K
    return scored_candidates[:top_k]
