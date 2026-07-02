"""Seller risk analytics — surfaces sellers with recurring dispute patterns."""

from __future__ import annotations

from collections import Counter, defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.database import DecisionRow, DisputeRow, get_session

router = APIRouter()


@router.get("/api/seller-risk")
async def get_seller_risk(session: AsyncSession = Depends(get_session)) -> list[dict]:
    """
    Aggregate dispute history by seller. Returns sellers ranked by dispute volume
    and pattern concentration — the same data Ghost Cases injects per-case.
    """
    result = await session.execute(select(DisputeRow))
    all_disputes = result.scalars().all()

    seller_map: dict[str, list] = defaultdict(list)
    for d in all_disputes:
        seller_map[d.seller_id].append(d)

    platform_total = len(all_disputes)

    sellers = []
    for seller_id, disputes in seller_map.items():
        if len(disputes) < 1:
            continue

        type_counts = Counter(d.dispute_type for d in disputes)
        status_counts = Counter(d.status for d in disputes)

        most_common_type = type_counts.most_common(1)[0] if type_counts else ("unknown", 0)
        pattern_score = most_common_type[1] / max(len(disputes), 1)

        resolved = status_counts.get("resolved", 0)
        escalated = status_counts.get("escalated", 0)
        investigated = resolved + escalated

        sellers.append({
            "seller_id": seller_id,
            "total_disputes": len(disputes),
            "platform_share": round(len(disputes) / max(platform_total, 1), 4),
            "dominant_type": most_common_type[0],
            "pattern_score": round(pattern_score, 4),
            "resolved": resolved,
            "escalated": escalated,
            "auto_resolution_rate": round(resolved / max(investigated, 1), 4),
            "type_breakdown": dict(type_counts),
            "status_breakdown": dict(status_counts),
            "risk_level": (
                "HIGH" if len(disputes) >= 5 and pattern_score >= 0.7 else
                "MEDIUM" if len(disputes) >= 3 or pattern_score >= 0.5 else
                "LOW"
            ),
        })

    return sorted(sellers, key=lambda s: (-s["total_disputes"], -s["pattern_score"]))


@router.get("/api/seller-risk/{seller_id}")
async def get_seller_risk_detail(
    seller_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return detailed dispute history for a single seller."""
    result = await session.execute(
        select(DisputeRow).where(DisputeRow.seller_id == seller_id)
    )
    disputes = result.scalars().all()

    if not disputes:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Seller not found or no disputes")

    type_counts = Counter(d.dispute_type for d in disputes)
    status_counts = Counter(d.status for d in disputes)
    most_common_type = type_counts.most_common(1)[0] if type_counts else ("unknown", 0)
    pattern_score = most_common_type[1] / max(len(disputes), 1)

    resolved = status_counts.get("resolved", 0)
    escalated = status_counts.get("escalated", 0)

    dispute_list = [
        {
            "id": d.id,
            "order_id": d.order_id,
            "dispute_type": d.dispute_type,
            "status": d.status,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in sorted(disputes, key=lambda x: x.created_at or "", reverse=True)
    ]

    return {
        "seller_id": seller_id,
        "total_disputes": len(disputes),
        "dominant_type": most_common_type[0],
        "pattern_score": round(pattern_score, 4),
        "resolved": resolved,
        "escalated": escalated,
        "auto_resolution_rate": round(resolved / max(resolved + escalated, 1), 4),
        "type_breakdown": dict(type_counts),
        "status_breakdown": dict(status_counts),
        "risk_level": (
            "HIGH" if len(disputes) >= 5 and pattern_score >= 0.7 else
            "MEDIUM" if len(disputes) >= 3 or pattern_score >= 0.5 else
            "LOW"
        ),
        "disputes": dispute_list,
    }
