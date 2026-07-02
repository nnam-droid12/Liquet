"""Full-text search across disputes by keyword."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import Dispute
from backend.repositories.database import DisputeRow, get_session
from backend.repositories.dispute_repo import DisputeRepository

router = APIRouter()


@router.get("/api/search")
async def search_disputes(
    q: str,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Full-text search across order IDs, buyer and seller narratives.
    Returns matching disputes ranked by relevance (order_id match first).
    """
    if not q or len(q.strip()) < 2:
        return {"query": q, "results": [], "total": 0}

    term = f"%{q.strip().lower()}%"
    limit = max(1, min(limit, 100))

    result = await session.execute(
        select(DisputeRow).where(
            or_(
                DisputeRow.order_id.ilike(term),
                DisputeRow.buyer_narrative.ilike(term),
                DisputeRow.seller_narrative.ilike(term),
                DisputeRow.buyer_id.ilike(term),
                DisputeRow.seller_id.ilike(term),
                DisputeRow.dispute_type.ilike(term),
            )
        ).limit(limit)
    )
    rows = result.scalars().all()
    repo = DisputeRepository(session)
    disputes = [repo._row_to_model(r) for r in rows]

    # Sort: exact order_id matches first
    disputes.sort(key=lambda d: (0 if q.lower() in d.order_id.lower() else 1, d.created_at), reverse=False)

    return {
        "query": q,
        "results": [d.model_dump(mode="json") for d in disputes],
        "total": len(disputes),
    }
