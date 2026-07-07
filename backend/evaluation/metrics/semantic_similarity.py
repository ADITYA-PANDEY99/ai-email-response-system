"""
Metric 1: Semantic Similarity (weight=0.30)

Measures the semantic closeness between generated and reference reply
using sentence-transformer cosine similarity.

Why: BLEU score only captures n-gram overlap. Two sentences can be
semantically identical but lexically different ("We'll help you" vs
"Our team will assist"). Cosine similarity on dense embeddings captures
meaning, not word choice.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from backend.retrieval.embedder import get_embedder


@dataclass
class SemanticSimilarityResult:
    score: float
    explanation: str
    details: dict


def compute(generated: str, reference: str) -> SemanticSimilarityResult:
    """
    Compute cosine similarity between generated and reference replies.

    Returns a score in [0, 1] where:
    - 1.0 = identical meaning
    - 0.8+ = excellent semantic match
    - 0.6-0.8 = good alignment with some variation
    - <0.6 = significant semantic drift
    """
    if not reference or not reference.strip():
        return SemanticSimilarityResult(
            score=0.5,
            explanation="No reference reply provided; neutral score assigned.",
            details={"raw_cosine": None, "has_reference": False},
        )

    embedder = get_embedder()
    vec_gen = embedder.embed_text(generated)
    vec_ref = embedder.embed_text(reference)

    # Vectors are already L2-normalised → dot product = cosine similarity
    cosine = float(np.dot(vec_gen, vec_ref))
    # Clamp to [0, 1]
    cosine = max(0.0, min(1.0, cosine))

    # Score interpretation
    if cosine >= 0.90:
        explanation = (
            f"Excellent semantic alignment (cosine={cosine:.3f}). The generated response "
            "conveys nearly identical meaning to the reference reply."
        )
    elif cosine >= 0.75:
        explanation = (
            f"Strong semantic similarity (cosine={cosine:.3f}). The response captures "
            "the core message with natural lexical variation."
        )
    elif cosine >= 0.60:
        explanation = (
            f"Moderate semantic overlap (cosine={cosine:.3f}). The response covers "
            "the main topic but may miss some nuanced elements."
        )
    elif cosine >= 0.45:
        explanation = (
            f"Weak semantic similarity (cosine={cosine:.3f}). The response diverges "
            "noticeably from the reference in meaning and topic coverage."
        )
    else:
        explanation = (
            f"Low semantic similarity (cosine={cosine:.3f}). The generated response "
            "appears to address a different topic than the reference reply."
        )

    return SemanticSimilarityResult(
        score=cosine,
        explanation=explanation,
        details={"raw_cosine": cosine, "has_reference": True},
    )
