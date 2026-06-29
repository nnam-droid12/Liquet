"""Dispute management endpoints."""

from __future__ import annotations

from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import Dispute, DisputeCreate, DisputeStatus
from backend.repositories.database import get_session
from backend.repositories.dispute_repo import DisputeRepository
from backend.services.orchestrator import DisputeOrchestrator

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=Dispute, status_code=201)
async def create_dispute(
    data: DisputeCreate,
    session: AsyncSession = Depends(get_session),
) -> Dispute:
    repo = DisputeRepository(session)
    dispute = await repo.create(data)
    logger.info("dispute_created", dispute_id=dispute.id, order_id=dispute.order_id)
    return dispute


@router.get("/", response_model=list[Dispute])
async def list_disputes(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> list[Dispute]:
    repo = DisputeRepository(session)
    return await repo.list_all(status=status)


@router.get("/{dispute_id}", response_model=Dispute)
async def get_dispute(
    dispute_id: str,
    session: AsyncSession = Depends(get_session),
) -> Dispute:
    repo = DisputeRepository(session)
    dispute = await repo.get(dispute_id)
    if dispute is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return dispute


@router.post("/{dispute_id}/investigate", status_code=202)
async def investigate_dispute(
    dispute_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Trigger the autopilot agent to investigate and resolve a dispute."""
    repo = DisputeRepository(session)
    dispute = await repo.get(dispute_id)
    if dispute is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if dispute.status not in (DisputeStatus.OPEN, DisputeStatus.INVESTIGATING):
        raise HTTPException(status_code=409, detail=f"Dispute already in status: {dispute.status}")

    orchestrator = DisputeOrchestrator(session)
    decision = await orchestrator.run(dispute)
    return {
        "dispute_id": dispute_id,
        "gate_result": decision.gate_result.value,
        "resolution": decision.verdict.resolution.value,
        "confidence": decision.verdict.confidence,
        "decision_id": decision.id,
    }
