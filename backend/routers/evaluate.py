"""
Evaluation router — triggers the multi-metric evaluation engine.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.evaluation.engine import get_engine
from backend.models.email import GeneratedResponse
from backend.models.evaluation import EvaluationResult
from backend.retrieval.faiss_store import get_faiss_store
from backend.schemas.evaluation import EvaluationRequest, EvaluationResponse, SystemEvalSummary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/evaluate", tags=["evaluation"])


@router.post("/", response_model=EvaluationResponse, status_code=status.HTTP_200_OK)
async def evaluate_response(
    request: EvaluationRequest,
    db: AsyncSession = Depends(get_db),
) -> EvaluationResponse:
    """
    Run the multi-metric evaluation engine on a generated response.

    Returns comprehensive scoring with per-metric explanations.
    """
    # Fetch retrieved replies for consistency check
    gen_response = await db.get(GeneratedResponse, request.response_id)
    retrieved_replies: list[str] = []

    if gen_response and gen_response.retrieval_ids:
        from backend.models.email import Email
        from sqlalchemy import select as sel
        stmt = sel(Email.ideal_reply).where(Email.id.in_(gen_response.retrieval_ids))
        result = await db.execute(stmt)
        retrieved_replies = [row[0] for row in result.fetchall()]

    try:
        engine = get_engine()
        evaluation = await engine.evaluate(request, db, retrieved_replies)
        logger.info(
            "Evaluation complete: response_id=%d score=%.3f",
            request.response_id,
            evaluation.overall_score,
        )
        return evaluation
    except Exception as e:
        logger.exception("Evaluation engine failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )


@router.get("/history", response_model=list[dict])
async def get_evaluation_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return recent evaluations with scores."""
    stmt = (
        select(EvaluationResult)
        .order_by(EvaluationResult.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    evaluations = result.scalars().all()

    return [
        {
            "id": e.id,
            "response_id": e.response_id,
            "overall_score": e.overall_score,
            "confidence": e.confidence,
            "traffic_light": e.traffic_light,
            "semantic_similarity": e.semantic_similarity,
            "intent_match": e.intent_match,
            "completeness": e.completeness,
            "safety": e.safety,
            "created_at": e.created_at.isoformat(),
        }
        for e in evaluations
    ]


@router.get("/summary", response_model=SystemEvalSummary)
async def get_system_summary(db: AsyncSession = Depends(get_db)) -> SystemEvalSummary:
    """Return aggregate system evaluation statistics."""
    stmt = select(EvaluationResult)
    result = await db.execute(stmt)
    all_evals = result.scalars().all()

    if not all_evals:
        return SystemEvalSummary(
            total_evaluations=0,
            average_score=0.0,
            score_distribution={"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
            metric_averages={},
            top_performers=[],
            low_performers=[],
            improvement_trend=[],
        )

    scores = [e.overall_score for e in all_evals]
    avg_score = sum(scores) / len(scores)

    def grade(s: float) -> str:
        if s >= 0.90: return "A"
        if s >= 0.80: return "B"
        if s >= 0.70: return "C"
        if s >= 0.55: return "D"
        return "F"

    distribution: dict[str, int] = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    for e in all_evals:
        distribution[grade(e.overall_score)] += 1

    metrics = ["semantic_similarity", "intent_match", "completeness", "tone_match",
               "action_coverage", "safety", "grammar_quality", "professionalism"]
    metric_avgs = {
        m: round(sum(getattr(e, m) for e in all_evals) / len(all_evals), 3)
        for m in metrics
    }

    sorted_evals = sorted(all_evals, key=lambda e: e.overall_score, reverse=True)
    top = [{"id": e.id, "score": e.overall_score, "traffic": e.traffic_light} for e in sorted_evals[:5]]
    low = [{"id": e.id, "score": e.overall_score, "traffic": e.traffic_light} for e in sorted_evals[-5:]]

    # Trend: last 20 evaluations in chronological order
    recent = sorted(all_evals, key=lambda e: e.created_at)[-20:]
    trend = [{"date": e.created_at.isoformat(), "score": e.overall_score} for e in recent]

    return SystemEvalSummary(
        total_evaluations=len(all_evals),
        average_score=round(avg_score, 3),
        score_distribution=distribution,
        metric_averages=metric_avgs,
        top_performers=top,
        low_performers=low,
        improvement_trend=trend,
    )


@router.get("/{evaluation_id}", response_model=dict)
async def get_evaluation(
    evaluation_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get a specific evaluation result by ID."""
    ev = await db.get(EvaluationResult, evaluation_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return {
        "id": ev.id,
        "response_id": ev.response_id,
        "overall_score": ev.overall_score,
        "confidence": ev.confidence,
        "traffic_light": ev.traffic_light,
        "semantic_similarity": ev.semantic_similarity,
        "intent_match": ev.intent_match,
        "completeness": ev.completeness,
        "tone_match": ev.tone_match,
        "action_coverage": ev.action_coverage,
        "safety": ev.safety,
        "grammar_quality": ev.grammar_quality,
        "professionalism": ev.professionalism,
        "length_penalty": ev.length_penalty,
        "hallucination_score": ev.hallucination_score,
        "entity_coverage": ev.entity_coverage,
        "retrieval_consistency": ev.retrieval_consistency,
        "metric_explanations": ev.metric_explanations,
        "strengths": ev.strengths,
        "weaknesses": ev.weaknesses,
        "recommendations": ev.recommendations,
        "executive_summary": ev.executive_summary,
        "created_at": ev.created_at.isoformat(),
    }
