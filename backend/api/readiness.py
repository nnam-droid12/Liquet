"""Kubernetes-style readiness and liveness probes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.database import get_session

router = APIRouter(tags=["health"])


@router.get("/ready")
async def readiness(session: AsyncSession = Depends(get_session)) -> dict:
    """Readiness probe: checks database connectivity."""
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    status = "ready" if db_ok else "not_ready"
    return {"status": status, "database": "ok" if db_ok else "error"}


@router.get("/live")
async def liveness() -> dict:
    """Liveness probe: confirms process is alive."""
    return {"status": "alive"}
