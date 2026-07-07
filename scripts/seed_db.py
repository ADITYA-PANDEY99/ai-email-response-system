"""
Database seeding script — generates dataset and seeds the database.
Run once before starting the application.

Usage:
    python scripts/seed_db.py
    python scripts/seed_db.py --force    # Clear existing data
    python scripts/seed_db.py --no-generate  # Use existing emails.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import get_settings
from backend.database import init_db, AsyncSessionLocal
from backend.models.email import Email
from backend.retrieval.faiss_store import get_faiss_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()


async def seed(force: bool = False) -> None:
    """Full seeding pipeline."""
    dataset_path = Path(settings.dataset_path)

    # ── Step 1: Generate dataset if not exists ────────────────────────────
    if not dataset_path.exists():
        logger.info("Dataset not found, generating...")
        from dataset.generator import main as gen_main
        gen_main()
    else:
        logger.info("Using existing dataset: %s", dataset_path)

    # ── Step 2: Initialize database ───────────────────────────────────────
    logger.info("Initializing database...")
    await init_db()

    # ── Step 3: Load dataset ──────────────────────────────────────────────
    with dataset_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info("Loaded %d email samples", len(data))

    # ── Step 4: Seed database ─────────────────────────────────────────────
    async with AsyncSessionLocal() as db:
        if force:
            from sqlalchemy import delete
            await db.execute(delete(Email))
            await db.commit()
            logger.info("Cleared existing emails")

        emails: list[Email] = []
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
            emails.append(email)
            db.add(email)

        await db.commit()
        logger.info("✅ Seeded %d emails to database", len(emails))

    # ── Step 5: Build FAISS index ─────────────────────────────────────────
    logger.info("Building FAISS index...")
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Email))
        all_emails = result.scalars().all()

    store = get_faiss_store()
    subjects = [e.subject for e in all_emails]
    bodies = [e.body for e in all_emails]
    metadata = [
        {"email_id": e.id, "category": e.category, "intent": e.intent}
        for e in all_emails
    ]
    store.rebuild(subjects, bodies, metadata)
    logger.info("✅ FAISS index built: %d vectors", store.size)
    logger.info("🎉 Seeding complete!")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the email database")
    parser.add_argument("--force", action="store_true", help="Clear existing data before seeding")
    parser.add_argument("--no-generate", action="store_true", help="Skip dataset generation")
    args = parser.parse_args()

    asyncio.run(seed(force=args.force))


if __name__ == "__main__":
    main()
