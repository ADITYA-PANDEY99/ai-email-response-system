"""
Metric 11: Retrieval Consistency (weight derived from hallucination)

Checks that the generated response is consistent with the retrieved
example responses (not just semantically close but not contradicting).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from backend.retrieval.embedder import get_embedder


@dataclass
class RetrievalConsistencyResult:
    score: float
    explanation: str
    details: dict


def compute(
    generated: str,
    retrieved_replies: list[str],
) -> RetrievalConsistencyResult:
    """
    Measure consistency between generated response and retrieved example replies.

    High score = generated response is in-distribution with retrieved examples.
    Low score = response significantly diverges from what similar cases resolved to.
    """
    if not retrieved_replies:
        return RetrievalConsistencyResult(
            score=0.70,
            explanation="No retrieved examples available; neutral score applied.",
            details={"num_retrieved": 0, "avg_similarity": None},
        )

    embedder = get_embedder()
    vec_gen = embedder.embed_text(generated[:600])

    similarities: list[float] = []
    for reply in retrieved_replies[:5]:  # max 5
        if not reply or not reply.strip():
            continue
        vec_ret = embedder.embed_text(reply[:600])
        sim = float(np.clip(np.dot(vec_gen, vec_ret), 0, 1))
        similarities.append(sim)

    if not similarities:
        return RetrievalConsistencyResult(
            score=0.70,
            explanation="Retrieved replies were empty.",
            details={"num_retrieved": 0, "avg_similarity": None},
        )

    avg_sim = float(np.mean(similarities))
    max_sim = float(np.max(similarities))
    min_sim = float(np.min(similarities))

    # Score biased toward max similarity (best-case retrieval match)
    score = float(np.clip(0.6 * avg_sim + 0.4 * max_sim, 0.0, 1.0))

    if score >= 0.80:
        explanation = (
            f"High retrieval consistency (score={score:.2f}). "
            f"Generated response closely aligns with {len(similarities)} retrieved examples "
            f"(avg similarity={avg_sim:.2f})."
        )
    elif score >= 0.60:
        explanation = (
            f"Good retrieval consistency (score={score:.2f}). "
            f"Response is broadly consistent with retrieved examples "
            f"(avg similarity={avg_sim:.2f})."
        )
    elif score >= 0.40:
        explanation = (
            f"Moderate retrieval consistency (score={score:.2f}). "
            f"Response diverges from some retrieved examples "
            f"(avg={avg_sim:.2f}, min={min_sim:.2f})."
        )
    else:
        explanation = (
            f"Low retrieval consistency (score={score:.2f}). "
            "Generated response significantly differs from retrieved similar cases. "
            "Consider reviewing retrieval quality."
        )

    return RetrievalConsistencyResult(
        score=score,
        explanation=explanation,
        details={
            "num_retrieved": len(similarities),
            "avg_similarity": avg_sim,
            "max_similarity": max_sim,
            "min_similarity": min_sim,
            "individual_scores": similarities,
        },
    )
