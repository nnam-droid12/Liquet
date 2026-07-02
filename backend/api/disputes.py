"""Dispute management endpoints."""

from __future__ import annotations

import datetime
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import Dispute, DisputeCreate, DisputeStatus
from backend.repositories.database import DisputeRow, get_session
from backend.repositories.dispute_repo import DisputeRepository
from backend.services.orchestrator import DisputeOrchestrator

logger = structlog.get_logger(__name__)
router = APIRouter()


class DisputePatch(BaseModel):
    seller_narrative: Optional[str] = None
    order_value_hint: Optional[float] = None


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
    buyer_id: Optional[str] = None,
    seller_id: Optional[str] = None,
    dispute_type: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> list[Dispute]:
    repo = DisputeRepository(session)
    disputes = await repo.list_all(status=status)
    if buyer_id:
        disputes = [d for d in disputes if d.buyer_id == buyer_id]
    if seller_id:
        disputes = [d for d in disputes if d.seller_id == seller_id]
    if dispute_type:
        disputes = [d for d in disputes if d.dispute_type.value == dispute_type]
    return disputes


@router.get("/count")
async def count_disputes(
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return a lightweight count of disputes, optionally filtered by status."""
    from sqlalchemy import func
    q = select(func.count()).select_from(DisputeRow)
    if status:
        q = q.where(DisputeRow.status == status)
    result = await session.execute(q)
    return {"count": result.scalar() or 0, "status": status or "all"}


@router.get("/recent", response_model=list[Dispute])
async def list_recent_disputes(
    limit: int = 5,
    session: AsyncSession = Depends(get_session),
) -> list[Dispute]:
    """Return the N most recently created disputes."""
    from sqlalchemy import desc
    limit = max(1, min(limit, 50))
    result = await session.execute(
        select(DisputeRow).order_by(desc(DisputeRow.created_at)).limit(limit)
    )
    repo = DisputeRepository(session)
    return [repo._row_to_model(r) for r in result.scalars()]


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


@router.delete("/{dispute_id}", status_code=204)
async def close_dispute(
    dispute_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Soft-close a dispute (status → closed). Does not delete the record."""
    repo = DisputeRepository(session)
    dispute = await repo.get(dispute_id)
    if dispute is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if dispute.status == DisputeStatus.CLOSED:
        return  # idempotent
    await repo.update_status(dispute_id, DisputeStatus.CLOSED)
    logger.info("dispute_closed", dispute_id=dispute_id)


@router.patch("/{dispute_id}", response_model=Dispute)
async def patch_dispute(
    dispute_id: str,
    patch: DisputePatch,
    session: AsyncSession = Depends(get_session),
) -> Dispute:
    """Update mutable fields on an open dispute (e.g. seller adds their response)."""
    repo = DisputeRepository(session)
    dispute = await repo.get(dispute_id)
    if dispute is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if dispute.status not in (DisputeStatus.OPEN, DisputeStatus.INVESTIGATING):
        raise HTTPException(status_code=409, detail="Cannot patch a closed or resolved dispute")

    values: dict = {"updated_at": datetime.datetime.utcnow()}
    if patch.seller_narrative is not None:
        values["seller_narrative"] = patch.seller_narrative
    if patch.order_value_hint is not None:
        meta = dict(dispute.metadata)
        meta["order_value_hint"] = patch.order_value_hint
        values["metadata_json"] = meta

    await session.execute(
        update(DisputeRow).where(DisputeRow.id == dispute_id).values(**values)
    )
    await session.commit()
    logger.info("dispute_patched", dispute_id=dispute_id, fields=list(values.keys()))
    return await repo.get(dispute_id)


MAX_RETRY_ATTEMPTS = 3


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
    if dispute.status not in (DisputeStatus.OPEN, DisputeStatus.INVESTIGATING, DisputeStatus.FAILED):
        raise HTTPException(status_code=409, detail=f"Dispute already in status: {dispute.status}")

    retry_count = int(dispute.metadata.get("retry_count", 0))
    if retry_count >= MAX_RETRY_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail=f"Max retry attempts ({MAX_RETRY_ATTEMPTS}) reached. Close and reopen the dispute to reset.",
        )

    # Increment retry counter in metadata
    await session.execute(
        update(DisputeRow)
        .where(DisputeRow.id == dispute_id)
        .values(metadata_json={**dispute.metadata, "retry_count": retry_count + 1})
    )
    await session.commit()

    orchestrator = DisputeOrchestrator(session)
    try:
        decision = await orchestrator.run(dispute)
    except Exception as exc:
        logger.error("investigation_failed", dispute_id=dispute_id, error=str(exc))
        await repo.update_status(dispute_id, DisputeStatus.FAILED)
        raise HTTPException(status_code=500, detail=f"Investigation failed: {exc}") from exc
    return {
        "dispute_id": dispute_id,
        "gate_result": decision.gate_result.value,
        "resolution": decision.verdict.resolution.value,
        "confidence": decision.verdict.confidence,
        "decision_id": decision.id,
    }
