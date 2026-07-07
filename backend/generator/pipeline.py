"""
End-to-end generation pipeline: Retrieve → Prompt → Generate → Persist.
"""
from __future__ import annotations

import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from backend.generator.llm_client import get_llm_client
from backend.generator.prompt_builder import build_fallback_prompt, build_prompt
from backend.models.email import GeneratedResponse
from backend.retrieval.retriever import get_retriever
from backend.schemas.email import GenerateRequest, GenerateResponse, RetrievedEmail

logger = logging.getLogger(__name__)


class GenerationPipeline:
    """
    Orchestrates the full RAG-based generation pipeline:

    1. Retrieve: Find top-k similar emails from FAISS index
    2. Build Prompt: Construct few-shot prompt with retrieved context
    3. Generate: Call LLM (Gemini or fallback)
    4. Persist: Store response in database
    5. Return: Structured response with provenance
    """

    def __init__(self) -> None:
        self._retriever = get_retriever()
        self._llm = get_llm_client()

    async def run(
        self,
        request: GenerateRequest,
        db: AsyncSession,
    ) -> GenerateResponse:
        """Execute the full generation pipeline."""
        t0 = time.monotonic()

        # ── Step 1: Retrieve similar emails ──────────────────────────────────
        retrieved: list[RetrievedEmail] = await self._retriever.retrieve(
            subject=request.subject,
            body=request.body,
            db=db,
            top_k=request.top_k,
        )
        logger.info("Retrieved %d similar emails", len(retrieved))

        # ── Step 2: Build prompt ──────────────────────────────────────────────
        if retrieved:
            prompt = build_prompt(
                subject=request.subject,
                body=request.body,
                sender=request.sender,
                retrieved_emails=retrieved,
            )
        else:
            logger.warning("No retrieved emails — using minimal prompt")
            prompt = build_fallback_prompt(
                subject=request.subject,
                body=request.body,
                sender=request.sender,
            )

        # ── Step 3: Generate ──────────────────────────────────────────────────
        llm_response = await self._llm.generate(prompt, email_body=request.body)
        generation_time_ms = (time.monotonic() - t0) * 1000

        # ── Step 4: Persist ───────────────────────────────────────────────────
        db_obj = GeneratedResponse(
            incoming_email=request.body,
            incoming_subject=request.subject,
            generated_reply=llm_response.text,
            reference_reply=request.reference_reply,
            model_used=llm_response.model,
            retrieval_ids=[r.id for r in retrieved],
            prompt_tokens=llm_response.prompt_tokens,
            completion_tokens=llm_response.completion_tokens,
            generation_time_ms=generation_time_ms,
        )
        db.add(db_obj)
        await db.flush()  # get ID without committing
        response_id = db_obj.id

        logger.info(
            "Generated response id=%d in %.0fms using %s",
            response_id,
            generation_time_ms,
            llm_response.model,
        )

        # ── Step 5: Return ────────────────────────────────────────────────────
        return GenerateResponse(
            response_id=response_id,
            generated_reply=llm_response.text,
            model_used=llm_response.model,
            retrieved_emails=retrieved,
            prompt_tokens=llm_response.prompt_tokens,
            completion_tokens=llm_response.completion_tokens,
            generation_time_ms=generation_time_ms,
        )


_pipeline: GenerationPipeline | None = None


def get_pipeline() -> GenerationPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = GenerationPipeline()
    return _pipeline
