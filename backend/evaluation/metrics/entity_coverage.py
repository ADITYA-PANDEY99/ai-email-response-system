"""
Metric 6: Entity Coverage

Checks that important entities from the incoming email (order numbers,
product names, dates, customer names) appear in the generated response.

Missing entities are a form of hallucination-by-omission — the response
ignores specific details the customer mentioned.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class EntityCoverageResult:
    score: float
    explanation: str
    details: dict


def _extract_entities_from_text(text: str) -> set[str]:
    """Heuristic entity extraction when no structured entities available."""
    entities: set[str] = set()

    # Order numbers / IDs (ORD-12345, #12345, order 12345)
    entities.update(re.findall(r"\b(?:ORD|INV|TKT|REF|CASE)[-#]?\d{4,}\b", text, re.IGNORECASE))
    entities.update(re.findall(r"#\d{4,}", text))

    # Dates
    entities.update(re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text))
    entities.update(re.findall(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b",
        text, re.IGNORECASE
    ))

    # Dollar amounts
    entities.update(re.findall(r"\$\d+(?:\.\d{2})?", text))

    # Email addresses
    entities.update(re.findall(r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b", text, re.IGNORECASE))

    return {e.strip() for e in entities if e.strip()}


def compute(
    generated: str,
    incoming_email: str,
    entities: dict | None = None,
) -> EntityCoverageResult:
    """
    Compute entity coverage score.

    If structured entities dict is provided (from dataset), use it directly.
    Otherwise, extract heuristically from the incoming email.
    """
    # ── Extract entities ───────────────────────────────────────────────────
    if entities:
        # Flatten structured entities dict → list of string values
        all_entity_values: list[str] = []
        for v in entities.values():
            if isinstance(v, list):
                all_entity_values.extend([str(x) for x in v])
            elif isinstance(v, str) and v:
                all_entity_values.append(v)
        entity_set = set(all_entity_values)
    else:
        entity_set = _extract_entities_from_text(incoming_email)

    if not entity_set:
        return EntityCoverageResult(
            score=0.75,
            explanation="No specific entities detected in the email; baseline score applied.",
            details={"entities_found": [], "covered": [], "uncovered": []},
        )

    gen_lower = generated.lower()
    covered = [e for e in entity_set if e.lower() in gen_lower]
    uncovered = [e for e in entity_set if e.lower() not in gen_lower]

    coverage_rate = len(covered) / len(entity_set)
    score = float(max(0.0, min(1.0, coverage_rate)))

    if score >= 0.90:
        explanation = (
            f"Excellent entity coverage (score={score:.2f}). "
            f"All key entities from the customer email are acknowledged: {', '.join(covered[:4])}."
        )
    elif score >= 0.65:
        explanation = (
            f"Good entity coverage (score={score:.2f}). "
            f"Most entities referenced. Missing: {', '.join(uncovered[:3])}."
        )
    elif score >= 0.40:
        explanation = (
            f"Partial entity coverage (score={score:.2f}). "
            f"Only {len(covered)}/{len(entity_set)} entities mentioned. "
            f"Response may feel generic."
        )
    else:
        explanation = (
            f"Poor entity coverage (score={score:.2f}). "
            "Critical customer-specific entities are absent. "
            f"Missing: {', '.join(uncovered[:5])}."
        )

    return EntityCoverageResult(
        score=score,
        explanation=explanation,
        details={
            "entities_found": list(entity_set),
            "covered": covered,
            "uncovered": uncovered,
            "coverage_rate": coverage_rate,
        },
    )
