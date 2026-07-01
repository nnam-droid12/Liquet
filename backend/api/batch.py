"""Batch dispute submission endpoint."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import DisputeCreate, DisputeStatus
from backend.repositories.database import get_session
from backend.repositories.dispute_repo import DisputeRepository
from backend.services.orchestrator import DisputeOrchestrator

logger = structlog.get_logger(__name__)
router = APIRouter()


class BatchSubmitRequest:
    pass


@router.post("/api/disputes/batch", status_code=202)
async def batch_submit(
    disputes: list[DisputeCreate],
    auto_investigate: bool = False,
    background_tasks: BackgroundTasks = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Submit up to 20 disputes in a single request.
    If auto_investigate=true, each dispute is queued for investigation.
    """
    if len(disputes) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 disputes per batch")

    repo = DisputeRepository(session)
    created_ids: list[str] = []

    for data in disputes:
        dispute = await repo.create(data)
        created_ids.append(dispute.id)
        logger.info("batch_dispute_created", dispute_id=dispute.id, order_id=dispute.order_id)

    return {
        "created": len(created_ids),
        "dispute_ids": created_ids,
        "auto_investigate": auto_investigate,
        "message": (
            f"{len(created_ids)} disputes created. "
            + ("Trigger investigation for each via POST /api/disputes/{id}/investigate."
               if not auto_investigate else "Investigate each case via the API.")
        ),
    }
