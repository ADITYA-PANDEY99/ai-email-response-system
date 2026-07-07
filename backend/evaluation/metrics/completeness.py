"""
Metric 4: Completeness (weight=0.15)

Measures how fully the generated response addresses all topics
raised in the incoming email. Incomplete responses leave customers
with unanswered questions.

Method: sentence-level coverage analysis — each sentence in the
incoming email that raises a question/concern should have a
corresponding addressed topic in the generated response.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

from backend.retrieval.embedder import get_embedder

# Patterns indicating customer expectations
QUESTION_PATTERNS = [
    r"\?",
    r"\bcan you\b",
    r"\bcould you\b",
    r"\bwould you\b",
    r"\bplease\b",
    r"\bi need\b",
    r"\bi want\b",
    r"\bi would like\b",
    r"\bwhat is\b",
    r"\bhow do\b",
    r"\bwhen will\b",
    r"\bwhere is\b",
]


def _extract_concerns(email_body: str) -> list[str]:
    """Extract distinct concerns/questions from email body."""
    sentences = re.split(r"(?<=[.!?])\s+", email_body.strip())
    concerns = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 15:
            continue
        if any(re.search(p, sent, re.IGNORECASE) for p in QUESTION_PATTERNS):
            concerns.append(sent)
    # If no explicit questions, treat full email as one concern
    return concerns if concerns else [email_body[:300]]


@dataclass
class CompletenessResult:
    score: float
    explanation: str
    details: dict


def compute(
    generated: str,
    incoming_email: str,
    reference: str | None = None,
) -> CompletenessResult:
    """
    Compute completeness score.

    Logic:
    1. Extract distinct concerns from the incoming email.
    2. For each concern, measure semantic similarity to the generated response.
    3. Score = proportion of concerns adequately addressed (sim > threshold).
    4. Bonus if generated length is comparable to reference.
    """
    embedder = get_embedder()
    concerns = _extract_concerns(incoming_email)
    threshold = 0.45  # cosine sim threshold for "addressed"

    # Embed generated response once
    vec_gen = embedder.embed_text(generated[:1000])

    addressed = []
    concern_scores = []
    for concern in concerns:
        vec_concern = embedder.embed_text(concern)
        sim = float(np.clip(np.dot(vec_concern, vec_gen), 0, 1))
        concern_scores.append(sim)
        addressed.append(sim >= threshold)

    coverage_rate = sum(addressed) / max(len(addressed), 1)

    # Length completeness: generated should be substantive
    gen_word_count = len(generated.split())
    ref_word_count = len(reference.split()) if reference else 150
    length_ratio = min(gen_word_count / max(ref_word_count, 1), 1.5)
    length_score = min(1.0, length_ratio) if length_ratio >= 0.5 else length_ratio * 0.8

    # Penalise very short responses regardless of coverage
    if gen_word_count < 30:
        coverage_rate *= 0.5

    score = float(np.clip(0.75 * coverage_rate + 0.25 * length_score, 0.0, 1.0))

    n_addressed = sum(addressed)
    n_total = len(concerns)

    if score >= 0.85:
        explanation = (
            f"Highly complete response (score={score:.2f}). "
            f"Addressed {n_addressed}/{n_total} customer concerns identified in the email."
        )
    elif score >= 0.65:
        explanation = (
            f"Mostly complete (score={score:.2f}). {n_addressed}/{n_total} concerns addressed. "
            "One or two topics may need more attention."
        )
    elif score >= 0.45:
        explanation = (
            f"Partially complete (score={score:.2f}). Only {n_addressed}/{n_total} concerns "
            "clearly addressed. The response should cover more customer points."
        )
    else:
        explanation = (
            f"Incomplete response (score={score:.2f}). {n_addressed}/{n_total} concerns addressed. "
            "Major customer concerns may have been overlooked."
        )

    return CompletenessResult(
        score=score,
        explanation=explanation,
        details={
            "num_concerns": n_total,
            "addressed_count": n_addressed,
            "coverage_rate": coverage_rate,
            "concern_scores": concern_scores,
            "generated_word_count": gen_word_count,
            "length_score": length_score,
        },
    )
