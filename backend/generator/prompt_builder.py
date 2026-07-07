"""
Prompt builder for few-shot RAG-augmented email response generation.

Design:
- System prompt establishes the AI as a professional customer service agent.
- Few-shot examples are drawn from retrieved similar emails (ranked by similarity).
- Incoming email is presented last with explicit formatting instructions.
- Structured output markers allow deterministic response extraction.
"""
from __future__ import annotations

from backend.schemas.email import RetrievedEmail

SYSTEM_PROMPT = """You are an expert customer service AI assistant working for a professional business.

Your role is to draft polished, empathetic, and action-oriented email responses to customer inquiries.

Guidelines:
- Always be professional, warm, and solution-focused
- Address the customer's specific concern directly
- Use their name if available, otherwise use a polite salutation
- Provide clear next steps or resolutions
- Keep responses concise but complete (150-350 words typical)
- Match the appropriate tone (formal for enterprise, friendly for general customers)
- Never make promises you cannot keep
- Always close with a professional sign-off

Format your response as a complete, ready-to-send business email."""


def build_prompt(
    subject: str,
    body: str,
    sender: str,
    retrieved_emails: list[RetrievedEmail],
) -> str:
    """
    Construct a full few-shot RAG prompt.

    Args:
        subject: Incoming email subject
        body: Incoming email body
        sender: Customer email / name
        retrieved_emails: Similar historical emails (sorted by similarity desc)

    Returns:
        Complete prompt string ready for LLM inference
    """
    lines: list[str] = [SYSTEM_PROMPT, ""]

    # ── Few-shot examples (top 3 by similarity) ──────────────────────────────
    if retrieved_emails:
        lines.append("=" * 60)
        lines.append("REFERENCE EXAMPLES (similar past interactions):")
        lines.append("=" * 60)

        for i, ex in enumerate(retrieved_emails[:3], 1):
            lines.append(f"\n[Example {i}] (Similarity: {ex.similarity_score:.2%})")
            lines.append(f"Category: {ex.category} | Intent: {ex.intent} | Tone: {ex.tone}")
            lines.append(f"Customer Email:\n{ex.body[:600]}")
            lines.append(f"\nIdeal Response:\n{ex.ideal_reply}")
            lines.append("-" * 40)

    # ── Task ─────────────────────────────────────────────────────────────────
    lines.append("\n" + "=" * 60)
    lines.append("NOW RESPOND TO THIS INCOMING EMAIL:")
    lines.append("=" * 60)
    lines.append(f"From: {sender}")
    lines.append(f"Subject: {subject}")
    lines.append(f"\nEmail Body:\n{body}")

    lines.append("\n" + "=" * 60)
    lines.append("YOUR RESPONSE:")
    lines.append("=" * 60)
    lines.append(
        "Write a complete, professional email response. "
        "Start with 'Dear [Name/Customer],' and end with a professional closing."
    )

    return "\n".join(lines)


def build_fallback_prompt(subject: str, body: str, sender: str) -> str:
    """Minimal prompt for local fallback model (no few-shot)."""
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"Customer email from {sender}:\nSubject: {subject}\n{body}\n\n"
        "Please write a professional email response:"
    )
