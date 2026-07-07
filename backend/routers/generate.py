"""
Generation router — triggers the full RAG pipeline.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.generator.pipeline import get_pipeline
from backend.schemas.email import GenerateRequest, GenerateResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/generate", tags=["generation"])


@router.post("/", response_model=GenerateResponse, status_code=status.HTTP_200_OK)
async def generate_response(
    request: GenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    """
    Generate an AI email response using the RAG pipeline.

    Pipeline:
    1. Embed incoming email
    2. Retrieve top-k similar historical emails via FAISS
    3. Build few-shot prompt with retrieved context
    4. Generate response via Gemini (or fallback)
    5. Persist generated response to database
    6. Return structured response with provenance
    """
    try:
        pipeline = get_pipeline()
        result = await pipeline.run(request, db)
        logger.info("Generation complete: response_id=%d", result.response_id)
        return result
    except Exception as e:
        logger.exception("Generation pipeline failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}",
        )
