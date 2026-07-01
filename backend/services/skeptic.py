"""
The Skeptic Pass — adversarial devil's-advocate second opinion.

Flow:
1. Given a preliminary verdict, generate the strongest possible counter-argument.
2. Have the adjudicator rebut that argument.
3. Score the rebuttal strength (0.0–1.0).
4. If rebuttal_strength < 0.55 → verdict is CONTESTED → force NON LIQUET.

This catches cases where the AI convinced itself with circular reasoning or
over-weighted a single evidence item.
"""

from __future__ import annotations

import json
import re

import structlog
from pydantic import BaseModel

from backend.core.llm_client import structured_chat
from backend.core.models import CaseFile, SkepticResult, Verdict
from config import settings

logger = structlog.get_logger(__name__)

CONTEST_THRESHOLD = 0.55   # below this → verdict cannot be defended


# ── LLM output schemas ────────────────────────────────────────────────────────

class DevilArgOutput(BaseModel):
    counter_argument: str
    weakest_evidence: str
    alternative_interpretation: str


class RebuttalOutput(BaseModel):
    rebuttal: str
    rebuttal_strength: float
    verdict_stands: bool
    contest_summary: str


# ── Prompts ───────────────────────────────────────────────────────────────────

_DEVIL_SYS = "You are a rigorous devil's advocate that finds the strongest possible flaw in legal rulings."

_DEVIL_USER = """A ruling was reached: {resolution} (confidence {confidence:.0%}).
Rationale: {rationale}

Case:
- Type: {dispute_type}  |  Order value: ${order_value}
- Buyer: {buyer_narrative}
- Seller: {seller_narrative}

Evidence:
{evidence_summary}

Find the single strongest counter-argument — a reason why this ruling might be WRONG.
Focus on: missing evidence, alternative interpretations, over-reliance on one source, policy exceptions."""

_REBUTTAL_SYS = "You are the original adjudicator defending your ruling against a skeptic's challenge."

_REBUTTAL_USER = """Your ruling: {resolution}
Your rationale: {rationale}

The skeptic argues: {counter_argument}
The skeptic calls out weak evidence: {weakest_evidence}
The skeptic's alternative reading: {alternative_interpretation}

Respond to each point. Then score how well you rebutted (0.0 = cannot rebut, 1.0 = fully neutralised).
End with a one-sentence summary: \"STANDS: <why>\" or \"CONTESTED: <why>\"."""


class SkepticEngine:
    async def challenge(self, case_file: CaseFile, verdict: Verdict) -> SkepticResult:
        log = logger.bind(dispute_id=case_file.dispute_id)

        try:
            evidence_summary = "\n".join(
                f"[{e.id}] {e.source} ({e.evidence_type.value}, "
                f"rel={e.reliability:.2f}): {str(e.content)[:200]}"
                for e in case_file.evidence
            )

            # Step 1: Devil's advocate
            devil_out = await structured_chat(
                messages=[
                    {"role": "system", "content": _DEVIL_SYS},
                    {"role": "user", "content": _DEVIL_USER.format(
                        resolution=verdict.resolution.value,
                        confidence=verdict.confidence,
                        rationale=verdict.rationale,
                        dispute_type=case_file.dispute_type.value,
                        order_value=case_file.order_value,
                        buyer_narrative=case_file.buyer.narrative,
                        seller_narrative=case_file.seller.narrative,
                        evidence_summary=evidence_summary,
                    )},
                ],
                schema=DevilArgOutput,
                model=settings.active_reasoning_model,
                temperature=0.5,
                max_tokens=1024,
            )

            # Step 2: Rebuttal
            rebuttal_out = await structured_chat(
                messages=[
                    {"role": "system", "content": _REBUTTAL_SYS},
                    {"role": "user", "content": _REBUTTAL_USER.format(
                        resolution=verdict.resolution.value,
                        rationale=verdict.rationale,
                        counter_argument=devil_out.counter_argument,
                        weakest_evidence=devil_out.weakest_evidence,
                        alternative_interpretation=devil_out.alternative_interpretation,
                    )},
                ],
                schema=RebuttalOutput,
                model=settings.active_reasoning_model,
                temperature=0.2,
                max_tokens=1024,
            )

            strength = max(0.0, min(1.0, rebuttal_out.rebuttal_strength))
            contested = strength < CONTEST_THRESHOLD

            log.info(
                "skeptic_complete",
                rebuttal_strength=strength,
                verdict_contested=contested,
            )

            return SkepticResult(
                devil_argument=devil_out.counter_argument,
                rebuttal=rebuttal_out.rebuttal,
                rebuttal_strength=strength,
                verdict_contested=contested,
                contest_summary=rebuttal_out.contest_summary,
            )

        except Exception as exc:
            log.error("skeptic_failed", error=str(exc))
            # Fail-open: don't block the verdict if the skeptic itself errors
            return SkepticResult(
                devil_argument="Skeptic pass failed — no counter-argument generated.",
                rebuttal="Rebuttal unavailable.",
                rebuttal_strength=0.75,
                verdict_contested=False,
                contest_summary="STANDS: Skeptic pass failed, defaulting to original verdict",
            )
