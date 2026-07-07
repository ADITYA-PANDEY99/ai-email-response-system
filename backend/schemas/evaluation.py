"""
Pydantic schemas for evaluation API.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MetricScore(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    weight: float = Field(..., ge=0.0, le=1.0)
    weighted_contribution: float
    explanation: str
    why_lost_points: str | None = Field(default=None)
    how_to_improve: str | None = Field(default=None)
    details: dict = Field(default_factory=dict)


class EvaluationRequest(BaseModel):
    response_id: int
    generated_reply: str
    reference_reply: str | None = None
    incoming_email: str
    incoming_subject: str
    intent: str | None = None
    tone: str | None = None
    expected_actions: list[str] = Field(default_factory=list)
    entities: dict = Field(default_factory=dict)
    retrieval_ids: list[int] = Field(default_factory=list)


class MetricBreakdown(BaseModel):
    semantic_similarity: MetricScore
    intent_match: MetricScore
    completeness: MetricScore
    tone_match: MetricScore
    action_coverage: MetricScore
    safety: MetricScore
    grammar_quality: MetricScore
    professionalism: MetricScore
    length_penalty: MetricScore
    hallucination_score: MetricScore
    entity_coverage: MetricScore
    retrieval_consistency: MetricScore


class EvaluationResponse(BaseModel):
    evaluation_id: int
    response_id: int
    overall_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    traffic_light: str  # "green" | "amber" | "red"
    grade: str  # "A" | "B" | "C" | "D" | "F"
    metric_breakdown: MetricBreakdown
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    executive_summary: str = Field(default="")
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemEvalSummary(BaseModel):
    total_evaluations: int
    average_score: float
    score_distribution: dict[str, int]  # grade → count
    metric_averages: dict[str, float]
    top_performers: list[dict]
    low_performers: list[dict]
    improvement_trend: list[dict]
