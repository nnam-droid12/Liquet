"""Platform stats endpoint — powers the landing page live counters."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.database import DecisionRow, DisputeRow, get_session

router = APIRouter()


@router.get("/api/stats")
async def get_stats(session: AsyncSession = Depends(get_session)) -> dict:
    """Return platform-wide stats for the landing page."""

    # Total disputes
    total_result = await session.execute(select(func.count()).select_from(DisputeRow))
    total = total_result.scalar() or 0

    # By status
    status_result = await session.execute(
        select(DisputeRow.status, func.count()).group_by(DisputeRow.status)
    )
    status_counts = {row[0]: row[1] for row in status_result.fetchall()}

    resolved = status_counts.get("resolved", 0)
    escalated = status_counts.get("escalated", 0)
    investigated = resolved + escalated

    # Average confidence (from decisions)
    conf_result = await session.execute(
        select(func.avg(DecisionRow.confidence)).select_from(DecisionRow)
    )
    avg_confidence = conf_result.scalar() or 0.0

    # Auto-resolution rate
    auto_rate = resolved / max(investigated, 1)

    # LIQUET vs NON_LIQUET counts
    gate_result = await session.execute(
        select(DecisionRow.gate_result, func.count()).group_by(DecisionRow.gate_result)
    )
    gate_counts = {row[0]: row[1] for row in gate_result.fetchall()}

    # Dispute type breakdown
    type_result = await session.execute(
        select(DisputeRow.dispute_type, func.count()).group_by(DisputeRow.dispute_type)
    )
    type_counts = {row[0]: row[1] for row in type_result.fetchall()}

    return {
        "total_disputes": total,
        "resolved": resolved,
        "escalated": escalated,
        "open": status_counts.get("open", 0),
        "investigating": status_counts.get("investigating", 0),
        "auto_resolution_rate": round(auto_rate, 4),
        "avg_confidence": round(float(avg_confidence), 4),
        "gate_counts": gate_counts,
        "dispute_type_breakdown": type_counts,
    }
