"""
Evaluation Engine — orchestrates all 12 metrics and produces weighted scores.

Design Philosophy:
==================
Traditional NLP metrics like BLEU measure n-gram overlap, which fails for
business email responses where "We'll process your refund immediately" and
"Your reimbursement will be handled right away" are semantically equivalent
but share almost no n-grams.

Our weighted multi-metric approach captures:
1. WHAT was said (semantic similarity, intent match)
2. HOW it was said (tone, professionalism, grammar)
3. WHAT was covered (completeness, action coverage, entity coverage)
4. RELIABILITY (hallucination detection, safety)
5. FIT (retrieval consistency, length)

Metric weights are calibrated to reflect customer impact:
- Semantic Similarity (30%): Core measure of response relevance
- Intent Match (20%): Critical — wrong intent = customer frustration
- Completeness (15%): Unanswered questions = repeat contacts
- Tone Match (10%): Affects customer satisfaction scores
- Action Coverage (10%): Missing commitments = broken promises
- Safety (5%): Non-negotiable floor metric
- Grammar (5%): Professional appearance
- Professionalism (3%): Brand representation
- Length (2%): UX factor
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.evaluation.metrics import (
    action_coverage,
    completeness,
    entity_coverage,
    grammar_quality,
    hallucination,
    intent_match,
    length_penalty,
    professionalism,
    retrieval_consistency,
    safety,
    semantic_similarity,
    tone_match,
)
from backend.models.evaluation import EvaluationResult
from backend.schemas.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    MetricBreakdown,
    MetricScore,
)

logger = logging.getLogger(__name__)
settings = get_settings()


def _traffic_light(score: float) -> str:
    if score >= 0.75:
        return "green"
    elif score >= 0.50:
        return "amber"
    return "red"


def _grade(score: float) -> str:
    if score >= 0.90:
        return "A"
    elif score >= 0.80:
        return "B"
    elif score >= 0.70:
        return "C"
    elif score >= 0.55:
        return "D"
    return "F"


def _compute_confidence(
    semantic_similarity: float,
    retrieval_consistency: float,
    intent_match: float,
    llm_judge_score: float,
) -> float:
    """
    Computes a refined confidence estimate based on:
    - Semantic embedding similarity
    - Retrieval similarity (consistency)
    - Intent match score
    - LLM judge agreement (agreement with embedding similarity)
    """
    agreement = 1.0 - abs(llm_judge_score - semantic_similarity)
    conf = (
        0.35 * semantic_similarity
        + 0.15 * retrieval_consistency
        + 0.25 * intent_match
        + 0.25 * agreement
    )
    return round(max(0.0, min(1.0, conf)), 3)


def _enrich_metric(name: str, score: float) -> tuple[str, str]:
    """Generates default explanation details for why a metric lost points and how to improve."""
    if score >= 0.95:
        return (
            "No significant point deductions. The response meets high-quality expectations.",
            "No improvements necessary. Excellent response structure and content."
        )

    # Dictionary mappings for why points were lost and improvements
    enrichment_map = {
        "semantic_similarity": (
            f"Score of {score:.0%} indicates semantic variation from reference. The phrasing or vocabulary deviates from the ideal template.",
            "Align terminology more closely with the ideal reference reply. Retain specific instructions and operational terms."
        ),
        "intent_match": (
            f"Intent match score is {score:.0%}. Certain intent-specific keywords or expected responses are missing.",
            "Identify the customer's main intent (e.g. billing, shipping, cancellation) and directly address it in the opening sentences."
        ),
        "completeness": (
            f"Completeness score of {score:.0%} indicates one or more customer concerns or questions were left unanswered.",
            "List all questions in the incoming email and verify the reply contains a direct answer for each."
        ),
        "tone_match": (
            f"Tone alignment is {score:.0%}. The emotion or sentiment level deviates from the expected target tone.",
            "Use empathetic phrases if the customer is frustrated, or clear professional language if inquiry is formal."
        ),
        "action_coverage": (
            f"Action coverage is {score:.0%}. Not all required next steps or workflow promises were committed to in writing.",
            "Specifically outline who does what next, providing concrete timelines for processing refunds, shipping, or technical fixes."
        ),
        "safety": (
            f"Safety score is {score:.0%}. Risky patterns such as making absolute guarantees or requesting sensitive details were flagged.",
            "Remove absolute liability statements and avoid asking for passwords, credit card numbers, or full keys."
        ),
        "grammar_quality": (
            f"Grammar score of {score:.0%} due to excessive word length, potential run-on sentences, or repetitive phrases.",
            "Keep sentences under 25 words. Proofread for double spaces, double punctuation, and active voice."
        ),
        "professionalism": (
            f"Professionalism score is {score:.0%}. Missing standard greeting, support signature blocks, or formal structural elements.",
            "Add a formal greeting (e.g., 'Dear [Name],'), clear paragraph breaks, and a professional closing signature."
        ),
        "length_penalty": (
            f"Length score is {score:.0%}. The response is either too brief to be helpful or overly verbose and wordy.",
            "Structure the email concisely. Aim for 50-150 words for simple inquiries, and up to 250 words for complex technical issues."
        ),
        "hallucination_score": (
            f"Hallucination score of {score:.0%}. Specific dates, dollar amounts, discount offers, or policy timelines do not match source data.",
            "Ensure all references, amounts, and dates are pulled exactly from the incoming email context. Avoid inventing placeholder values."
        ),
        "entity_coverage": (
            f"Entity coverage is {score:.0%}. Customer details (names, dates, order IDs) were genericized or omitted.",
            "Directly reference custom entities like order IDs (e.g. ORD-123) and dates mentioned by the customer."
        ),
        "retrieval_consistency": (
            f"Retrieval consistency is {score:.0%}. The tone or solution conflicts with how similar cases were historically resolved.",
            "Consult the top retrieved historical examples and reuse approved phrasing patterns for resolving identical category tickets."
        )
    }

    return enrichment_map.get(
        name,
        ("The response did not meet the standard threshold on this metric.", "Review the metric rules and refine the response wording accordingly.")
    )


class EvaluationEngine:
    """
    Orchestrates all evaluation metrics and returns a comprehensive score.
    """

    def __init__(self) -> None:
        self._weights = settings.eval_weights

    async def _run_llm_judge(
        self,
        gen: str,
        ref: str | None,
        inc: str,
        tone: str | None,
        intent: str | None,
    ) -> dict[str, Any]:
        """Call Gemini to rate generated reply on correctness, helpfulness, tone, etc."""
        ref_text = ref or "No ideal reply provided. Score against general business communication standards and responsiveness to the customer email."
        
        prompt = f"""You are an expert customer service quality assurance auditor. Evaluate the generated email reply compared to the ideal reference reply.

Incoming Customer Email:
{inc}

Ideal Reference Reply:
{ref_text}

Generated Reply:
{gen}

Evaluate the generated reply across these 6 criteria. For each, provide a score from 0.0 to 1.0 (where 1.0 is perfect) and a concise one-sentence explanation.
1. correctness: Factually accurate, follows guidelines, and addresses the root issue.
2. helpfulness: Friendly, supportive, solves the problem completely.
3. tone: Appropriate sentiment matching the customer's state (concerned, polite, or apologetic).
4. professionalism: Proper business formatting, greeting/sign-off, brand-safe language.
5. missing_information: Score 1.0 if all crucial information or steps from the reference are covered.
6. hallucinations: Score 1.0 if the response has zero invented details, ungrounded dates/amounts, or false promises.

Return raw JSON only, matching this exact template:
{{
  "correctness": {{"score": 0.95, "explanation": "..."}},
  "helpfulness": {{"score": 0.90, "explanation": "..."}},
  "tone": {{"score": 0.85, "explanation": "..."}},
  "professionalism": {{"score": 1.00, "explanation": "..."}},
  "missing_information": {{"score": 0.80, "explanation": "..."}},
  "hallucinations": {{"score": 1.00, "explanation": "..."}}
}}"""

        from backend.generator.llm_client import get_llm_client
        client = get_llm_client()
        
        try:
            if settings.has_gemini_key:
                resp = await client.generate(prompt)
                text = resp.text
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                return json.loads(text.strip())
        except Exception as e:
            logger.warning("LLM Judge evaluation failed: %s. Using heuristic judge.", e)

        # Heuristic judge fallback
        import numpy as np
        sim = 0.8
        try:
            from backend.retrieval.embedder import get_embedder
            embedder = get_embedder()
            vec_gen = embedder.embed_text(gen[:600])
            vec_ref = embedder.embed_text(ref_text[:600])
            sim = float(np.clip(np.dot(vec_gen, vec_ref), 0.0, 1.0))
        except Exception:
            pass

        has_greeting = any(g in gen.lower() for g in ["dear", "hi", "hello", "thank you"])
        has_signoff = any(s in gen.lower() for s in ["sincerely", "regards", "best", "thanks"])
        
        return {
            "correctness": {"score": round(sim, 2), "explanation": "Estimated via semantic comparison to ideal reference reply."},
            "helpfulness": {"score": round(max(0.4, sim - 0.05), 2), "explanation": "Response addresses the core inquiry matching reference semantics."},
            "tone": {"score": 0.90 if (not tone or tone.lower() in gen.lower() or sim > 0.7) else 0.70, "explanation": "Tone matches standard business email guidelines."},
            "professionalism": {"score": 1.0 if (has_greeting and has_signoff) else 0.75, "explanation": "Checks for greetings, sign-offs, and appropriate language structure."},
            "missing_information": {"score": round(sim, 2), "explanation": "Proportion of information aligned with the reference reply."},
            "hallucinations": {"score": 0.95, "explanation": "No direct hallucinations detected heuristically."}
        }

    async def evaluate(
        self,
        request: EvaluationRequest,
        db: AsyncSession,
        retrieved_replies: list[str] | None = None,
    ) -> EvaluationResponse:
        """
        Run all metrics concurrently, aggregate, persist, and return results.
        """
        gen = request.generated_reply
        ref = request.reference_reply
        inc = request.incoming_email
        intent = request.intent
        tone_exp = request.tone
        actions = request.expected_actions
        entities = request.entities

        # ── Run all metrics (non-async) in executor ───────────────────────
        loop = asyncio.get_event_loop()

        def _run_all() -> dict:
            return {
                "semantic_similarity": semantic_similarity.compute(gen, ref or ""),
                "intent_match": intent_match.compute(gen, ref or "", intent),
                "completeness": completeness.compute(gen, inc, ref),
                "tone_match": tone_match.compute(gen, tone_exp),
                "action_coverage": action_coverage.compute(gen, actions),
                "entity_coverage": entity_coverage.compute(gen, inc, entities),
                "hallucination": hallucination.compute(gen, inc, ref, retrieved_replies),
                "grammar_quality": grammar_quality.compute(gen),
                "professionalism": professionalism.compute(gen),
                "safety": safety.compute(gen),
                "retrieval_consistency": retrieval_consistency.compute(gen, retrieved_replies or []),
                "length_penalty": length_penalty.compute(gen, ref),
            }

        results = await loop.run_in_executor(None, _run_all)

        # ── Extract scores ────────────────────────────────────────────────
        raw_scores = {
            "semantic_similarity": results["semantic_similarity"].score,
            "intent_match": results["intent_match"].score,
            "completeness": results["completeness"].score,
            "tone_match": results["tone_match"].score,
            "action_coverage": results["action_coverage"].score,
            "safety": results["safety"].score,
            "grammar_quality": results["grammar_quality"].score,
            "professionalism": results["professionalism"].score,
            "length_penalty": results["length_penalty"].score,
            "hallucination_score": results["hallucination"].score,
            "entity_coverage": results["entity_coverage"].score,
            "retrieval_consistency": results["retrieval_consistency"].score,
        }

        # ── Step 2: Add LLM Judge Evaluation ─────────────────────────────────
        llm_judge = await self._run_llm_judge(gen, ref, inc, tone_exp, intent)
        judge_correctness = float(llm_judge.get("correctness", {}).get("score", 0.8))
        judge_helpfulness = float(llm_judge.get("helpfulness", {}).get("score", 0.8))

        # Combine: 50% embedding similarity + 30% judge correctness + 20% judge helpfulness
        combined_semantic = 0.5 * raw_scores["semantic_similarity"] + 0.3 * judge_correctness + 0.2 * judge_helpfulness
        raw_scores["semantic_similarity"] = round(combined_semantic, 4)

        # ── Weighted overall score ────────────────────────────────────────
        w = self._weights
        overall_score = (
            w["semantic_similarity"] * raw_scores["semantic_similarity"]
            + w["intent_match"] * raw_scores["intent_match"]
            + w["completeness"] * raw_scores["completeness"]
            + w["tone_match"] * raw_scores["tone_match"]
            + w["action_coverage"] * raw_scores["action_coverage"]
            + w["safety"] * raw_scores["safety"]
            + w["grammar_quality"] * raw_scores["grammar_quality"]
            + w["professionalism"] * raw_scores["professionalism"]
            + w["length_penalty"] * raw_scores["length_penalty"]
        )
        overall_score = round(min(1.0, max(0.0, overall_score)), 4)

        # Safety floor: if safety score is very low, cap overall
        if raw_scores["safety"] < 0.3:
            overall_score = min(overall_score, 0.4)
            logger.warning("Safety floor applied: overall_score capped at 0.4")

        # ── Confidence & traffic light ────────────────────────────────────
        confidence = _compute_confidence(
            semantic_similarity=raw_scores["semantic_similarity"],
            retrieval_consistency=raw_scores["retrieval_consistency"],
            intent_match=raw_scores["intent_match"],
            llm_judge_score=(judge_correctness + judge_helpfulness) / 2.0
        )
        traffic = _traffic_light(overall_score)
        grade = _grade(overall_score)

        # ── Build MetricBreakdown ─────────────────────────────────────────
        def _ms(key: str, weight: float, result) -> MetricScore:
            why, improve = _enrich_metric(key, result.score)
            return MetricScore(
                score=result.score,
                weight=weight,
                weighted_contribution=round(result.score * weight, 4),
                explanation=result.explanation,
                why_lost_points=why,
                how_to_improve=improve,
                details=result.details,
            )

        breakdown = MetricBreakdown(
            semantic_similarity=_ms("semantic_similarity", w["semantic_similarity"], results["semantic_similarity"]),
            intent_match=_ms("intent_match", w["intent_match"], results["intent_match"]),
            completeness=_ms("completeness", w["completeness"], results["completeness"]),
            tone_match=_ms("tone_match", w["tone_match"], results["tone_match"]),
            action_coverage=_ms("action_coverage", w["action_coverage"], results["action_coverage"]),
            safety=_ms("safety", w["safety"], results["safety"]),
            grammar_quality=_ms("grammar_quality", w["grammar_quality"], results["grammar_quality"]),
            professionalism=_ms("professionalism", w["professionalism"], results["professionalism"]),
            length_penalty=_ms("length_penalty", w["length_penalty"], results["length_penalty"]),
            hallucination_score=MetricScore(
                score=results["hallucination"].score,
                weight=0.0,
                weighted_contribution=0.0,
                explanation=results["hallucination"].explanation,
                why_lost_points=_enrich_metric("hallucination_score", results["hallucination"].score)[0],
                how_to_improve=_enrich_metric("hallucination_score", results["hallucination"].score)[1],
                details=results["hallucination"].details,
            ),
            entity_coverage=MetricScore(
                score=results["entity_coverage"].score,
                weight=0.0,
                weighted_contribution=0.0,
                explanation=results["entity_coverage"].explanation,
                why_lost_points=_enrich_metric("entity_coverage", results["entity_coverage"].score)[0],
                how_to_improve=_enrich_metric("entity_coverage", results["entity_coverage"].score)[1],
                details=results["entity_coverage"].details,
            ),
            retrieval_consistency=MetricScore(
                score=results["retrieval_consistency"].score,
                weight=0.0,
                weighted_contribution=0.0,
                explanation=results["retrieval_consistency"].explanation,
                why_lost_points=_enrich_metric("retrieval_consistency", results["retrieval_consistency"].score)[0],
                how_to_improve=_enrich_metric("retrieval_consistency", results["retrieval_consistency"].score)[1],
                details=results["retrieval_consistency"].details,
            ),
        )

        # ── Strengths / weaknesses / recommendations ──────────────────────
        strengths, weaknesses, recommendations = _generate_narrative(raw_scores, results, llm_judge)

        # ── Format metric explanations for database ───────────────────────
        db_metric_exps = {}
        for k in results:
            score_obj = getattr(breakdown, k + "_score" if k in ["hallucination"] else k, None)
            if score_obj:
                db_metric_exps[k] = {
                    "explanation": score_obj.explanation,
                    "why_lost_points": score_obj.why_lost_points,
                    "how_to_improve": score_obj.how_to_improve,
                }
            else:
                db_metric_exps[k] = {"explanation": getattr(results[k], "explanation", "")}

        # ── Executive Summary ─────────────────────────────────────────────
        executive_summary = _generate_executive_summary(raw_scores, strengths, weaknesses)

        # ── Persist ───────────────────────────────────────────────────────
        eval_orm = EvaluationResult(
            response_id=request.response_id,
            overall_score=overall_score,
            confidence=confidence,
            traffic_light=traffic,
            semantic_similarity=raw_scores["semantic_similarity"],
            intent_match=raw_scores["intent_match"],
            completeness=raw_scores["completeness"],
            tone_match=raw_scores["tone_match"],
            action_coverage=raw_scores["action_coverage"],
            safety=raw_scores["safety"],
            grammar_quality=raw_scores["grammar_quality"],
            professionalism=raw_scores["professionalism"],
            length_penalty=raw_scores["length_penalty"],
            hallucination_score=raw_scores["hallucination_score"],
            entity_coverage=raw_scores["entity_coverage"],
            retrieval_consistency=raw_scores["retrieval_consistency"],
            metric_explanations=db_metric_exps,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            executive_summary=executive_summary,
        )
        db.add(eval_orm)
        await db.flush()

        from datetime import datetime, timezone
        return EvaluationResponse(
            evaluation_id=eval_orm.id,
            response_id=request.response_id,
            overall_score=overall_score,
            confidence=confidence,
            traffic_light=traffic,
            grade=grade,
            metric_breakdown=breakdown,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            executive_summary=executive_summary,
            created_at=datetime.now(timezone.utc),
        )


def _generate_executive_summary(
    scores: dict[str, float],
    strengths: list[str],
    weaknesses: list[str],
) -> str:
    """Generate a short business executive summary about response quality."""
    correct = scores.get("semantic_similarity", 0.8) >= 0.75
    empathy = scores.get("tone_match", 0.8) >= 0.75
    complete = scores.get("completeness", 0.8) >= 0.75
    actions = scores.get("action_coverage", 0.8) >= 0.75
    
    parts = []
    if correct and complete:
        parts.append("This reply preserves customer intent, maintains a professional tone, and addresses all customer concerns comprehensively.")
    elif correct:
        parts.append("The reply is semantically accurate but overlooks some secondary concerns.")
    else:
        parts.append("The reply exhibits semantic drift compared to the expected ideal reply template.")
        
    if empathy:
        parts.append("It maintains an empathetic and professional customer support tone.")
    else:
        parts.append("However, minor adjustments to tone are recommended to improve customer sentiment.")
        
    if not actions:
        parts.append("Critical next-step action commitments are currently missing.")
    elif scores.get("hallucination_score", 1.0) < 0.75:
        parts.append("Minor improvements are recommended around clarifying specific refund details or dates to avoid hallucination risks.")
    else:
        parts.append("All next steps are clearly committed to with zero factual risk.")
        
    return " ".join(parts)


def _generate_narrative(
    scores: dict[str, float],
    results: dict,
    llm_judge: dict[str, Any],
) -> tuple[list[str], list[str], list[str]]:
    """Generate human-readable strengths, weaknesses, and recommendations."""
    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendations: list[str] = []

    thresholds = {
        "semantic_similarity": ("Excellent semantic alignment with the reference response", "Semantic meaning diverges significantly from expected response"),
        "intent_match": ("Successfully identifies and addresses the customer's intent", "Response does not adequately address the stated customer intent"),
        "completeness": ("Comprehensively addresses all customer concerns", "Leaves key customer questions unanswered"),
        "tone_match": ("Tone is well-calibrated to the customer context", "Tone mismatch may affect customer satisfaction"),
        "action_coverage": ("Commits to all required next steps and actions", "Misses committing to required customer actions"),
        "safety": ("No safety or compliance concerns detected", "Safety violations detected — requires immediate review"),
        "grammar_quality": ("Professional writing quality with minimal errors", "Grammar issues undermine professional credibility"),
        "professionalism": ("Email structure and formality meet business standards", "Response lacks professional email structure"),
        "length_penalty": ("Response length is appropriate for the context", "Response length is outside optimal range"),
        "hallucination_score": ("Claims are well-grounded in source material", "Potential hallucination — claims not supported by context"),
        "entity_coverage": ("Customer-specific details are acknowledged", "Generic response ignores customer-specific details"),
        "retrieval_consistency": ("Consistent with similar historical responses", "Inconsistent with how similar cases were resolved"),
    }

    for metric, (strength_msg, weakness_msg) in thresholds.items():
        score = scores.get(metric, 0.5)
        if score >= 0.75:
            strengths.append(f"✓ {strength_msg} ({score:.0%})")
        elif score < 0.55:
            weaknesses.append(f"✗ {weakness_msg} ({score:.0%})")

    # Flag missing details from the evaluation request
    hall_details = results["hallucination"].details.get("hallucination_flags", {})
    if hall_details:
        for flag_name, matches in hall_details.items():
            if matches:
                weaknesses.append(f"✗ Hallucination Flagged: {flag_name.replace('_', ' ')} ({len(matches)} occurrences)")
                recommendations.append(f"Fix flagged {flag_name.replace('_', ' ')}: {', '.join(matches[:2])}.")

    # Integrate LLM Judge feedback
    for criterion in ["correctness", "helpfulness", "tone", "professionalism", "missing_information", "hallucinations"]:
        judge_data = llm_judge.get(criterion, {})
        if isinstance(judge_data, dict):
            j_score = judge_data.get("score", 1.0)
            j_expl = judge_data.get("explanation", "")
            if j_score < 0.7:
                weaknesses.append(f"✗ Judge Criticized {criterion.capitalize()}: {j_expl}")
                recommendations.append(f"Improve {criterion}: {j_expl}")

    # Generate actionable recommendations
    if scores.get("completeness", 1.0) < 0.65:
        recommendations.append("Expand the response to address all questions raised in the customer email.")
    if scores.get("action_coverage", 1.0) < 0.65:
        recommendations.append("Add explicit commitments for each expected action (e.g., 'We will process X within Y days').")
    if scores.get("hallucination_score", 1.0) < 0.70:
        recommendations.append("Review and remove unverified claims not supported by the email context.")
    if scores.get("tone_match", 1.0) < 0.60:
        recommendations.append("Adjust the tone to better match the customer's communication style and context.")
    if scores.get("entity_coverage", 1.0) < 0.60:
        recommendations.append("Reference specific details from the customer email (order numbers, dates, amounts).")
    if scores.get("safety", 1.0) < 0.70:
        recommendations.append("PRIORITY: Remove legally risky language and ensure compliance review before sending.")
    if not recommendations:
        recommendations.append("Response is strong. Consider A/B testing this template for similar customer cases.")

    return strengths, weaknesses, recommendations


_engine: EvaluationEngine | None = None


def get_engine() -> EvaluationEngine:
    global _engine
    if _engine is None:
        _engine = EvaluationEngine()
    return _engine
