"""Retrieval evaluation harness for semantic matching.

Provides Top-K evaluation sanity tests on real/seed scrap listings to verify that
Sentence-BERT representations correctly rank relevant scrap materials higher than
unrelated materials.
"""

from __future__ import annotations

import logging
from typing import Any

from .embedding_engine import generate_embedding
from .text_normalizer import build_matching_text
from .vector_matcher import rank_candidates

logger = logging.getLogger(__name__)

# Representative test evaluation queries
BENCHMARK_EVAL_QUERIES = [
    {
        "query_name": "Steel Scrap Request",
        "material_name": "Heavy Melting Steel Scrap",
        "category": "Steel",
        "grade": "Heavy Melting",
        "quantity": 5000,
        "unit": "kg",
        "description": "Require clean MS steel demolition scrap or plates",
        "expected_material_keywords": ["steel", "ms"],
    },
    {
        "query_name": "Copper Wire Request",
        "material_name": "Copper Wire Scrap",
        "category": "Copper",
        "grade": "#1 Bare Bright",
        "quantity": 1000,
        "unit": "kg",
        "description": "Stripped unalloyed bare bright electrical wire scrap",
        "expected_material_keywords": ["copper"],
    },
    {
        "query_name": "Aluminium Extrusion Request",
        "material_name": "Aluminium 6063 Extrusions",
        "category": "Aluminium",
        "grade": "6063",
        "quantity": 2000,
        "unit": "kg",
        "description": "Clean architectural window profile extrusions",
        "expected_material_keywords": ["aluminium", "aluminum"],
    },
]


def evaluate_matching_retrieval(
    candidate_catalog: list[dict[str, Any]],
    top_k: int = 3,
) -> dict[str, Any]:
    """Run sanity evaluation over test queries against a candidate listing catalog.

    Calculates:
        - top_1_accuracy: Whether top result matches expected category keywords.
        - top_k_accuracy: Whether at least one expected match appears in top K.
        - mean_similarity_top1: Average similarity of the top retrieved candidate.
    """
    total_queries = len(BENCHMARK_EVAL_QUERIES)
    top_1_hits = 0
    top_k_hits = 0
    similarity_sum = 0.0
    detailed_results = []

    # Ensure catalog has embeddings
    prepared_catalog = []
    for item in candidate_catalog:
        catalog_copy = dict(item)
        if "embedding" not in catalog_copy or not catalog_copy["embedding"]:
            text = build_matching_text(
                material_name=catalog_copy.get("material_name", ""),
                category=catalog_copy.get("category"),
                grade=catalog_copy.get("grade"),
                description=catalog_copy.get("description"),
                quantity=catalog_copy.get("quantity"),
                unit=catalog_copy.get("unit"),
                location=catalog_copy.get("location"),
            )
            catalog_copy["embedding"] = generate_embedding(text)
        prepared_catalog.append(catalog_copy)

    for query in BENCHMARK_EVAL_QUERIES:
        q_text = build_matching_text(
            material_name=query["material_name"],
            category=query.get("category"),
            grade=query.get("grade"),
            description=query.get("description"),
            quantity=query.get("quantity"),
            unit=query.get("unit"),
        )
        q_vec = generate_embedding(q_text)

        ranked = rank_candidates(
            requirement_vector=q_vec,
            candidate_listings=prepared_catalog,
            top_k=top_k,
            min_similarity=0.10,
        )

        expected_kw = [k.lower() for k in query["expected_material_keywords"]]
        
        hit_top1 = False
        hit_topk = False
        top1_score = 0.0

        if ranked:
            top_res = ranked[0]
            top1_score = top_res["similarity_score"]
            top_mat = str(top_res["material_name"]).lower()
            top_cat = str(top_res.get("category") or "").lower()
            if any(kw in top_mat or kw in top_cat for kw in expected_kw):
                hit_top1 = True

            for res in ranked:
                r_mat = str(res["material_name"]).lower()
                r_cat = str(res.get("category") or "").lower()
                if any(kw in r_mat or kw in r_cat for kw in expected_kw):
                    hit_topk = True
                    break

        if hit_top1:
            top_1_hits += 1
        if hit_topk:
            top_k_hits += 1
        similarity_sum += top1_score

        detailed_results.append({
            "query": query["query_name"],
            "top_retrieved": ranked[0]["material_name"] if ranked else None,
            "top_similarity": top1_score,
            "top_1_correct": hit_top1,
            "top_k_hit": hit_topk,
        })

    return {
        "total_queries_tested": total_queries,
        "top_1_accuracy": round(top_1_hits / max(1, total_queries), 4),
        "top_k_accuracy": round(top_k_hits / max(1, total_queries), 4),
        "mean_similarity_top1": round(similarity_sum / max(1, total_queries), 4),
        "query_evaluations": detailed_results,
    }
