"""
Metric 12: Length Penalty (weight=0.02)

Penalises responses that are excessively short (unhelpfully terse)
or excessively long (padding that wastes customer's time).

Optimal range: 80–350 words for most customer service emails.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

OPTIMAL_MIN_WORDS = 80
OPTIMAL_MAX_WORDS = 350
ABSOLUTE_MIN_WORDS = 20
ABSOLUTE_MAX_WORDS = 800


@dataclass
class LengthPenaltyResult:
    score: float
    explanation: str
    details: dict


def compute(
    generated: str,
    reference: str | None = None,
) -> LengthPenaltyResult:
    """
    Compute length appropriateness score.

    If reference available: score relative to reference length.
    Otherwise: score against optimal absolute range.
    """
    gen_words = len(generated.split())
    ref_words = len(reference.split()) if reference else None

    # ── Reference-relative scoring ────────────────────────────────────────
    if ref_words and ref_words > 0:
        ratio = gen_words / ref_words
        # Ideal: 0.7x – 1.4x of reference length
        if 0.7 <= ratio <= 1.4:
            score = 1.0
        elif ratio < 0.7:
            # Too short relative to reference
            score = float(max(0.0, ratio / 0.7))
        else:
            # Too long
            excess = ratio - 1.4
            score = float(max(0.0, 1.0 - excess * 0.5))

        length_type = f"vs reference ({ref_words} words)"
    else:
        # ── Absolute range scoring ─────────────────────────────────────────
        if OPTIMAL_MIN_WORDS <= gen_words <= OPTIMAL_MAX_WORDS:
            score = 1.0
        elif gen_words < OPTIMAL_MIN_WORDS:
            if gen_words < ABSOLUTE_MIN_WORDS:
                score = 0.1
            else:
                # Linear interpolation
                score = (gen_words - ABSOLUTE_MIN_WORDS) / (OPTIMAL_MIN_WORDS - ABSOLUTE_MIN_WORDS)
                score = float(0.3 + 0.7 * score)
        else:
            if gen_words > ABSOLUTE_MAX_WORDS:
                score = 0.3
            else:
                # Logarithmic penalty for long responses
                excess_ratio = (gen_words - OPTIMAL_MAX_WORDS) / (ABSOLUTE_MAX_WORDS - OPTIMAL_MAX_WORDS)
                score = float(1.0 - 0.5 * excess_ratio)

        length_type = f"absolute ({OPTIMAL_MIN_WORDS}–{OPTIMAL_MAX_WORDS} words optimal)"

    score = float(max(0.0, min(1.0, score)))

    # ── Explanation ───────────────────────────────────────────────────────
    if score >= 0.90:
        explanation = (
            f"Appropriate length (score={score:.2f}). "
            f"{gen_words} words is within optimal range {length_type}."
        )
    elif score >= 0.65:
        explanation = (
            f"Slightly suboptimal length (score={score:.2f}). "
            f"{gen_words} words compared to {length_type}."
        )
    elif gen_words < OPTIMAL_MIN_WORDS:
        explanation = (
            f"Response too short (score={score:.2f}). "
            f"{gen_words} words may be insufficient for a complete customer response. "
            f"Target: {OPTIMAL_MIN_WORDS}–{OPTIMAL_MAX_WORDS} words."
        )
    else:
        explanation = (
            f"Response too long (score={score:.2f}). "
            f"{gen_words} words may overwhelm the customer. "
            f"Consider trimming to {OPTIMAL_MAX_WORDS} words."
        )

    return LengthPenaltyResult(
        score=score,
        explanation=explanation,
        details={
            "generated_word_count": gen_words,
            "reference_word_count": ref_words,
            "optimal_range": [OPTIMAL_MIN_WORDS, OPTIMAL_MAX_WORDS],
            "length_type": length_type,
        },
    )
