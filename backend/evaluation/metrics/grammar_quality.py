"""
Metric 8: Grammar Quality (weight=0.05)

Assesses grammatical correctness and writing quality without
requiring an external grammar API. Uses heuristic signals.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class GrammarQualityResult:
    score: float
    explanation: str
    details: dict


# Common grammar error patterns
GRAMMAR_ERROR_PATTERNS = [
    (r"\bi is\b", "subject-verb agreement (i is)"),
    (r"\bthey is\b", "subject-verb agreement (they is)"),
    (r"\bwe is\b", "subject-verb agreement (we is)"),
    (r"\byou is\b", "subject-verb agreement (you is)"),
    (r"\bdoesnt\b|\bcant\b|\bwont\b|\bdidnt\b|\bisnt\b|\barent\b|\bhasnt\b", "missing apostrophe"),
    (r"\b(\w+)\s+\1\b", "word repetition"),
    (r"\s{2,}", "extra whitespace"),
    (r"[.!?]{3,}", "excessive punctuation"),
    (r"\b(?:alot|irregardless|alright)\b", "non-standard word"),
]

POSITIVE_GRAMMAR_SIGNALS = [
    "Dear",        # proper salutation
    "Sincerely",   # proper closing
    "Best regards",
    "Thank you",
    "Please",
]


def compute(generated: str) -> GrammarQualityResult:
    """
    Compute grammar quality using heuristic rules.

    Scoring:
    - Start from 1.0
    - Deduct for each error found (proportional)
    - Bonus for positive professional writing signals
    - Check sentence structure variety
    """
    errors: list[dict] = []
    text = generated

    # ── Error detection ───────────────────────────────────────────────────
    for pattern, description in GRAMMAR_ERROR_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            errors.append({"pattern": description, "match": str(match)[:50]})

    # Check for very short sentences (< 5 words) that are not greetings
    sentences = [s.strip() for s in re.split(r"[.!?]", text) if s.strip()]
    short_sentences = [s for s in sentences if 1 < len(s.split()) < 4 and len(s) > 3]
    errors.extend([{"pattern": "very short sentence", "match": s[:40]} for s in short_sentences[:2]])

    # Check starts with uppercase
    if text and not text[0].isupper():
        errors.append({"pattern": "does not start with uppercase", "match": text[:20]})

    # Check ends with proper punctuation
    stripped = text.strip()
    if stripped and stripped[-1] not in ".!?":
        errors.append({"pattern": "missing terminal punctuation", "match": stripped[-20:]})

    # ── Positive signals ──────────────────────────────────────────────────
    positive_hits = sum(1 for signal in POSITIVE_GRAMMAR_SIGNALS if signal in generated)

    # ── Sentence variety ──────────────────────────────────────────────────
    if len(sentences) >= 3:
        lengths = [len(s.split()) for s in sentences]
        length_variance = max(lengths) - min(lengths)
        variety_bonus = min(0.1, length_variance / 100)
    else:
        variety_bonus = 0.0

    # ── Score calculation ─────────────────────────────────────────────────
    error_penalty = min(0.7, len(errors) * 0.08)
    positive_bonus = min(0.2, positive_hits * 0.05)
    score = float(max(0.0, min(1.0, 1.0 - error_penalty + positive_bonus + variety_bonus)))

    # Word count sanity
    word_count = len(generated.split())
    if word_count < 20:
        score *= 0.5

    if score >= 0.85:
        explanation = (
            f"Excellent grammar quality (score={score:.2f}). "
            f"Response demonstrates professional writing with {len(errors)} minor issue(s). "
            f"Positive signals: {positive_hits}."
        )
    elif score >= 0.65:
        explanation = (
            f"Good grammar quality (score={score:.2f}). "
            f"{len(errors)} grammar concern(s) detected but overall professional."
        )
    elif score >= 0.45:
        explanation = (
            f"Moderate grammar quality (score={score:.2f}). "
            f"{len(errors)} issues detected: "
            f"{', '.join(set(e['pattern'] for e in errors[:3]))}."
        )
    else:
        explanation = (
            f"Poor grammar quality (score={score:.2f}). "
            f"Multiple grammar issues ({len(errors)}) undermine professionalism."
        )

    return GrammarQualityResult(
        score=score,
        explanation=explanation,
        details={
            "errors": errors[:10],
            "error_count": len(errors),
            "positive_signals": positive_hits,
            "sentence_count": len(sentences),
            "word_count": word_count,
        },
    )
