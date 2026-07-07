"""
Email CRUD router — manage the training/reference dataset via REST.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.email import Email
from backend.retrieval.faiss_store import get_faiss_store
from backend.schemas.email import EmailCreate, EmailListResponse, EmailRead

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/emails", tags=["emails"])


@router.get("/", response_model=EmailListResponse)
async def list_emails(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    category: str | None = None,
    intent: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> EmailListResponse:
    """List emails with filtering and pagination."""
    stmt = select(Email)

    if category:
        stmt = stmt.where(Email.category.ilike(f"%{category}%"))
    if intent:
        stmt = stmt.where(Email.intent.ilike(f"%{intent}%"))
    if priority:
        stmt = stmt.where(Email.priority == priority)
    if search:
        stmt = stmt.where(
            Email.subject.ilike(f"%{search}%") | Email.body.ilike(f"%{search}%")
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    emails = (await db.execute(stmt)).scalars().all()

    return EmailListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[EmailRead.model_validate(e) for e in emails],
    )


@router.get("/{email_id}", response_model=EmailRead)
async def get_email(email_id: int, db: AsyncSession = Depends(get_db)) -> EmailRead:
    """Get a single email by ID."""
    email = await db.get(Email, email_id)
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    return EmailRead.model_validate(email)


@router.post("/", response_model=EmailRead, status_code=status.HTTP_201_CREATED)
async def create_email(
    payload: EmailCreate,
    db: AsyncSession = Depends(get_db),
) -> EmailRead:
    """Create a new email in the dataset and index it in FAISS."""
    email = Email(**payload.model_dump())
    db.add(email)
    await db.flush()

    # Index in FAISS
    store = get_faiss_store()
    store.add_texts(
        subjects=[email.subject],
        bodies=[email.body],
        metadata=[{"email_id": email.id, "category": email.category, "intent": email.intent}],
    )

    logger.info("Created email id=%d and indexed in FAISS", email.id)
    return EmailRead.model_validate(email)


@router.delete("/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_email(email_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Delete an email from the database. (FAISS rebuild required separately.)"""
    email = await db.get(Email, email_id)
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    await db.delete(email)


@router.get("/stats/categories")
async def get_category_stats(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Return email counts by category."""
    stmt = select(Email.category, func.count(Email.id).label("count")).group_by(Email.category)
    result = await db.execute(stmt)
    return [{"category": row.category, "count": row.count} for row in result]


@router.get("/stats/intents")
async def get_intent_stats(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """Return email counts by intent."""
    stmt = select(Email.intent, func.count(Email.id).label("count")).group_by(Email.intent)
    result = await db.execute(stmt)
    return [{"intent": row.intent, "count": row.count} for row in result]
