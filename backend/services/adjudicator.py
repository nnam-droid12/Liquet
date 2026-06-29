"""
Adjudication Pipeline — uses qwen3.7-max (REASONING model) to:
1. Extract claims from both parties' narratives
2. Map each claim to evidence items (supporting / contradicting)
3. Score evidence reliability
4. Detect hard contradictions
5. Apply policy to select resolution
6. Emit a Verdict with calibrated confidence and evidence citations
"""

from __future__ import annotations

import json
import structlog
from typing import Any

from backend.core.llm_client import structured_chat, chat_completion
from backend.core.models import (
    CaseFile, Claim, EvidenceCitation, EvidenceType, ResolutionType,
    Verdict, VerdictOutput, ClaimExtraction,
)
from config import settings

logger = structlog.get_logger(__name__)

CLAIM_EXTRACTION_PROMPT = """You are a neutral marketplace dispute analyst.

Extract the specific factual claims made by each party from their narratives and any message history.
Focus on claims that are verifiable against evidence (item condition, delivery, color, damage, etc.).
Do NOT include opinions or demands — only factual assertions.

Return JSON with:
{{
  "buyer_claims": ["specific factual claim 1", ...],
  "seller_claims": ["specific factual claim 1", ...]
}}"""

ADJUDICATION_PROMPT = """You are Liquet — an autonomous marketplace dispute adjudicator applying Roman legal standards.

You must reach a verdict of LIQUET (clear — resolve) or NON_LIQUET (unclear — escalate).
For now, produce your best verdict with a calibrated confidence score.

## Case Summary
- Dispute Type: {dispute_type}
- Order Value: ${order_value}
- Buyer Claims: {buyer_claims}
- Seller Claims: {seller_claims}

## Evidence Available
{evidence_summary}

## Policy
{policy_text}

## Instructions
1. Map each claim to evidence. Which evidence supports or contradicts each claim?
2. Weight evidence by reliability: carrier_scan (0.95) > order_record (0.90) > listing_data (0.85) > photo (0.70) > message (0.40) > claim (0.20)
3. Identify any HARD CONTRADICTIONS (two pieces of evidence that cannot both be true)
4. Select the best resolution from eligible options considering policy
5. Assign a calibrated confidence (0.0–1.0):
   - >0.90: overwhelming evidence, clear-cut case
   - 0.80–0.90: strong evidence, reasonable certainty
   - 0.60–0.80: moderate evidence, some uncertainty
   - <0.60: genuinely ambiguous, missing critical evidence
6. Note which policy clauses control the decision

Respond with JSON:
{{
  "resolution": "full_refund|partial_refund|replacement|return_then_refund|deny|escalate",
  "confidence": 0.0-1.0,
  "rationale": "2-4 sentence explanation citing evidence IDs",
  "policy_clauses": ["T-001-A", ...],
  "citation_evidence_ids": ["evidence_id_1", ...],
  "partial_refund_pct": null or 0.0-1.0,
  "hard_contradictions": ["description of contradiction if any"]
}}"""


class AdjudicationPipeline:
    async def adjudicate(self, case_file: CaseFile) -> Verdict:
        log = logger.bind(dispute_id=case_file.dispute_id)

        # Step 1: Extract claims
        claims = await self._extract_claims(case_file)
        log.info("claims_extracted",
                 buyer_claims=len(claims.buyer_claims),
                 seller_claims=len(claims.seller_claims))

        # Step 2: Build evidence summary for LLM
        evidence_summary = self._format_evidence(case_file)

        # Step 3: Get policy text
        try:
            from backend.services.tool_client import ToolClient
            policy_text = await ToolClient().get_policy_text()
        except Exception:
            policy_text = "Standard buyer protection policy applies."

        # Step 4: Run adjudication
        verdict_output = await self._run_adjudication(
            case_file, claims, evidence_summary, policy_text
        )
        log.info("adjudication_complete",
                 resolution=verdict_output.resolution,
                 confidence=verdict_output.confidence)

        # Step 5: Build Verdict with citations
        citations = []
        for eid in verdict_output.citation_evidence_ids:
            ev = case_file.evidence_by_id(eid)
            if ev:
                citations.append(EvidenceCitation(
                    evidence_id=ev.id,
                    evidence_source=ev.source,
                    supports=verdict_output.rationale[:100],
                ))

        # Map hard contradictions back to case_file
        if verdict_output.hard_contradictions:
            case_file.hard_contradictions.extend(verdict_output.hard_contradictions)

        # Resolve resolution enum safely
        try:
            resolution = ResolutionType(verdict_output.resolution)
        except ValueError:
            resolution = ResolutionType.ESCALATE

        return Verdict(
            resolution=resolution,
            confidence=max(0.0, min(1.0, verdict_output.confidence)),
            rationale=verdict_output.rationale,
            citations=citations,
            value_at_stake=case_file.order_value,
            policy_clauses=verdict_output.policy_clauses,
            partial_refund_pct=verdict_output.partial_refund_pct,
        )

    async def _extract_claims(self, case_file: CaseFile) -> ClaimExtraction:
        """Use LLM to extract verifiable claims from each party's narrative + messages."""
        messages_text = ""
        for ev in case_file.evidence:
            if ev.evidence_type == EvidenceType.MESSAGE:
                msgs = ev.content if isinstance(ev.content, list) else []
                for m in msgs:
                    messages_text += f"\n[{m.get('from','?')}]: {m.get('text','')}"

        user_content = (
            f"BUYER NARRATIVE:\n{case_file.buyer.narrative}\n\n"
            f"SELLER NARRATIVE:\n{case_file.seller.narrative}\n\n"
            f"MESSAGE THREAD:\n{messages_text or '(no messages)'}"
        )

        try:
            return await structured_chat(
                messages=[
                    {"role": "system", "content": CLAIM_EXTRACTION_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                schema=ClaimExtraction,
                model=settings.active_reasoning_model,
                temperature=0.0,
            )
        except Exception as exc:
            logger.warning("claim_extraction_failed", error=str(exc))
            return ClaimExtraction(
                buyer_claims=[case_file.buyer.narrative],
                seller_claims=[case_file.seller.narrative],
            )

    def _format_evidence(self, case_file: CaseFile) -> str:
        lines = []
        for ev in case_file.evidence:
            content_preview = str(ev.content)[:300]
            lines.append(
                f"[{ev.id}] source={ev.source} type={ev.evidence_type.value} "
                f"reliability={ev.reliability:.2f}\n  {content_preview}"
            )
        if case_file.missing_evidence_gaps:
            lines.append(f"\nMISSING EVIDENCE: {', '.join(case_file.missing_evidence_gaps)}")
        return "\n".join(lines)

    async def _run_adjudication(
        self,
        case_file: CaseFile,
        claims: ClaimExtraction,
        evidence_summary: str,
        policy_text: str,
    ) -> VerdictOutput:
        prompt = ADJUDICATION_PROMPT.format(
            dispute_type=case_file.dispute_type.value,
            order_value=case_file.order_value,
            buyer_claims=json.dumps(claims.buyer_claims),
            seller_claims=json.dumps(claims.seller_claims),
            evidence_summary=evidence_summary,
            policy_text=policy_text[:3000],
        )

        try:
            return await structured_chat(
                messages=[
                    {"role": "system", "content": "You are Liquet, a precise marketplace dispute adjudicator."},
                    {"role": "user", "content": prompt},
                ],
                schema=VerdictOutput,
                model=settings.active_reasoning_model,
                temperature=0.0,
                max_tokens=2048,
            )
        except Exception as exc:
            logger.error("adjudication_llm_failed", error=str(exc))
            # Graceful degradation: produce a low-confidence escalation verdict
            return VerdictOutput(
                resolution="escalate",
                confidence=0.30,
                rationale=f"Adjudication failed due to LLM error: {exc}. Case requires human review.",
                policy_clauses=["A-001"],
                citation_evidence_ids=[],
                partial_refund_pct=None,
                hard_contradictions=[],
            )
