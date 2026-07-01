"""Decision export endpoint — return full case JSON for download."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.database import get_session
from backend.repositories.dispute_repo import (
    AuditRepository, CaseFileRepository, DecisionRepository, DisputeRepository,
)

router = APIRouter()


@router.get("/api/cases/{dispute_id}/export")
async def export_case(
    dispute_id: str,
    session: AsyncSession = Depends(get_session),
) -> JSONResponse:
    """Export a complete case bundle (dispute + case file + decision + audit) as JSON."""
    dispute_repo = DisputeRepository(session)
    case_repo = CaseFileRepository(session)
    decision_repo = DecisionRepository(session)
    audit_repo = AuditRepository(session)

    dispute = await dispute_repo.get(dispute_id)
    if dispute is None:
        raise HTTPException(status_code=404, detail="Dispute not found")

    case_file = await case_repo.get(dispute_id)
    decision = await decision_repo.get_by_dispute(dispute_id)
    audit = await audit_repo.get_for_dispute(dispute_id)

    bundle = {
        "export_version": "1.0",
        "dispute": dispute.model_dump(mode="json"),
        "case_file": case_file.model_dump(mode="json") if case_file else None,
        "decision": decision.model_dump(mode="json") if decision else None,
        "audit_trail": [a.model_dump(mode="json") for a in audit],
        "metadata": {
            "dispute_id": dispute_id,
            "exported_by": "liquet-api",
        },
    }

    filename = f"liquet-case-{dispute_id[:8]}.json"
    return JSONResponse(
        content=bundle,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
