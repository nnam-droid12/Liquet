"""Platform stats and confidence histogram endpoints."""

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


@router.get("/api/stats/confidence-histogram")
async def confidence_histogram(
    buckets: int = 10,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return a histogram of verdict confidence scores across all decisions."""
    from sqlalchemy import text

    buckets = max(2, min(buckets, 20))
    result = await session.execute(
        select(DecisionRow.confidence).select_from(DecisionRow)
    )
    scores = [float(r) for r in result.scalars() if r is not None]

    if not scores:
        return {"buckets": buckets, "histogram": [], "min": 0, "max": 0, "mean": 0}

    step = 1.0 / buckets
    hist = [0] * buckets
    for s in scores:
        idx = min(int(s / step), buckets - 1)
        hist[idx] += 1

    labels = [f"{i/buckets:.0%}–{(i+1)/buckets:.0%}" for i in range(buckets)]

    return {
        "buckets": buckets,
        "histogram": [{"range": labels[i], "count": hist[i]} for i in range(buckets)],
        "min": round(min(scores), 4),
        "max": round(max(scores), 4),
        "mean": round(sum(scores) / len(scores), 4),
        "total": len(scores),
    }
