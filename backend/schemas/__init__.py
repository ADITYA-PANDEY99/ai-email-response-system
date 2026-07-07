# backend/schemas/__init__.py
from backend.schemas.email import (
    EmailCreate,
    EmailListResponse,
    EmailRead,
    GenerateRequest,
    GenerateResponse,
    RetrievedEmail,
)
from backend.schemas.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    MetricBreakdown,
    MetricScore,
    SystemEvalSummary,
)

__all__ = [
    "EmailCreate",
    "EmailRead",
    "EmailListResponse",
    "GenerateRequest",
    "GenerateResponse",
    "RetrievedEmail",
    "EvaluationRequest",
    "EvaluationResponse",
    "MetricBreakdown",
    "MetricScore",
    "SystemEvalSummary",
]
