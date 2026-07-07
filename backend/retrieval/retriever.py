"""
RAG Retriever — combines FAISS search with database hydration.
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.email import Email
from backend.retrieval.embedder import get_embedder
from backend.retrieval.faiss_store import get_faiss_store
from backend.schemas.email import RetrievedEmail

logger = logging.getLogger(__name__)
settings = get_settings()


class RAGRetriever:
    """
    Retrieves the most semantically similar historical emails.

    Workflow:
    1. Embed incoming email text using sentence-transformers.
    2. Search FAISS index for top-k nearest neighbours.
    3. Hydrate ORM objects from SQLite for full field access.
    4. Return structured RetrievedEmail objects for prompt construction.
    """

    def __init__(self) -> None:
        self._store = get_faiss_store()
        self._embedder = get_embedder()

    async def retrieve(
        self,
        subject: str,
        body: str,
        db: AsyncSession,
        top_k: int = 5,
    ) -> list[RetrievedEmail]:
        """Main retrieval entry point."""
        query_text = self._embedder.email_to_text(subject, body)
        raw_results = self._store.search(query_text, top_k=top_k)

        if not raw_results:
            logger.warning("FAISS returned no results for query.")
            return []

        # Hydrate from DB to get full email objects
        email_ids = [r["email_id"] for r in raw_results if "email_id" in r]
        score_map = {r["email_id"]: r["similarity_score"] for r in raw_results if "email_id" in r}

        if not email_ids:
            return []

        stmt = select(Email).where(Email.id.in_(email_ids))
        result = await db.execute(stmt)
        emails = result.scalars().all()

        # Simple query intent / category detection for retrieval reasons
        body_lower = body.lower()
        query_intent = "general"
        for kw, it in [
            ("refund", "refund_request"), ("ship", "shipping_inquiry"),
            ("bill", "billing_dispute"), ("error", "technical_issue"),
            ("password", "account_recovery"), ("cancel", "subscription_cancellation"),
            ("price", "pricing_inquiry"), ("bug", "bug_report"),
            ("feature", "feature_request"), ("access", "account_access")
        ]:
            if kw in body_lower:
                query_intent = it
                break

        # Preserve ranking order from FAISS
        id_to_email = {e.id: e for e in emails}
        retrieved: list[RetrievedEmail] = []
        for eid in email_ids:
            email = id_to_email.get(eid)
            if email is None:
                continue
            
            # Formulate reason
            score = score_map.get(eid, 0.0)
            reasons = []
            if score >= 0.8:
                reasons.append(f"Strong semantic match ({score:.0%})")
            elif score >= 0.6:
                reasons.append(f"Moderate semantic match ({score:.0%})")
            else:
                reasons.append(f"Semantic similarity match ({score:.0%})")

            if email.intent.lower() == query_intent.lower():
                reasons.append("identical customer intent")
            if any(t in body_lower for t in email.tags):
                reasons.append("overlapping context tags")
            
            reason_str = reasons[0]
            if len(reasons) > 1:
                reason_str += " and " + ", ".join(reasons[1:])

            retrieved.append(
                RetrievedEmail(
                    id=email.id,
                    subject=email.subject,
                    body=email.body,
                    ideal_reply=email.ideal_reply,
                    intent=email.intent,
                    tone=email.tone,
                    category=email.category,
                    similarity_score=score,
                    retrieval_reason=reason_str,
                )
            )

        logger.debug("Retrieved %d similar emails for query.", len(retrieved))
        return retrieved


_retriever_instance: RAGRetriever | None = None


def get_retriever() -> RAGRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = RAGRetriever()
    return _retriever_instance
