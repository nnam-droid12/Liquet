"""Daily digest endpoint — summary suitable for email or webhook delivery."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.database import DecisionRow, DisputeRow, get_session

router = APIRouter()


@router.get("/api/digest/daily")
async def daily_digest(session: AsyncSession = Depends(get_session)) -> dict:
    """
    Return a human-readable daily digest covering the last 24 hours:
    new disputes, decisions made, auto-resolution rate, and any failed investigations.
    """
    since = datetime.datetime.utcnow() - datetime.timedelta(hours=24)

    new_disputes = await session.execute(
        select(func.count()).select_from(DisputeRow).where(DisputeRow.created_at >= since)
    )
    decisions_made = await session.execute(
        select(func.count()).select_from(DecisionRow).where(DecisionRow.decided_at >= since)
    )
    liquet_today = await session.execute(
        select(func.count()).select_from(DecisionRow)
        .where(DecisionRow.decided_at >= since, DecisionRow.gate_result == "LIQUET")
    )
    failed_today = await session.execute(
        select(func.count()).select_from(DisputeRow)
        .where(DisputeRow.updated_at >= since, DisputeRow.status == "failed")
    )

    n_new = new_disputes.scalar() or 0
    n_decisions = decisions_made.scalar() or 0
    n_liquet = liquet_today.scalar() or 0
    n_failed = failed_today.scalar() or 0
    auto_rate = round(n_liquet / max(n_decisions, 1), 4)

    return {
        "period": "last_24h",
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "new_disputes": n_new,
        "decisions_made": n_decisions,
        "auto_resolved": n_liquet,
        "escalated": n_decisions - n_liquet,
        "failed_investigations": n_failed,
        "auto_resolution_rate": auto_rate,
        "summary": (
            f"{n_new} new dispute{'s' if n_new != 1 else ''} in the last 24h. "
            f"{n_decisions} investigated: {n_liquet} auto-resolved (LIQUET), "
            f"{n_decisions - n_liquet} escalated (NON LIQUET). "
            f"{n_failed} failed."
        ),
    }
