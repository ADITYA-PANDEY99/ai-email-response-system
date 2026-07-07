# backend/models/__init__.py
from backend.models.email import Email, GeneratedResponse
from backend.models.evaluation import EvaluationResult

__all__ = ["Email", "GeneratedResponse", "EvaluationResult"]
