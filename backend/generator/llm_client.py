"""
LLM client with Gemini primary and template-based fallback.

Design decisions:
- Async-first (httpx for Gemini REST calls).
- Fallback: rule-based template generator ensures system always produces output.
- Token counting approximated when exact values unavailable.
- Exponential backoff on rate limit errors.
"""
from __future__ import annotations

import asyncio
import logging
import random
import re
import time
from dataclasses import dataclass

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"


@dataclass
class LLMResponse:
    text: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float


class GeminiClient:
    """
    Async Gemini API client using the REST endpoint.
    Uses google-generativeai SDK when available, falls back to raw httpx.
    """

    def __init__(self) -> None:
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_model
        self._temperature = settings.gemini_temperature
        self._max_tokens = settings.gemini_max_tokens

    async def generate(self, prompt: str) -> LLMResponse:
        """Send prompt to Gemini and return structured response."""
        start = time.monotonic()

        try:
            import google.generativeai as genai  # type: ignore[import]

            genai.configure(api_key=self._api_key)
            model = genai.GenerativeModel(self._model)

            # Run synchronous SDK call in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self._temperature,
                        max_output_tokens=self._max_tokens,
                    ),
                ),
            )

            text = response.text
            latency_ms = (time.monotonic() - start) * 1000

            # Extract token usage if available
            usage = getattr(response, "usage_metadata", None)
            prompt_tokens = getattr(usage, "prompt_token_count", self._estimate_tokens(prompt))
            completion_tokens = getattr(usage, "candidates_token_count", self._estimate_tokens(text))

            return LLMResponse(
                text=text,
                model=self._model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
            )

        except Exception as e:
            logger.warning("Gemini SDK failed (%s), trying REST fallback...", e)
            return await self._generate_via_rest(prompt, start)

    async def _generate_via_rest(self, prompt: str, start: float) -> LLMResponse:
        """Direct REST call to Gemini API."""
        url = f"{GEMINI_API_BASE}/models/{self._model}:generateContent?key={self._api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self._temperature,
                "maxOutputTokens": self._max_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(3):
                try:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    latency_ms = (time.monotonic() - start) * 1000

                    usage = data.get("usageMetadata", {})
                    return LLMResponse(
                        text=text,
                        model=self._model,
                        prompt_tokens=usage.get("promptTokenCount", self._estimate_tokens(prompt)),
                        completion_tokens=usage.get("candidatesTokenCount", self._estimate_tokens(text)),
                        latency_ms=latency_ms,
                    )
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429 and attempt < 2:
                        await asyncio.sleep(2 ** attempt + random.random())
                        continue
                    raise

        raise RuntimeError("Gemini REST API failed after retries")

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Approximate token count: ~4 chars per token."""
        return max(1, len(text) // 4)


class TemplateFallbackClient:
    """
    Rule-based email response generator.

    Used when Gemini API is unavailable. Produces professional,
    coherent responses based on detected email intent patterns.
    """

    TEMPLATES: dict[str, str] = {
        "refund": (
            "Dear Valued Customer,\n\n"
            "Thank you for reaching out to us regarding your refund request. "
            "I completely understand how frustrating this situation must be, and I sincerely apologize "
            "for any inconvenience caused.\n\n"
            "I have reviewed your case and I'm happy to confirm that we will process your refund "
            "within 5-7 business days. The amount will be credited back to your original payment method.\n\n"
            "Please don't hesitate to contact us if you have any further questions. "
            "We value your business and hope to serve you better in the future.\n\n"
            "Best regards,\nCustomer Service Team"
        ),
        "shipping": (
            "Dear Valued Customer,\n\n"
            "Thank you for contacting us about your shipment. I apologize for any confusion "
            "or delay you may have experienced.\n\n"
            "I have checked the status of your order and can confirm it is being processed. "
            "You will receive a tracking number via email once your order has been dispatched. "
            "Estimated delivery is within 3-5 business days.\n\n"
            "If you have any further concerns, please do not hesitate to reach out to us.\n\n"
            "Best regards,\nCustomer Service Team"
        ),
        "technical": (
            "Dear Valued Customer,\n\n"
            "Thank you for reporting this technical issue. I apologize for the inconvenience "
            "this has caused.\n\n"
            "Our technical team has been notified and is actively working on a resolution. "
            "In the meantime, you may try clearing your browser cache and cookies, then "
            "attempting the action again. If the issue persists, please reply with any "
            "error messages you are seeing.\n\n"
            "We aim to have this resolved within 24-48 hours and will keep you updated.\n\n"
            "Best regards,\nTechnical Support Team"
        ),
        "billing": (
            "Dear Valued Customer,\n\n"
            "Thank you for contacting our billing department. I understand billing concerns "
            "can be stressful, and I want to assure you that we take these matters seriously.\n\n"
            "I have reviewed your account and will investigate the discrepancy you've mentioned. "
            "Our billing team will contact you within 2 business days with a full explanation "
            "and any necessary adjustments.\n\n"
            "Thank you for your patience and understanding.\n\n"
            "Best regards,\nBilling Support Team"
        ),
        "default": (
            "Dear Valued Customer,\n\n"
            "Thank you for reaching out to us. We have received your message and appreciate "
            "you taking the time to contact our team.\n\n"
            "We understand your concern and want to assure you that this has been escalated "
            "to the appropriate department. A member of our team will reach out to you within "
            "1-2 business days with a comprehensive response.\n\n"
            "We value your patience and look forward to resolving this matter to your satisfaction.\n\n"
            "Best regards,\nCustomer Service Team"
        ),
    }

    def detect_intent(self, email_body: str) -> str:
        body_lower = email_body.lower()
        if any(w in body_lower for w in ["refund", "money back", "return", "reimburs"]):
            return "refund"
        if any(w in body_lower for w in ["ship", "deliver", "tracking", "order", "package"]):
            return "shipping"
        if any(w in body_lower for w in ["error", "bug", "crash", "broken", "not work", "technical"]):
            return "technical"
        if any(w in body_lower for w in ["bill", "charge", "invoice", "payment", "subscription"]):
            return "billing"
        return "default"

    async def generate(self, prompt: str, email_body: str = "") -> LLMResponse:
        start = time.monotonic()
        intent = self.detect_intent(email_body or prompt)
        text = self.TEMPLATES.get(intent, self.TEMPLATES["default"])
        latency_ms = (time.monotonic() - start) * 1000
        return LLMResponse(
            text=text,
            model="template-fallback-v1",
            prompt_tokens=len(prompt) // 4,
            completion_tokens=len(text) // 4,
            latency_ms=latency_ms,
        )


class LLMClient:
    """
    Unified LLM client with automatic fallback.

    Priority:
    1. Gemini API (if key is available)
    2. Template-based fallback
    """

    def __init__(self) -> None:
        self._gemini = GeminiClient()
        self._fallback = TemplateFallbackClient()
        self._use_fallback = settings.use_fallback_llm or not settings.has_gemini_key

    async def generate(self, prompt: str, email_body: str = "") -> LLMResponse:
        if not self._use_fallback:
            try:
                return await self._gemini.generate(prompt)
            except Exception as e:
                logger.error("Gemini generation failed: %s. Using fallback.", e)
        return await self._fallback.generate(prompt, email_body)


_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
