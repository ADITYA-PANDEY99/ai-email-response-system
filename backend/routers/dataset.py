"""
Dataset management router — seed, rebuild FAISS, and export.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.database import get_db
from backend.models.email import Email
from backend.retrieval.faiss_store import get_faiss_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dataset", tags=["dataset"])
settings = get_settings()


@router.get("/status")
async def dataset_status(db: AsyncSession = Depends(get_db)) -> dict:
    """Return dataset and FAISS index status."""
    email_count = (await db.execute(select(func.count(Email.id)))).scalar_one()
    store = get_faiss_store()
    return {
        "email_count": email_count,
        "faiss_index_size": store.size,
        "dataset_path": settings.dataset_path,
        "dataset_exists": Path(settings.dataset_path).exists(),
    }


@router.post("/seed")
async def seed_database(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    force: bool = False,
) -> dict:
    """
    Seed the database from the JSON dataset file.
    If force=True, clears existing data before seeding.
    """
    dataset_path = Path(settings.dataset_path)
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset file not found: {dataset_path}")

    with dataset_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if force:
        # Delete all existing emails
        from sqlalchemy import delete
        await db.execute(delete(Email))
        await db.flush()

    emails_created = 0
    subjects, bodies, metas = [], [], []

    for item in data:
        email = Email(
            subject=item.get("subject", ""),
            sender=item.get("sender", "customer@example.com"),
            recipient=item.get("recipient", "support@company.com"),
            body=item.get("incoming_email", item.get("body", "")),
            ideal_reply=item.get("ideal_reply", ""),
            intent=item.get("intent", "general"),
            tone=item.get("tone", "professional"),
            priority=item.get("priority", "medium"),
            entities=item.get("entities", {}),
            expected_actions=item.get("expected_actions", []),
            tags=item.get("tags", []),
            category=item.get("category", "general"),
        )
        db.add(email)
        emails_created += 1

    await db.flush()

    # Rebuild FAISS in background
    background_tasks.add_task(_rebuild_faiss_task)

    return {
        "status": "seeding_complete",
        "emails_seeded": emails_created,
        "faiss_rebuild": "scheduled_in_background",
    }


async def _rebuild_faiss_task() -> None:
    """Background task to rebuild FAISS index from all emails in DB."""
    from backend.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        stmt = select(Email)
        result = await db.execute(stmt)
        emails = result.scalars().all()

    store = get_faiss_store()
    if emails:
        subjects = [e.subject for e in emails]
        bodies = [e.body for e in emails]
        metadata = [{"email_id": e.id, "category": e.category, "intent": e.intent} for e in emails]
        store.rebuild(subjects, bodies, metadata)
        logger.info("FAISS rebuild complete: %d vectors", len(emails))


@router.post("/rebuild-index")
async def rebuild_faiss_index(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Rebuild the FAISS index from all emails in the database."""
    count = (await db.execute(select(func.count(Email.id)))).scalar_one()
    background_tasks.add_task(_rebuild_faiss_task)
    return {
        "status": "rebuild_scheduled",
        "email_count": count,
        "message": "FAISS index rebuild started in background",
    }


@router.get("/export")
async def export_dataset(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Export all emails as JSON."""
    stmt = select(Email).limit(1000)
    result = await db.execute(stmt)
    emails = result.scalars().all()

    return [
        {
            "id": e.id,
            "subject": e.subject,
            "sender": e.sender,
            "category": e.category,
            "intent": e.intent,
            "tone": e.tone,
            "priority": e.priority,
            "incoming_email": e.body,
            "ideal_reply": e.ideal_reply,
            "entities": e.entities,
            "expected_actions": e.expected_actions,
            "tags": e.tags,
        }
        for e in emails
    ]
