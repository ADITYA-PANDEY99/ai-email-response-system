"""
Metric 7: Hallucination Detection

Detects factual claims in the generated response that are NOT
supported by the incoming email or retrieved context.

Hallucination types detected:
1. Invented timelines ("within 24 hours" when no SLA was discussed)
2. Fabricated reference numbers ("Ticket #XYZ-001" out of thin air)
3. Unsupported product/policy claims
4. False confirmations ("Your refund has been processed" without authority)

Method: cross-check generated claims against source documents.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

from backend.retrieval.embedder import get_embedder

# High-risk claim patterns that should be grounded in source material
HALLUCINATION_RISK_PATTERNS = [
    (r"\$[\d,]+(?:\.\d{2})?", "specific dollar amounts"),
    (r"\b\d+\s*(?:business\s+)?days?\b", "specific timelines"),
    (r"\b(?:ORD|INV|TKT|REF|CASE|TICKET)[-#]?\s*\d+\b", "reference numbers"),
    (r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", "specific dates"),
    (r"\bversion\s+[\d.]+\b", "software versions"),
    (r"\b\d+%\s*(?:off|discount|refund)\b", "percentage discounts"),
    (r"\bguar(?:antee|anteed)\b", "guarantee claims"),
    (r"\bfull(?:y)?\s+refund\b", "full refund claims"),
]


@dataclass
class HallucinationResult:
    score: float  # High score = low hallucination (score inverted: 1=good)
    explanation: str
    details: dict


def compute(
    generated: str,
    incoming_email: str,
    reference: str | None = None,
    retrieved_contexts: list[str] | None = None,
) -> HallucinationResult:
    """
    Compute hallucination score.

    Score: 1.0 = no hallucination detected, 0.0 = high hallucination risk.

    Method:
    1. Extract high-risk claims from generated text.
    2. Verify each claim appears in source material (email + reference + retrieved).
    3. Penalise ungrounded claims proportionally.
    4. Also measure semantic grounding: generated should be inferable from sources.
    """
    source_text = incoming_email
    if reference:
        source_text += " " + reference
    if retrieved_contexts:
        source_text += " " + " ".join(retrieved_contexts[:3])

    source_lower = source_text.lower()
    gen_lower = generated.lower()

    # ── Step 1: Check high-risk claims ───────────────────────────────────
    risk_claims: list[dict] = []
    unsupported_count = 0
    hallucination_flags = {
        "invented_refund_policies": [],
        "wrong_dates": [],
        "imaginary_discounts": [],
        "unsupported_promises": [],
        "missing_customer_context": []
    }

    # Extract dates to compare them
    src_dates = set(re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", source_text))
    src_dates.update(re.findall(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s+\d{4})?\b", source_text))

    for pattern, claim_type in HALLUCINATION_RISK_PATTERNS:
        gen_matches = re.findall(pattern, generated, re.IGNORECASE)
        src_matches = re.findall(pattern, source_text, re.IGNORECASE)

        for match in gen_matches:
            is_grounded = match.lower() in source_lower
            
            # Sub-type checks
            m_lower = match.lower()
            if claim_type == "full refund claims" or "refund" in m_lower:
                if not is_grounded:
                    hallucination_flags["invented_refund_policies"].append(match)
            elif claim_type == "specific dates" or any(month in m_lower for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                # If date is not grounded in source dates
                if not any(match.lower() in s.lower() or s.lower() in match.lower() for s in src_dates):
                    hallucination_flags["wrong_dates"].append(match)
            elif claim_type == "percentage discounts" or "discount" in m_lower or "free" in m_lower:
                if not is_grounded:
                    hallucination_flags["imaginary_discounts"].append(match)
            elif claim_type == "guarantee claims" or "promise" in m_lower or "guarantee" in m_lower:
                if not is_grounded:
                    hallucination_flags["unsupported_promises"].append(match)

            risk_claims.append({
                "value": match,
                "type": claim_type,
                "grounded": is_grounded,
            })
            if not is_grounded:
                unsupported_count += 1

    # Check for missing customer context
    # If the incoming email has a name/identity, but we address them with generic placeholders
    src_names = re.findall(r"\b(?:Regards|Sincerely|Thanks|Best),\s*\n*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b", source_text)
    if src_names:
        first_name = src_names[0].split()[0]
        if first_name.lower() not in gen_lower and ("valued customer" in gen_lower or "customer support" in gen_lower):
            hallucination_flags["missing_customer_context"].append(f"Generic greeting used despite name '{src_names[0]}' being present.")
            unsupported_count += 1

    # ── Step 2: Semantic grounding check ─────────────────────────────────
    embedder = get_embedder()
    vec_gen = embedder.embed_text(generated[:600])
    vec_src = embedder.embed_text(source_text[:800])
    semantic_grounding = float(np.clip(np.dot(vec_gen, vec_src), 0, 1))

    # ── Step 3: Aggregate score ───────────────────────────────────────────
    total_claims = max(len(risk_claims), 1)
    grounding_rate = 1.0 - (unsupported_count / total_claims)

    score = float(np.clip(0.6 * grounding_rate + 0.4 * semantic_grounding, 0.0, 1.0))

    # ── Step 4: Explanation ───────────────────────────────────────────────
    ungrounded_claims = [c for c in risk_claims if not c["grounded"]]
    grounded_claims = [c for c in risk_claims if c["grounded"]]

    if score >= 0.90:
        explanation = (
            f"Low hallucination risk (score={score:.2f}). "
            "Generated claims are well-grounded in the source material."
        )
    elif score >= 0.70:
        explanation = (
            f"Moderate hallucination risk (score={score:.2f}). "
            f"{unsupported_count} ungrounded claim(s) detected."
        )
        if ungrounded_claims:
            examples = [f"'{c['value']}' ({c['type']})" for c in ungrounded_claims[:2]]
            explanation += f" Examples: {'; '.join(examples)}."
    elif score >= 0.50:
        explanation = (
            f"Elevated hallucination risk (score={score:.2f}). "
            f"Multiple ungrounded claims: {unsupported_count} specific values "
            "not found in source material."
        )
    else:
        explanation = (
            f"High hallucination risk (score={score:.2f}). "
            "The response contains numerous claims unsupported by the email context. "
            "This response should not be sent without human review."
        )

    return HallucinationResult(
        score=score,
        explanation=explanation,
        details={
            "total_risk_claims": len(risk_claims),
            "grounded_claims": len(grounded_claims),
            "unsupported_claims": unsupported_count,
            "ungrounded_examples": [c["value"] for c in ungrounded_claims[:5]],
            "semantic_grounding": semantic_grounding,
            "grounding_rate": grounding_rate,
            "hallucination_flags": hallucination_flags,
        },
    )
