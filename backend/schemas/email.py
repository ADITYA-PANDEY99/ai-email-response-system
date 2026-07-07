"""
Pydantic schemas for email-related API requests and responses.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EmailBase(BaseModel):
    subject: str = Field(..., min_length=1, max_length=500)
    sender: str = Field(..., min_length=1)
    recipient: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    ideal_reply: str = Field(..., min_length=1)
    intent: str
    tone: str
    priority: str
    entities: dict[str, Any] = Field(default_factory=dict)
    expected_actions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    category: str


class EmailCreate(EmailBase):
    pass


class EmailRead(EmailBase):
    id: int
    embedding_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmailListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[EmailRead]


class GenerateRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=10, description="Incoming email body")
    sender: str = Field(default="customer@example.com")
    top_k: int = Field(default=5, ge=1, le=10)
    reference_reply: str | None = Field(default=None, description="Ground truth for evaluation")


class RetrievedEmail(BaseModel):
    id: int
    subject: str
    body: str
    ideal_reply: str
    intent: str
    tone: str
    category: str
    similarity_score: float
    retrieval_reason: str = Field(default="")


class GenerateResponse(BaseModel):
    response_id: int
    generated_reply: str
    model_used: str
    retrieved_emails: list[RetrievedEmail]
    prompt_tokens: int
    completion_tokens: int
    generation_time_ms: float
