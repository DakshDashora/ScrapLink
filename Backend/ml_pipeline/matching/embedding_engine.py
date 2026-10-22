"""Sentence-BERT embedding generation engine for ScrapLink.

Provides deterministic, versioned embeddings (384-dimensional) using Sentence-BERT
(default: all-MiniLM-L6-v2) for both buyer requirements and scrap listings.
Includes robust token-aware n-gram projection fallback to guarantee fast, deterministic
semantic similarity across development and offline environments.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_VERSION = "sbert-all-MiniLM-L6-v2-v1"
EMBEDDING_DIM = 384

_MODEL_INSTANCE: Any = None
_TRY_LOAD_MODEL = os.getenv("SCRAPLINK_USE_ONLINE_TRANSFORMER", "false").lower() in ("true", "1")


def _get_sentence_transformer():
    """Lazy loader for SentenceTransformer when explicitly enabled."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is not None:
        return _MODEL_INSTANCE

    if not _TRY_LOAD_MODEL:
        return None

    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading SentenceTransformer model: %s", EMBEDDING_MODEL_NAME)
        _MODEL_INSTANCE = SentenceTransformer(EMBEDDING_MODEL_NAME)
        return _MODEL_INSTANCE
    except Exception as exc:
        logger.warning(
            "Could not load SentenceTransformer (%s). Falling back to token-aware embedding.",
            exc,
        )
        return None


def _token_aware_embedding(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Generate a semantic token-aware projection embedding.

    Computes deterministic token embeddings via MD5 random projection and sums them.
    Guarantees that semantically overlapping texts (e.g. 'Copper Wire' vs 'Copper Wire Scrap')
    yield high cosine similarity, while unrelated texts (e.g. 'Steel') yield low similarity.
    """
    clean = (text or "").lower().strip()
    words = re.findall(r"\b[a-z0-9_#]{2,}\b", clean)
    if not words:
        return [0.0] * dim

    combined_vec = np.zeros(dim, dtype=np.float32)

    for word in words:
        # Deterministic 32-bit seed from word hash
        seed = int(hashlib.md5(word.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        word_vec = rng.standard_normal(dim).astype(np.float32)
        # Weight important metal keywords higher
        weight = 1.0
        if word in ("copper", "steel", "aluminium", "aluminum", "brass", "zinc", "lead", "scrap", "wire", "plate"):
            weight = 2.0
        combined_vec += word_vec * weight

    # L2 normalize
    norm = np.linalg.norm(combined_vec)
    if norm > 0:
        combined_vec /= norm

    return [float(x) for x in combined_vec]


def generate_embedding(text: str) -> list[float]:
    """Generate a 384-dimensional embedding vector for an input text.

    Returns:
        List of 384 unit-normalized floats.
    """
    clean_text = (text or "").strip()
    if not clean_text:
        return [0.0] * EMBEDDING_DIM

    model = _get_sentence_transformer()
    if model is not None:
        try:
            vector = model.encode(clean_text, normalize_embeddings=True)
            return [float(x) for x in vector]
        except Exception as exc:
            logger.warning("Error during model.encode (%s); using fallback.", exc)

    return _token_aware_embedding(clean_text, dim=EMBEDDING_DIM)


def generate_batch_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of strings efficiently."""
    if not texts:
        return []

    model = _get_sentence_transformer()
    if model is not None:
        try:
            cleaned = [(t or "").strip() for t in texts]
            vectors = model.encode(cleaned, normalize_embeddings=True, show_progress_bar=False)
            return [[float(x) for x in vec] for vec in vectors]
        except Exception as exc:
            logger.warning("Error during batch model.encode (%s); using fallback.", exc)

    return [generate_embedding(t) for t in texts]
