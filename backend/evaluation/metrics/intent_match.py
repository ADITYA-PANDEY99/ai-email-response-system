"""
Metric 2: Intent Match (weight=0.20)

Verifies that the generated response actually addresses the same
customer intent as the reference (e.g. refund request → refund resolution).

Method: NLI-style keyword + semantic matching against intent taxonomy.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import numpy as np

from backend.retrieval.embedder import get_embedder

# Intent taxonomy: each intent maps to representative phrases
INTENT_SIGNALS: dict[str, list[str]] = {
    "refund": [
        "process your refund", "refund your payment", "return the amount",
        "money back", "reimburse", "refund processed", "credit back"
    ],
    "shipping": [
        "tracking number", "your order has shipped", "estimated delivery",
        "shipment", "dispatched", "out for delivery", "package"
    ],
    "billing": [
        "billing team", "invoice", "payment adjusted", "charge corrected",
        "account statement", "billing error", "subscription charge"
    ],
    "technical_support": [
        "technical team", "engineering team", "bug fix", "issue resolved",
        "workaround", "error investigated", "patch released", "ticket"
    ],
    "password_reset": [
        "reset link", "password reset", "account recovery",
        "verification email", "secure link", "update your password"
    ],
    "cancellation": [
        "subscription cancelled", "account closed", "cancel confirmed",
        "cancellation processed", "effective date"
    ],
    "account_access": [
        "account access restored", "login issue", "account unlocked",
        "access granted", "authentication"
    ],
    "complaint": [
        "sincerely apologize", "deeply sorry", "escalate", "make it right",
        "compensation", "resolve your concern"
    ],
    "feature_request": [
        "passed to product team", "feature request noted", "roadmap",
        "development team", "future update", "considered for"
    ],
    "pricing": [
        "pricing details", "current plan", "discount", "promotion",
        "quote", "pricing tier", "upgrade"
    ],
    "sales": [
        "solution", "demo", "schedule a call", "our product",
        "enterprise plan", "get started"
    ],
    "positive_feedback": [
        "thank you for your kind", "wonderful feedback", "delighted",
        "share with team", "your support means"
    ],
}

GENERIC_RESOLUTION_SIGNALS = [
    "thank you", "reach out", "happy to help", "best regards",
    "contact us", "our team", "business days"
]


@dataclass
class IntentMatchResult:
    score: float
    explanation: str
    details: dict


def compute(
    generated: str,
    reference: str,
    declared_intent: str | None = None,
) -> IntentMatchResult:
    """
    Compute intent match score.

    1. If reference is available: measure semantic proximity of response themes.
    2. If declared_intent is given: check for intent-specific resolution signals.
    3. Baseline: check for general resolution language.
    """
    gen_lower = generated.lower()
    ref_lower = (reference or "").lower()

    # ── Method 1: Semantic similarity to reference (primary) ──────────────
    if reference and reference.strip():
        embedder = get_embedder()
        # Compare only first 200 chars (intent is frontloaded)
        vec_gen = embedder.embed_text(generated[:500])
        vec_ref = embedder.embed_text(reference[:500])
        semantic_sim = float(np.clip(np.dot(vec_gen, vec_ref), 0, 1))
    else:
        semantic_sim = None

    # ── Method 2: Intent-specific keyword signals ─────────────────────────
    intent_signal_score = 0.0
    matched_signals: list[str] = []

    if declared_intent:
        canonical_intent = _normalize_intent(declared_intent)
        signals = INTENT_SIGNALS.get(canonical_intent, [])
        if signals:
            matches = [s for s in signals if s in gen_lower]
            matched_signals = matches
            intent_signal_score = min(1.0, len(matches) / max(3, len(signals) * 0.4))

    # ── Method 3: Generic resolution language ────────────────────────────
    generic_matches = sum(1 for s in GENERIC_RESOLUTION_SIGNALS if s in gen_lower)
    generic_score = min(1.0, generic_matches / 4.0)

    # ── Aggregate ─────────────────────────────────────────────────────────
    if semantic_sim is not None and intent_signal_score > 0:
        score = 0.6 * semantic_sim + 0.3 * intent_signal_score + 0.1 * generic_score
    elif semantic_sim is not None:
        score = 0.7 * semantic_sim + 0.3 * generic_score
    elif intent_signal_score > 0:
        score = 0.6 * intent_signal_score + 0.4 * generic_score
    else:
        score = generic_score * 0.7

    score = float(np.clip(score, 0.0, 1.0))

    # ── Explanation ───────────────────────────────────────────────────────
    if score >= 0.85:
        explanation = (
            f"Strong intent match (score={score:.2f}). The response correctly addresses "
            f"the customer's {declared_intent or 'stated'} intent with appropriate resolution language."
        )
    elif score >= 0.65:
        explanation = (
            f"Good intent alignment (score={score:.2f}). The response addresses the intent "
            f"but could be more specifically targeted to {declared_intent or 'the request'}."
        )
    elif score >= 0.45:
        explanation = (
            f"Partial intent match (score={score:.2f}). The response includes some relevant "
            "language but may not fully resolve the customer's specific concern."
        )
    else:
        explanation = (
            f"Weak intent match (score={score:.2f}). The response lacks intent-specific "
            "resolution language and may leave the customer's concern unaddressed."
        )

    if matched_signals:
        explanation += f" Detected signals: {', '.join(matched_signals[:3])}."

    return IntentMatchResult(
        score=score,
        explanation=explanation,
        details={
            "semantic_similarity": semantic_sim,
            "intent_signal_score": intent_signal_score,
            "generic_score": generic_score,
            "matched_signals": matched_signals,
            "declared_intent": declared_intent,
        },
    )


def _normalize_intent(intent: str) -> str:
    """Normalize intent string to match taxonomy keys."""
    intent = intent.lower().replace(" ", "_").replace("-", "_")
    # Fuzzy match
    for key in INTENT_SIGNALS:
        if key in intent or intent in key:
            return key
    return intent
