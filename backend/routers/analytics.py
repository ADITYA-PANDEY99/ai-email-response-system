"""
Analytics router — aggregated metrics for the dashboard.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.email import Email, GeneratedResponse
from backend.models.evaluation import EvaluationResult

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db)) -> dict:
    """High-level overview stats for the home dashboard."""
    email_count = (await db.execute(select(func.count(Email.id)))).scalar_one()
    gen_count = (await db.execute(select(func.count(GeneratedResponse.id)))).scalar_one()
    eval_count = (await db.execute(select(func.count(EvaluationResult.id)))).scalar_one()

    avg_score_result = await db.execute(select(func.avg(EvaluationResult.overall_score)))
    avg_score = avg_score_result.scalar_one()

    avg_safety_result = await db.execute(select(func.avg(EvaluationResult.safety)))
    avg_safety = avg_safety_result.scalar_one()

    return {
        "total_emails": email_count,
        "total_generated": gen_count,
        "total_evaluated": eval_count,
        "average_score": round(avg_score or 0.0, 3),
        "average_safety": round(avg_safety or 0.0, 3),
    }


@router.get("/score-distribution")
async def get_score_distribution(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Score distribution bucketed by 10% ranges."""
    stmt = select(EvaluationResult.overall_score)
    result = await db.execute(stmt)
    scores = [row[0] for row in result.fetchall()]

    buckets = {f"{i*10}-{i*10+10}%": 0 for i in range(10)}
    for s in scores:
        bucket_idx = min(int(s * 10), 9)
        label = f"{bucket_idx*10}-{bucket_idx*10+10}%"
        buckets[label] = buckets.get(label, 0) + 1

    return [{"range": k, "count": v} for k, v in buckets.items()]


@router.get("/metric-radar")
async def get_metric_radar(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Average scores for each metric — suitable for a radar chart."""
    stmt = select(EvaluationResult)
    result = await db.execute(stmt)
    evals = result.scalars().all()

    if not evals:
        return []

    n = len(evals)
    return [
        {"metric": "Semantic Similarity", "score": round(sum(e.semantic_similarity for e in evals) / n, 3)},
        {"metric": "Intent Match", "score": round(sum(e.intent_match for e in evals) / n, 3)},
        {"metric": "Completeness", "score": round(sum(e.completeness for e in evals) / n, 3)},
        {"metric": "Tone Match", "score": round(sum(e.tone_match for e in evals) / n, 3)},
        {"metric": "Action Coverage", "score": round(sum(e.action_coverage for e in evals) / n, 3)},
        {"metric": "Safety", "score": round(sum(e.safety for e in evals) / n, 3)},
        {"metric": "Grammar", "score": round(sum(e.grammar_quality for e in evals) / n, 3)},
        {"metric": "Professionalism", "score": round(sum(e.professionalism for e in evals) / n, 3)},
        {"metric": "Hallucination", "score": round(sum(e.hallucination_score for e in evals) / n, 3)},
        {"metric": "Entity Coverage", "score": round(sum(e.entity_coverage for e in evals) / n, 3)},
    ]


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Recent generate + evaluate activity."""
    stmt = (
        select(GeneratedResponse, EvaluationResult)
        .outerjoin(EvaluationResult, GeneratedResponse.id == EvaluationResult.response_id)
        .order_by(GeneratedResponse.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.fetchall()

    return [
        {
            "response_id": gr.id,
            "subject": gr.incoming_subject,
            "model": gr.model_used,
            "overall_score": ev.overall_score if ev else None,
            "traffic_light": ev.traffic_light if ev else None,
            "generated_at": gr.created_at.isoformat(),
        }
        for gr, ev in rows
    ]
