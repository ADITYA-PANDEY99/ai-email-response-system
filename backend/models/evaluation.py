"""
ORM model for evaluation results.
"""
from __future__ import annotations

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class EvaluationResult(Base):
    """Stores the full evaluation breakdown for a generated response."""

    __tablename__ = "evaluation_results"

    response_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("generated_responses.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Aggregate scores
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    traffic_light: Mapped[str] = mapped_column(String(10), nullable=False)  # green/amber/red

    # Individual metric scores (0.0 – 1.0)
    semantic_similarity: Mapped[float] = mapped_column(Float, nullable=False)
    intent_match: Mapped[float] = mapped_column(Float, nullable=False)
    completeness: Mapped[float] = mapped_column(Float, nullable=False)
    tone_match: Mapped[float] = mapped_column(Float, nullable=False)
    action_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    safety: Mapped[float] = mapped_column(Float, nullable=False)
    grammar_quality: Mapped[float] = mapped_column(Float, nullable=False)
    professionalism: Mapped[float] = mapped_column(Float, nullable=False)
    length_penalty: Mapped[float] = mapped_column(Float, nullable=False)
    hallucination_score: Mapped[float] = mapped_column(Float, nullable=False)
    entity_coverage: Mapped[float] = mapped_column(Float, nullable=False)
    retrieval_consistency: Mapped[float] = mapped_column(Float, nullable=False)

    # Explanations (JSON list of strings)
    metric_explanations: Mapped[dict] = mapped_column(JSON, default=dict)

    # Narrative
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    recommendations: Mapped[list] = mapped_column(JSON, default=list)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=True)

    # Relationship
    response: Mapped["GeneratedResponse"] = relationship(back_populates="evaluation")  # type: ignore[name-defined]
