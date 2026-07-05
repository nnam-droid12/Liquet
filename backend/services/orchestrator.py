"""
Liquet Dispute Orchestrator — the autopilot loop.

Flow:
1. Gather evidence via MCP tool calls (order, logistics, listing, comms, vision)
2. Assemble CaseFile
3. Run adjudication pipeline (qwen3.7-max)
4. Apply liquet gate
5. Execute resolution OR escalate to human queue
6. Write full audit trail
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import (
    Actor, AuditEntry, CaseFile, Claim, Decision, Dispute,
    DisputeStatus, DisputeType, EvidenceItem, EvidenceType,
    GateResult, HumanReviewBrief, Party, ResolutionType, Verdict,
    EvidenceCitation, VerdictOutput, ClaimExtraction, GhostCaseResult,
)
from backend.repositories.dispute_repo import (
    AuditRepository, CaseFileRepository, DecisionRepository,
    DisputeRepository, HumanQueueRepository,
)
from backend.services.adjudicator import AdjudicationPipeline
from backend.services.ghost_cases import GhostCaseEngine
from backend.services.liquet_gate import LiquetGate
from backend.services.skeptic import SkepticEngine
from backend.services.stability import StabilityScorer
from backend.services.tool_client import ToolClient
from config import settings

logger = structlog.get_logger(__name__)


class DisputeOrchestrator:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dispute_repo = DisputeRepository(session)
        self.case_repo = CaseFileRepository(session)
        self.decision_repo = DecisionRepository(session)
        self.queue_repo = HumanQueueRepository(session)
        self.audit_repo = AuditRepository(session)
        self.tools = ToolClient()
        self.adjudicator = AdjudicationPipeline()
        self.gate = LiquetGate()
        self.ghost_engine = GhostCaseEngine(session)
        self.stability_scorer = StabilityScorer(self.adjudicator)
        self.skeptic_engine = SkepticEngine()

    async def run(self, dispute: Dispute) -> Decision:
        log = logger.bind(dispute_id=dispute.id, order_id=dispute.order_id)
        log.info("orchestrator_start")

        await self.dispute_repo.update_status(dispute.id, DisputeStatus.INVESTIGATING)
        await self._audit(dispute.id, "investigation_started", Actor.AGENT, {
            "dispute_type": dispute.dispute_type.value,
            "buyer_id": dispute.buyer_id,
        })

        # ── Phase 1: Gather evidence ──────────────────────────────────────────
        case_file = await self._assemble_case(dispute)

        # Ghost Cases — inject synthetic evidence before adjudication
        ghost_result = await self.ghost_engine.analyze(dispute)
        if ghost_result.synthetic_evidence is not None:
            case_file.evidence.append(ghost_result.synthetic_evidence)
            await self._audit(dispute.id, "ghost_cases_injected", Actor.AGENT, {
                "similar_cases": ghost_result.similar_cases_count,
                "pattern_score": round(ghost_result.pattern_match_score, 3),
                "weight": ghost_result.weight,
            })
            log.info("ghost_cases_injected",
                     similar=ghost_result.similar_cases_count,
                     pattern=ghost_result.pattern_match_score)

        await self.case_repo.save(case_file)
        await self._audit(dispute.id, "case_assembled", Actor.AGENT, {
            "evidence_count": len(case_file.evidence),
            "hard_contradictions": case_file.hard_contradictions,
        })

        # ── Phase 2: Extract claims (shared across adjudication + stability) ──
        claims = await self.adjudicator._extract_claims(case_file)
        await self._audit(dispute.id, "claims_extracted", Actor.AGENT, {
            "buyer_claims": len(claims.buyer_claims),
            "seller_claims": len(claims.seller_claims),
        })

        # ── Phase 3: Verdict Stability Scoring ───────────────────────────────
        stability_result = await self.stability_scorer.score(case_file, claims)
        await self._audit(dispute.id, "stability_scored", Actor.AGENT, {
            "stability_score": stability_result.stability_score,
            "effective_confidence": stability_result.effective_confidence,
            "is_stable": stability_result.is_stable,
            "distribution": stability_result.verdict_distribution,
        })
        log.info("stability_scored",
                 score=stability_result.stability_score,
                 effective_conf=stability_result.effective_confidence)

        # ── Phase 4: Final adjudication ───────────────────────────────────────
        verdict = await self.adjudicator.adjudicate_with_claims(case_file, claims)
        await self._audit(dispute.id, "verdict_produced", Actor.AGENT, {
            "resolution": verdict.resolution.value,
            "confidence": verdict.confidence,
            "effective_confidence": stability_result.effective_confidence,
            "policy_clauses": verdict.policy_clauses,
        })
        log.info("verdict_produced",
                 resolution=verdict.resolution.value,
                 confidence=verdict.confidence)

        # ── Phase 5: Skeptic Pass ─────────────────────────────────────────────
        skeptic_result = await self.skeptic_engine.challenge(case_file, verdict)
        await self._audit(dispute.id, "skeptic_complete", Actor.AGENT, {
            "rebuttal_strength": skeptic_result.rebuttal_strength,
            "verdict_contested": skeptic_result.verdict_contested,
            "summary": skeptic_result.contest_summary,
        })
        log.info("skeptic_complete",
                 contested=skeptic_result.verdict_contested,
                 strength=skeptic_result.rebuttal_strength)

        # ── Phase 6: Liquet gate (stability + skeptic aware) ─────────────────
        gate_result, abstention_reason = self.gate.evaluate(
            verdict, case_file,
            stability=stability_result,
            skeptic=skeptic_result,
        )
        log.info("gate_evaluated", result=gate_result.value)

        decision = Decision(
            dispute_id=dispute.id,
            verdict=verdict,
            gate_result=gate_result,
            abstention_reason=abstention_reason,
            actor=Actor.AGENT,
            ghost_case_result=ghost_result,
            stability_result=stability_result,
            skeptic_result=skeptic_result,
        )
        await self.decision_repo.save(decision)

        if gate_result == GateResult.LIQUET:
            await self._execute_resolution(dispute, case_file, verdict)
            await self.dispute_repo.update_status(dispute.id, DisputeStatus.RESOLVED)
            await self._audit(dispute.id, "auto_resolved", Actor.AGENT, {
                "gate": "LIQUET",
                "resolution": verdict.resolution.value,
            })
            try:
                from backend.services.resolution_executor import notify_resolution
                await notify_resolution(
                    dispute_id=dispute.id,
                    order_id=dispute.order_id,
                    resolution=verdict.resolution.value,
                    confidence=verdict.confidence,
                    rationale=verdict.rationale,
                    amount=case_file.order_value,
                    buyer_id=dispute.buyer_id,
                    seller_id=dispute.seller_id,
                    buyer_email=dispute.metadata.get("reply_to", ""),
                )
            except Exception as exc:
                log.warning("resolution_notify_failed", error=str(exc))
        else:
            await self._escalate_to_human(dispute, case_file, verdict, decision, abstention_reason)
            await self.dispute_repo.update_status(dispute.id, DisputeStatus.ESCALATED)
            await self._audit(dispute.id, "escalated_to_human", Actor.AGENT, {
                "gate": "NON_LIQUET",
                "reason": abstention_reason,
            })
            try:
                from backend.services.resolution_executor import notify_escalation
                await notify_escalation(
                    dispute_id=dispute.id,
                    decision_id=decision.id,
                    order_id=dispute.order_id,
                    order_value=case_file.order_value,
                    dispute_type=dispute.dispute_type.value,
                    leaning_verdict=verdict.resolution.value,
                    leaning_confidence=verdict.confidence,
                    abstention_reason=abstention_reason or "Confidence below threshold",
                    buyer_narrative=dispute.buyer_narrative,
                    seller_narrative=dispute.seller_narrative or "",
                )
            except Exception as exc:
                log.warning("escalation_notify_failed", error=str(exc))

        log.info("orchestrator_complete", gate=gate_result.value)
        return decision

    async def _assemble_case(self, dispute: Dispute) -> CaseFile:
        evidence: list[EvidenceItem] = []
        hard_contradictions: list[str] = []
        missing_gaps: list[str] = []

        # Order record
        order_data = await self.tools.get_order(dispute.order_id)
        if "error" not in order_data:
            evidence.append(EvidenceItem.from_type(
                source="order_service",
                evidence_type=EvidenceType.ORDER_RECORD,
                content=order_data,
            ))
        else:
            missing_gaps.append(f"Order record not found for {dispute.order_id}")

        order_value = order_data.get("price", 0.0) if "error" not in order_data else 0.0
        product_id = order_data.get("product_id", "")

        # Tracking
        tracking_data = await self.tools.get_tracking(dispute.order_id)
        if "error" not in tracking_data:
            evidence.append(EvidenceItem.from_type(
                source="logistics_service",
                evidence_type=EvidenceType.CARRIER_SCAN,
                content=tracking_data,
            ))
        else:
            missing_gaps.append(f"Tracking record not found for {dispute.order_id}")
            logger.warning("tracking_missing", order_id=dispute.order_id)

        # Listing — fetched once, reused below
        listing_data: dict = {}
        if product_id:
            listing_data = await self.tools.get_listing(product_id)
            if "error" not in listing_data:
                evidence.append(EvidenceItem.from_type(
                    source="listing_service",
                    evidence_type=EvidenceType.LISTING_DATA,
                    content=listing_data,
                ))
            else:
                missing_gaps.append(f"Listing not found for product {product_id}")

        # Messages
        messages = await self.tools.get_messages(dispute.order_id)
        if messages:
            evidence.append(EvidenceItem.from_type(
                source="comms_service",
                evidence_type=EvidenceType.MESSAGE,
                content=messages,
            ))

        # Evidence images from metadata — use listing_data already fetched above
        image_urls: list[str] = dispute.metadata.get("evidence_images", [])
        listing_desc = listing_data.get("description", "")
        for i, url in enumerate(image_urls):
            vision_result = await self.tools.analyze_image(url, listing_desc)
            ev_type = EvidenceType.PHOTO
            evidence.append(EvidenceItem(
                source=f"vision_intake_photo_{i+1}",
                evidence_type=ev_type,
                reliability=0.65 if not vision_result.get("error") else 0.30,
                content=vision_result,
                metadata={"image_url": url},
            ))

        # Policy signal
        case_summary = {
            "order_value": order_value,
            "dispute_type": dispute.dispute_type.value,
            "delivered": tracking_data.get("status") == "delivered" if "error" not in tracking_data else None,
            "tracking_missing": "error" in tracking_data,
            "damage_in_photos": any(
                e.content.get("damage_detected", False)
                for e in evidence if e.evidence_type == EvidenceType.PHOTO
            ),
            "color_mismatch": any(
                "grey" in str(e.content).lower() or "gray" in str(e.content).lower()
                for e in evidence if e.evidence_type == EvidenceType.PHOTO
            ),
            "wrong_item": dispute.dispute_type == DisputeType.WRONG_ITEM,
        }
        policy_result = await self.tools.evaluate_policy(case_summary)

        buyer = Party(
            user_id=dispute.buyer_id,
            role="buyer",
            narrative=dispute.buyer_narrative,
        )
        seller = Party(
            user_id=dispute.seller_id,
            role="seller",
            narrative=dispute.seller_narrative,
        )

        return CaseFile(
            dispute_id=dispute.id,
            order_id=dispute.order_id,
            order_value=order_value,
            dispute_type=dispute.dispute_type,
            buyer=buyer,
            seller=seller,
            evidence=evidence,
            hard_contradictions=hard_contradictions,
            missing_evidence_gaps=missing_gaps,
        )

    async def _execute_resolution(self, dispute: Dispute, case_file: CaseFile, verdict: Verdict) -> None:
        resolution = verdict.resolution
        order_id = dispute.order_id
        buyer_id = dispute.buyer_id
        seller_id = dispute.seller_id
        amount = case_file.order_value

        if resolution == ResolutionType.FULL_REFUND:
            await self.tools.issue_full_refund(dispute.id, order_id, amount, buyer_id)
        elif resolution == ResolutionType.PARTIAL_REFUND:
            pct = verdict.partial_refund_pct or 0.5
            await self.tools.issue_partial_refund(dispute.id, order_id, amount, pct, buyer_id, verdict.rationale[:200])
        elif resolution == ResolutionType.REPLACEMENT:
            await self.tools.initiate_replacement(dispute.id, order_id, buyer_id, seller_id)
        elif resolution == ResolutionType.RETURN_THEN_REFUND:
            await self.tools.initiate_return_then_refund(dispute.id, order_id, buyer_id, seller_id, amount)
        elif resolution == ResolutionType.DENY:
            await self.tools.deny_claim(dispute.id, order_id, buyer_id, verdict.rationale[:200])

    async def _escalate_to_human(
        self,
        dispute: Dispute,
        case_file: CaseFile,
        verdict: Verdict,
        decision: Decision,
        abstention_reason: Optional[str],
    ) -> None:
        evidence_summary = [
            {
                "id": e.id,
                "source": e.source,
                "type": e.evidence_type.value,
                "reliability": e.reliability,
                "summary": str(e.content)[:200],
            }
            for e in case_file.evidence
        ]

        brief = HumanReviewBrief(
            decision_id=decision.id,
            dispute_id=dispute.id,
            order_value=case_file.order_value,
            dispute_type=dispute.dispute_type,
            buyer_narrative=dispute.buyer_narrative,
            seller_narrative=dispute.seller_narrative,
            evidence_summary=evidence_summary,
            leaning_verdict=verdict.resolution,
            leaning_confidence=verdict.confidence,
            abstention_reason=abstention_reason or "Confidence below threshold",
            hard_contradictions=case_file.hard_contradictions,
            missing_gaps=case_file.missing_evidence_gaps,
        )
        await self.queue_repo.enqueue(brief)

    async def _audit(self, dispute_id: str, event: str, actor: Actor, data: dict) -> None:
        await self.audit_repo.append(AuditEntry(
            dispute_id=dispute_id,
            event=event,
            actor=actor,
            data=data,
        ))
