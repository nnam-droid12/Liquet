"""Case notes endpoint — human reviewers can append freetext notes to a case audit."""

from __future__ import annotations

from pydantic import BaseModel
import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import Actor, AuditEntry
from backend.repositories.database import get_session
from backend.repositories.dispute_repo import AuditRepository, DisputeRepository

logger = structlog.get_logger(__name__)
router = APIRouter()


class NoteCreate(BaseModel):
    reviewer_id: str
    note: str


@router.post("/api/cases/{dispute_id}/notes", status_code=201)
async def add_note(
    dispute_id: str,
    body: NoteCreate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Append a human reviewer note to the case audit trail."""
    dispute_repo = DisputeRepository(session)
    if await dispute_repo.get(dispute_id) is None:
        raise HTTPException(status_code=404, detail="Dispute not found")

    audit_repo = AuditRepository(session)
    entry = AuditEntry(
        dispute_id=dispute_id,
        event="reviewer_note",
        actor=Actor.HUMAN_REVIEWER,
        actor_id=body.reviewer_id,
        data={"note": body.note},
    )
    await audit_repo.append(entry)
    logger.info("reviewer_note_added", dispute_id=dispute_id, reviewer=body.reviewer_id)
    return {"id": entry.id, "dispute_id": dispute_id, "event": "reviewer_note"}
