"""Daily metrics endpoint — disputes and resolutions over the last 30 days."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.database import DecisionRow, DisputeRow, get_session

router = APIRouter()


@router.get("/api/metrics/daily")
async def daily_metrics(
    days: int = 30,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return per-day dispute submissions and resolution counts for the last N days."""
    days = max(1, min(days, 90))
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    # Daily dispute submissions
    sub_result = await session.execute(
        select(
            func.date(DisputeRow.created_at).label("day"),
            func.count().label("count"),
        )
        .where(DisputeRow.created_at >= cutoff)
        .group_by(func.date(DisputeRow.created_at))
        .order_by(func.date(DisputeRow.created_at))
    )
    submissions = [{"date": str(r.day), "count": r.count} for r in sub_result.fetchall()]

    # Daily resolutions (decisions made)
    res_result = await session.execute(
        select(
            func.date(DecisionRow.decided_at).label("day"),
            DecisionRow.gate_result,
            func.count().label("count"),
        )
        .where(DecisionRow.decided_at >= cutoff)
        .group_by(func.date(DecisionRow.decided_at), DecisionRow.gate_result)
        .order_by(func.date(DecisionRow.decided_at))
    )
    resolutions: dict[str, dict] = {}
    for r in res_result.fetchall():
        day = str(r.day)
        if day not in resolutions:
            resolutions[day] = {"date": day, "liquet": 0, "non_liquet": 0}
        key = "liquet" if r.gate_result == "LIQUET" else "non_liquet"
        resolutions[day][key] = r.count

    # Average confidence per day
    conf_result = await session.execute(
        select(
            func.date(DecisionRow.decided_at).label("day"),
            func.avg(DecisionRow.confidence).label("avg_conf"),
        )
        .where(DecisionRow.decided_at >= cutoff)
        .group_by(func.date(DecisionRow.decided_at))
        .order_by(func.date(DecisionRow.decided_at))
    )
    confidence_by_day = {
        str(r.day): round(float(r.avg_conf), 4) for r in conf_result.fetchall()
    }

    return {
        "days": days,
        "submissions": submissions,
        "resolutions": list(resolutions.values()),
        "avg_confidence_by_day": confidence_by_day,
    }
