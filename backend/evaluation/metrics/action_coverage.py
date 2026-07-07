"""
Metric 5: Action Coverage (weight=0.10)

Checks whether the generated response covers all expected actions
defined in the dataset (e.g., "process refund", "send tracking info").

This is critical: a response can sound great but fail to actually
commit to the required actions.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from backend.retrieval.embedder import get_embedder


@dataclass
class ActionCoverageResult:
    score: float
    explanation: str
    details: dict


def compute(
    generated: str,
    expected_actions: list[str],
) -> ActionCoverageResult:
    """
    Compute action coverage score.

    For each expected action, check if the generated response
    semantically addresses it (cosine similarity > threshold).
    """
    if not expected_actions:
        return ActionCoverageResult(
            score=0.80,  # generous default when no actions defined
            explanation="No expected actions defined; baseline score applied.",
            details={"expected_actions": [], "covered": [], "uncovered": []},
        )

    embedder = get_embedder()
    threshold = 0.50
    vec_gen = embedder.embed_text(generated[:1000])

    covered: list[str] = []
    uncovered: list[str] = []
    action_scores: dict[str, float] = {}

    for action in expected_actions:
        vec_action = embedder.embed_text(action)
        sim = float(np.clip(np.dot(vec_action, vec_gen), 0, 1))
        action_scores[action] = sim
        if sim >= threshold:
            covered.append(action)
        else:
            uncovered.append(action)

    coverage_rate = len(covered) / len(expected_actions)
    score = float(np.clip(coverage_rate, 0.0, 1.0))

    # Partial credit: average similarity for uncovered actions
    if uncovered and action_scores:
        avg_uncovered_sim = np.mean([action_scores[a] for a in uncovered])
        partial_credit = float(avg_uncovered_sim) * 0.3
        score = min(1.0, score + partial_credit * (1 - coverage_rate))

    if score >= 0.90:
        explanation = (
            f"All expected actions covered (score={score:.2f}). "
            f"Covered: {', '.join(covered[:3])}."
        )
    elif score >= 0.70:
        explanation = (
            f"Most actions covered (score={score:.2f}). "
            f"Covered {len(covered)}/{len(expected_actions)} actions. "
            f"Missing: {', '.join(uncovered[:2])}."
        )
    elif score >= 0.40:
        explanation = (
            f"Partial action coverage (score={score:.2f}). "
            f"Only {len(covered)}/{len(expected_actions)} expected actions addressed. "
            f"Not addressed: {', '.join(uncovered[:3])}."
        )
    else:
        explanation = (
            f"Poor action coverage (score={score:.2f}). "
            f"The response fails to commit to most required actions. "
            f"Missing: {', '.join(uncovered[:5])}."
        )

    return ActionCoverageResult(
        score=score,
        explanation=explanation,
        details={
            "expected_actions": expected_actions,
            "covered": covered,
            "uncovered": uncovered,
            "action_scores": action_scores,
            "coverage_rate": coverage_rate,
        },
    )
