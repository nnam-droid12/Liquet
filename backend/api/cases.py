"""Case file and decision endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import AuditEntry, CaseFile, Decision
from backend.repositories.database import get_session
from backend.repositories.dispute_repo import AuditRepository, CaseFileRepository, DecisionRepository

router = APIRouter()


@router.get("/{dispute_id}/casefile", response_model=CaseFile)
async def get_case_file(
    dispute_id: str,
    session: AsyncSession = Depends(get_session),
) -> CaseFile:
    repo = CaseFileRepository(session)
    case_file = await repo.get(dispute_id)
    if case_file is None:
        raise HTTPException(status_code=404, detail="CaseFile not found")
    return case_file


@router.get("/{dispute_id}/decision", response_model=Decision)
async def get_decision(
    dispute_id: str,
    session: AsyncSession = Depends(get_session),
) -> Decision:
    repo = DecisionRepository(session)
    decision = await repo.get_by_dispute(dispute_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@router.get("/{dispute_id}/summary")
async def get_case_summary(
    dispute_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return a lightweight summary card for a resolved case."""
    case_repo = CaseFileRepository(session)
    decision_repo = DecisionRepository(session)
    case_file = await case_repo.get(dispute_id)
    decision = await decision_repo.get_by_dispute(dispute_id)

    if case_file is None and decision is None:
        raise HTTPException(status_code=404, detail="No data found for this dispute")

    return {
        "dispute_id": dispute_id,
        "order_value": case_file.order_value if case_file else None,
        "dispute_type": case_file.dispute_type.value if case_file else None,
        "evidence_count": len(case_file.evidence) if case_file else 0,
        "hard_contradictions": len(case_file.hard_contradictions) if case_file else 0,
        "gate_result": decision.gate_result.value if decision else None,
        "resolution": decision.verdict.resolution.value if decision else None,
        "confidence": decision.verdict.confidence if decision else None,
        "has_ghost_cases": bool(decision and decision.ghost_case_result and decision.ghost_case_result.synthetic_evidence),
        "stability_score": decision.stability_result.stability_score if decision and decision.stability_result else None,
        "skeptic_contested": decision.skeptic_result.verdict_contested if decision and decision.skeptic_result else None,
    }


@router.get("/{dispute_id}/claims")
async def get_claims(
    dispute_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return extracted buyer and seller claims from the assembled case file."""
    repo = CaseFileRepository(session)
    case_file = await repo.get(dispute_id)
    if case_file is None:
        raise HTTPException(status_code=404, detail="CaseFile not found — run investigation first")
    buyer_claims = [c.model_dump() for c in case_file.buyer.claims]
    seller_claims = [c.model_dump() for c in case_file.seller.claims]
    return {
        "dispute_id": dispute_id,
        "buyer_claims": buyer_claims,
        "seller_claims": seller_claims,
        "total": len(buyer_claims) + len(seller_claims),
    }


@router.get("/{dispute_id}/audit", response_model=list[AuditEntry])
async def get_audit(
    dispute_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[AuditEntry]:
    repo = AuditRepository(session)
    return await repo.get_for_dispute(dispute_id)
