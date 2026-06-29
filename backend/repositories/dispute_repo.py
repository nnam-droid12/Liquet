"""Repository for Dispute and Decision persistence."""

from __future__ import annotations

import datetime
import json
from typing import Optional

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import (
    AuditEntry, CaseFile, Decision, Dispute, DisputeCreate,
    DisputeStatus, GateResult, HumanReviewBrief
)
from backend.repositories.database import (
    AuditRow, CaseFileRow, DecisionRow, DisputeRow, HumanQueueRow
)

logger = structlog.get_logger(__name__)


class DisputeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: DisputeCreate) -> Dispute:
        dispute = Dispute(**data.model_dump())
        row = DisputeRow(
            id=dispute.id,
            order_id=dispute.order_id,
            dispute_type=dispute.dispute_type.value,
            status=dispute.status.value,
            buyer_id=dispute.buyer_id,
            seller_id=dispute.seller_id,
            buyer_narrative=dispute.buyer_narrative,
            seller_narrative=dispute.seller_narrative,
            metadata_json=dispute.metadata,
        )
        self.session.add(row)
        await self.session.commit()
        return dispute

    async def get(self, dispute_id: str) -> Optional[Dispute]:
        result = await self.session.execute(
            select(DisputeRow).where(DisputeRow.id == dispute_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._row_to_model(row)

    async def get_by_order_id(self, order_id: str) -> Optional[Dispute]:
        result = await self.session.execute(
            select(DisputeRow).where(DisputeRow.order_id == order_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._row_to_model(row)

    async def list_all(self, status: Optional[str] = None) -> list[Dispute]:
        q = select(DisputeRow)
        if status:
            q = q.where(DisputeRow.status == status)
        result = await self.session.execute(q)
        return [self._row_to_model(r) for r in result.scalars()]

    async def update_status(self, dispute_id: str, status: DisputeStatus) -> None:
        await self.session.execute(
            update(DisputeRow)
            .where(DisputeRow.id == dispute_id)
            .values(status=status.value, updated_at=datetime.datetime.utcnow())
        )
        await self.session.commit()

    def _row_to_model(self, row: DisputeRow) -> Dispute:
        return Dispute(
            id=row.id,
            order_id=row.order_id,
            dispute_type=row.dispute_type,
            status=row.status,
            buyer_id=row.buyer_id,
            seller_id=row.seller_id,
            buyer_narrative=row.buyer_narrative,
            seller_narrative=row.seller_narrative,
            metadata=row.metadata_json or {},
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class CaseFileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, case_file: CaseFile) -> None:
        row = CaseFileRow(
            dispute_id=case_file.dispute_id,
            order_value=case_file.order_value,
            case_json=case_file.model_dump(mode="json"),
        )
        await self.session.merge(row)
        await self.session.commit()

    async def get(self, dispute_id: str) -> Optional[CaseFile]:
        result = await self.session.execute(
            select(CaseFileRow).where(CaseFileRow.dispute_id == dispute_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return CaseFile.model_validate(row.case_json)


class DecisionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, decision: Decision) -> None:
        row = DecisionRow(
            id=decision.id,
            dispute_id=decision.dispute_id,
            gate_result=decision.gate_result.value,
            resolution=decision.verdict.resolution.value,
            confidence=decision.verdict.confidence,
            actor=decision.actor.value,
            decision_json=decision.model_dump(mode="json"),
        )
        self.session.add(row)
        await self.session.commit()

    async def get_by_dispute(self, dispute_id: str) -> Optional[Decision]:
        result = await self.session.execute(
            select(DecisionRow).where(DecisionRow.dispute_id == dispute_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return Decision.model_validate(row.decision_json)


class HumanQueueRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def enqueue(self, brief: HumanReviewBrief) -> None:
        row = HumanQueueRow(
            decision_id=brief.decision_id,
            dispute_id=brief.dispute_id,
            brief_json=brief.model_dump(mode="json"),
            resolved=False,
        )
        self.session.add(row)
        await self.session.commit()

    async def list_pending(self) -> list[HumanReviewBrief]:
        result = await self.session.execute(
            select(HumanQueueRow).where(HumanQueueRow.resolved == False)  # noqa: E712
        )
        return [HumanReviewBrief.model_validate(r.brief_json) for r in result.scalars()]

    async def mark_resolved(self, decision_id: str) -> None:
        await self.session.execute(
            update(HumanQueueRow)
            .where(HumanQueueRow.decision_id == decision_id)
            .values(resolved=True)
        )
        await self.session.commit()


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def append(self, entry: AuditEntry) -> None:
        row = AuditRow(
            id=entry.id,
            dispute_id=entry.dispute_id,
            event=entry.event,
            actor=entry.actor.value,
            actor_id=entry.actor_id,
            data_json=entry.data,
        )
        self.session.add(row)
        await self.session.commit()

    async def get_for_dispute(self, dispute_id: str) -> list[AuditEntry]:
        result = await self.session.execute(
            select(AuditRow)
            .where(AuditRow.dispute_id == dispute_id)
            .order_by(AuditRow.timestamp)
        )
        rows = result.scalars().all()
        return [
            AuditEntry(
                id=r.id,
                dispute_id=r.dispute_id,
                event=r.event,
                actor=r.actor,
                actor_id=r.actor_id,
                data=r.data_json or {},
                timestamp=r.timestamp,
            )
            for r in rows
        ]
