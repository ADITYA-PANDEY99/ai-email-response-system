"""
Metric 9: Professionalism Score (weight=0.03)

Evaluates whether the response meets business communication standards:
- Proper salutation and closing
- Appropriate formality level
- No emotional language or inappropriate content
- Clear structure (greeting → body → action → closing)
"""
from __future__ import annotations

import re
from dataclasses import dataclass

REQUIRED_ELEMENTS = {
    "salutation": [
        r"^dear\b",
        r"^hello\b",
        r"^good\s+(?:morning|afternoon|evening)\b",
        r"^greetings\b",
    ],
    "closing": [
        r"best\s+regards",
        r"kind\s+regards",
        r"sincerely",
        r"yours\s+(?:truly|faithfully|sincerely)",
        r"warm\s+regards",
        r"thank\s+you",
        r"with\s+appreciation",
    ],
    "action_statement": [
        r"will\s+(?:process|send|contact|follow\s+up|investigate|resolve)",
        r"please\s+(?:let\s+us\s+know|feel\s+free|contact|don[''']t\s+hesitate)",
        r"we\s+(?:will|are|have)",
        r"happy\s+to\s+(?:help|assist)",
    ],
}

UNPROFESSIONAL_SIGNALS = [
    r"\bhey\b(?!\s+there)",  # casual greeting
    r"\bwhatever\b",
    r"\byeah\b",
    r"\bnah\b",
    r"\bbtw\b",
    r"\blol\b",
    r"\bomg\b",
    r"\bfyi\b",
    r"\bwow\b",
    r"!!+",  # multiple exclamation marks
    r"\?\?+",  # multiple question marks
    r"\bsorry\s+but\b.*\bno\b",  # dismissive refusal
]


@dataclass
class ProfessionalismResult:
    score: float
    explanation: str
    details: dict


def compute(generated: str) -> ProfessionalismResult:
    """
    Compute professionalism score based on business email structure.
    """
    text_lower = generated.lower().strip()
    text_lines = generated.strip().split("\n")
    first_line = text_lines[0].lower().strip() if text_lines else ""

    element_scores: dict[str, float] = {}

    # ── Check required elements ───────────────────────────────────────────
    for element, patterns in REQUIRED_ELEMENTS.items():
        if element == "salutation":
            found = any(re.match(p, first_line, re.IGNORECASE) for p in patterns)
        else:
            found = any(re.search(p, text_lower, re.IGNORECASE) for p in patterns)
        element_scores[element] = 1.0 if found else 0.0

    # ── Check unprofessional signals ──────────────────────────────────────
    unprofessional_hits: list[str] = []
    for pattern in UNPROFESSIONAL_SIGNALS:
        matches = re.findall(pattern, generated, re.IGNORECASE)
        unprofessional_hits.extend(matches)

    # ── Structure check ───────────────────────────────────────────────────
    paragraph_count = len([p for p in generated.split("\n\n") if p.strip()])
    has_good_structure = paragraph_count >= 2

    # ── Score aggregation ─────────────────────────────────────────────────
    element_avg = sum(element_scores.values()) / len(element_scores)
    unprofessional_penalty = min(0.5, len(unprofessional_hits) * 0.15)
    structure_bonus = 0.1 if has_good_structure else 0.0

    score = float(max(0.0, min(1.0,
        0.7 * element_avg
        + 0.2 * (1.0 - unprofessional_penalty)
        + 0.1 * (1.0 + structure_bonus)
    )))

    # ── Explanation ───────────────────────────────────────────────────────
    missing = [k for k, v in element_scores.items() if v == 0.0]

    if score >= 0.85:
        explanation = (
            f"Highly professional email (score={score:.2f}). "
            "Contains proper salutation, action statement, and closing."
        )
    elif score >= 0.65:
        explanation = (
            f"Professional response (score={score:.2f}). "
            f"Most business email elements present."
        )
        if missing:
            explanation += f" Missing: {', '.join(missing)}."
    elif score >= 0.45:
        explanation = (
            f"Partially professional (score={score:.2f}). "
            f"Missing elements: {', '.join(missing) or 'none'}. "
        )
        if unprofessional_hits:
            explanation += f"Informal language detected: {', '.join(unprofessional_hits[:2])}."
    else:
        explanation = (
            f"Unprofessional response (score={score:.2f}). "
            f"Missing: {', '.join(missing)}. "
            f"Informal signals: {', '.join(unprofessional_hits[:3])}."
        )

    return ProfessionalismResult(
        score=score,
        explanation=explanation,
        details={
            "element_scores": element_scores,
            "unprofessional_signals": unprofessional_hits[:5],
            "paragraph_count": paragraph_count,
            "has_structure": has_good_structure,
        },
    )
