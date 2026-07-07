"""
ORM models for emails and generated responses.
"""
from __future__ import annotations

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Email(Base):
    """Represents an email in the training/reference dataset."""

    __tablename__ = "emails"

    subject: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    ideal_reply: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tone: Mapped[str] = mapped_column(String(50), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    entities: Mapped[dict] = mapped_column(JSON, default=dict)
    expected_actions: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    embedding_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    generated_responses: Mapped[list["GeneratedResponse"]] = relationship(
        back_populates="source_email", cascade="all, delete-orphan"
    )


class GeneratedResponse(Base):
    """Stores a generated response and its evaluation result."""

    __tablename__ = "generated_responses"

    email_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("emails.id", ondelete="SET NULL"), nullable=True
    )
    incoming_email: Mapped[str] = mapped_column(Text, nullable=False)
    incoming_subject: Mapped[str] = mapped_column(String(500), nullable=False)
    generated_reply: Mapped[str] = mapped_column(Text, nullable=False)
    reference_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    retrieval_ids: Mapped[list] = mapped_column(JSON, default=list)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    generation_time_ms: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    source_email: Mapped["Email | None"] = relationship(back_populates="generated_responses")
    evaluation: Mapped["EvaluationResult | None"] = relationship(
        back_populates="response", uselist=False, cascade="all, delete-orphan"
    )
