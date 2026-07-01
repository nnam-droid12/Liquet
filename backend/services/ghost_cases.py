"""
Ghost Cases — cross-dispute pattern mining injected as synthetic evidence.

Queries all past resolved disputes for the same seller and dispute type,
computes a pattern-match score, and injects a synthetic EvidenceItem so the
adjudicator can reason about recurring seller behaviour.
"""

from __future__ import annotations

from collections import Counter

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import (
    Dispute, EvidenceItem, EvidenceType, GhostCaseResult,
)
from backend.repositories.database import DisputeRow

logger = structlog.get_logger(__name__)

_BASE_RELIABILITY = 0.55


class GhostCaseEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def analyze(self, dispute: Dispute) -> GhostCaseResult:
        log = logger.bind(dispute_id=dispute.id, seller_id=dispute.seller_id)

        try:
            # All past resolved disputes for this seller (excluding the current one)
            seller_result = await self.session.execute(
                select(DisputeRow)
                .where(DisputeRow.seller_id == dispute.seller_id)
                .where(DisputeRow.id != dispute.id)
                .where(DisputeRow.status.in_(["resolved", "escalated", "closed"]))
            )
            seller_past = seller_result.scalars().all()

            # Platform-wide total for rate denominator
            platform_result = await self.session.execute(
                select(DisputeRow).where(
                    DisputeRow.status.in_(["resolved", "escalated", "closed"])
                )
            )
            platform_total = len(platform_result.scalars().all())

            # Disputes with same type (the "pattern")
            similar = [r for r in seller_past if r.dispute_type == dispute.dispute_type.value]

            seller_dispute_rate = len(seller_past) / max(platform_total, 1)
            pattern_match_score = (
                len(similar) / max(len(seller_past), 1) if seller_past else 0.0
            )

            # Most common outcome among similar disputes
            dominant_resolution: str | None = None
            if similar:
                status_counts = Counter(r.status for r in similar)
                dominant_resolution = status_counts.most_common(1)[0][0]

            synthetic_evidence: EvidenceItem | None = None
            weight = 0.0

            if len(seller_past) >= 2:
                weight = min(0.8, 0.25 + len(similar) * 0.12)
                reliability = min(0.75, _BASE_RELIABILITY + pattern_match_score * 0.20)

                signal_parts = [
                    f"Seller has {len(seller_past)} prior resolved dispute(s)."
                ]
                if similar:
                    signal_parts.append(
                        f"{len(similar)} match the current type ({dispute.dispute_type.value})."
                    )
                if pattern_match_score > 0.5:
                    signal_parts.append(
                        f"Recurring pattern detected ({pattern_match_score:.0%} match rate)."
                    )

                content = {
                    "seller_id": dispute.seller_id,
                    "total_prior_disputes": len(seller_past),
                    "similar_type_count": len(similar),
                    "seller_dispute_rate": round(seller_dispute_rate, 4),
                    "pattern_match_score": round(pattern_match_score, 4),
                    "signal": " ".join(signal_parts),
                }
                synthetic_evidence = EvidenceItem(
                    source="ghost_case_engine",
                    evidence_type=EvidenceType.ORDER_RECORD,
                    reliability=reliability,
                    content=content,
                    metadata={"synthetic": True, "ghost_case": True},
                )

            log.info(
                "ghost_analysis_complete",
                past=len(seller_past),
                similar=len(similar),
                pattern_score=round(pattern_match_score, 3),
            )

            return GhostCaseResult(
                similar_cases_count=len(similar),
                seller_dispute_rate=seller_dispute_rate,
                pattern_match_score=pattern_match_score,
                dominant_resolution=dominant_resolution,
                synthetic_evidence=synthetic_evidence,
                weight=weight,
            )

        except Exception as exc:
            log.error("ghost_analysis_failed", error=str(exc))
            return GhostCaseResult(
                similar_cases_count=0,
                seller_dispute_rate=0.0,
                pattern_match_score=0.0,
                dominant_resolution=None,
                synthetic_evidence=None,
                weight=0.0,
            )
