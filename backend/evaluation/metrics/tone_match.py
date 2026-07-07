"""
Metric 3: Tone Match (weight=0.10)

Ensures the generated response uses the appropriate tone
(formal, friendly, empathetic, urgent) matching the expected tone.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

TONE_LEXICONS: dict[str, dict[str, list[str]]] = {
    "formal": {
        "positive": [
            "dear", "sincerely", "regards", "respectfully", "pleased to",
            "in accordance", "pursuant to", "kindly", "at your earliest"
        ],
        "negative": ["hey", "hi there", "no worries", "cool", "awesome", "totally"],
    },
    "friendly": {
        "positive": [
            "happy to help", "great news", "absolutely", "sure",
            "let me know", "feel free", "hope this helps", "no problem"
        ],
        "negative": ["pursuant to", "aforementioned", "hereby", "henceforth"],
    },
    "empathetic": {
        "positive": [
            "understand how frustrating", "i'm so sorry", "sincerely apologize",
            "completely understand", "must be", "how you feel", "deeply sorry",
            "appreciate your patience", "i can imagine"
        ],
        "negative": ["unfortunately we cannot", "per our policy", "as stated"],
    },
    "urgent": {
        "positive": [
            "immediately", "right away", "as soon as possible", "priority",
            "urgent", "asap", "within the next hour", "right now"
        ],
        "negative": ["take your time", "whenever you get a chance"],
    },
    "professional": {
        "positive": [
            "thank you for", "please", "we appreciate", "best regards",
            "our team", "we will", "we have", "i wanted to"
        ],
        "negative": ["dunno", "gonna", "wanna", "btw", "lol"],
    },
}

# Default tone weights for scoring
DEFAULT_TONE = "professional"


@dataclass
class ToneMatchResult:
    score: float
    explanation: str
    details: dict


def compute(
    generated: str,
    expected_tone: str | None = None,
) -> ToneMatchResult:
    """
    Compute tone match score between generated response and expected tone.

    Scoring:
    - If expected_tone provided: check positive signals - check negative signals
    - If no tone: evaluate against "professional" baseline
    """
    target_tone = (expected_tone or DEFAULT_TONE).lower().strip()
    gen_lower = generated.lower()

    # Map common tone aliases
    tone_aliases = {
        "formal": "formal",
        "business": "formal",
        "enterprise": "formal",
        "friendly": "friendly",
        "casual": "friendly",
        "warm": "friendly",
        "empathetic": "empathetic",
        "sympathetic": "empathetic",
        "apologetic": "empathetic",
        "urgent": "urgent",
        "critical": "urgent",
        "professional": "professional",
        "neutral": "professional",
    }
    canonical_tone = tone_aliases.get(target_tone, "professional")

    lexicon = TONE_LEXICONS.get(canonical_tone, TONE_LEXICONS["professional"])
    positive_signals = lexicon["positive"]
    negative_signals = lexicon["negative"]

    positive_hits = [s for s in positive_signals if s in gen_lower]
    negative_hits = [s for s in negative_signals if s in gen_lower]

    positive_rate = len(positive_hits) / max(len(positive_signals), 1)
    negative_penalty = len(negative_hits) / max(len(negative_signals), 1)

    raw_score = positive_rate - 0.5 * negative_penalty
    score = float(max(0.0, min(1.0, 0.4 + raw_score * 0.6)))  # baseline 0.4

    # Word count heuristic: very short = likely not tonal enough
    word_count = len(generated.split())
    if word_count < 30:
        score *= 0.7

    if score >= 0.80:
        explanation = (
            f"Excellent tone alignment with '{canonical_tone}' style (score={score:.2f}). "
            f"Detected signals: {', '.join(positive_hits[:3])}."
        )
    elif score >= 0.60:
        explanation = (
            f"Good tone match for '{canonical_tone}' (score={score:.2f}). "
            f"Response has appropriate register with minor variations."
        )
    elif score >= 0.40:
        explanation = (
            f"Moderate tone alignment (score={score:.2f}). The response's '{canonical_tone}' "
            "tone could be strengthened."
        )
        if negative_hits:
            explanation += f" Inappropriate signals found: {', '.join(negative_hits[:2])}."
    else:
        explanation = (
            f"Tone mismatch detected (score={score:.2f}). "
            f"Expected '{canonical_tone}' but the response language does not align well."
        )

    return ToneMatchResult(
        score=score,
        explanation=explanation,
        details={
            "target_tone": canonical_tone,
            "positive_signals_found": positive_hits,
            "negative_signals_found": negative_hits,
            "positive_rate": positive_rate,
            "negative_penalty": negative_penalty,
        },
    )
