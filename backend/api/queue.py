"""Human review queue endpoints."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import (
    Actor, AuditEntry, Decision, DisputeStatus,
    GateResult, HumanReviewAction, HumanReviewBrief, ResolutionType, Verdict
)
from backend.repositories.database import get_session
from backend.repositories.dispute_repo import (
    AuditRepository, DecisionRepository, DisputeRepository, HumanQueueRepository
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[HumanReviewBrief])
async def list_queue(
    session: AsyncSession = Depends(get_session),
) -> list[HumanReviewBrief]:
    """Return all pending non-liquet cases awaiting human review."""
    repo = HumanQueueRepository(session)
    return await repo.list_pending()


@router.post("/{decision_id}/resolve")
async def resolve_queued_case(
    decision_id: str,
    action: HumanReviewAction,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Human reviewer approves or overrides a NON_LIQUET decision."""
    queue_repo = HumanQueueRepository(session)
    decision_repo = DecisionRepository(session)
    audit_repo = AuditRepository(session)

    # Fetch original non-liquet decision to get dispute_id
    briefs = await queue_repo.list_pending()
    brief = next((b for b in briefs if b.decision_id == decision_id), None)
    if brief is None:
        raise HTTPException(status_code=404, detail="Queued case not found or already resolved")

    # Mark as resolved in queue
    await queue_repo.mark_resolved(decision_id)

    # Save human override decision
    original = await decision_repo.get_by_dispute(brief.dispute_id)
    human_verdict = Verdict(
        resolution=action.approved_resolution,
        confidence=1.0,
        rationale=action.override_note or "Human reviewer decision",
        value_at_stake=brief.order_value,
        citations=original.verdict.citations if original else [],
        partial_refund_pct=action.partial_refund_pct,
    )
    human_decision = Decision(
        dispute_id=brief.dispute_id,
        verdict=human_verdict,
        gate_result=GateResult.LIQUET,
        actor=Actor.HUMAN_REVIEWER,
        actor_id=action.reviewer_id,
    )
    await decision_repo.save(human_decision)

    # Update dispute status
    dispute_repo = DisputeRepository(session)
    await dispute_repo.update_status(brief.dispute_id, DisputeStatus.RESOLVED)

    # Audit
    await audit_repo.append(AuditEntry(
        dispute_id=brief.dispute_id,
        event="human_review_resolved",
        actor=Actor.HUMAN_REVIEWER,
        actor_id=action.reviewer_id,
        data={
            "resolution": action.approved_resolution.value,
            "override_note": action.override_note,
            "original_decision_id": decision_id,
        },
    ))

    logger.info(
        "human_review_resolved",
        dispute_id=brief.dispute_id,
        resolution=action.approved_resolution.value,
        reviewer=action.reviewer_id,
    )
    return {
        "dispute_id": brief.dispute_id,
        "resolution": action.approved_resolution.value,
        "human_decision_id": human_decision.id,
    }
