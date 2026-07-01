"""
Core Pydantic data models for Liquet.

All persistence and API boundaries use these types.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ── Enumerations ───────────────────────────────────────────────────────────────

class DisputeType(str, Enum):
    NOT_AS_DESCRIBED = "not_as_described"
    NEVER_ARRIVED = "never_arrived"
    WRONG_ITEM = "wrong_item"
    DAMAGED = "damaged"
    COUNTERFEIT = "counterfeit"
    OTHER = "other"


class ResolutionType(str, Enum):
    FULL_REFUND = "full_refund"
    PARTIAL_REFUND = "partial_refund"
    REPLACEMENT = "replacement"
    RETURN_THEN_REFUND = "return_then_refund"
    DENY = "deny"
    ESCALATE = "escalate"


class GateResult(str, Enum):
    LIQUET = "LIQUET"         # Clear — resolved autonomously
    NON_LIQUET = "NON_LIQUET" # Not clear — escalated to human


class DisputeStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"
    FAILED = "failed"


class EvidenceType(str, Enum):
    CARRIER_SCAN = "carrier_scan"         # Most reliable
    ORDER_RECORD = "order_record"
    LISTING_DATA = "listing_data"
    PHOTO = "photo"
    SCREENSHOT = "screenshot"
    MESSAGE = "message"
    USER_CLAIM = "user_claim"             # Least reliable unverified


class Actor(str, Enum):
    AGENT = "agent"
    HUMAN_REVIEWER = "human_reviewer"
    SYSTEM = "system"


# ── Evidence ───────────────────────────────────────────────────────────────────

EVIDENCE_RELIABILITY: dict[EvidenceType, float] = {
    EvidenceType.CARRIER_SCAN: 0.95,
    EvidenceType.ORDER_RECORD: 0.90,
    EvidenceType.LISTING_DATA: 0.85,
    EvidenceType.PHOTO: 0.70,
    EvidenceType.SCREENSHOT: 0.50,
    EvidenceType.MESSAGE: 0.40,
    EvidenceType.USER_CLAIM: 0.20,
}


class EvidenceItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str                         # e.g. "order_service", "buyer_photo_1"
    evidence_type: EvidenceType
    reliability: float = Field(ge=0.0, le=1.0)
    content: Any                        # structured data or text
    timestamp: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_type(cls, source: str, evidence_type: EvidenceType, content: Any, **kw) -> "EvidenceItem":
        return cls(
            source=source,
            evidence_type=evidence_type,
            reliability=EVIDENCE_RELIABILITY[evidence_type],
            content=content,
            **kw,
        )


# ── Parties & Claims ───────────────────────────────────────────────────────────

class Party(BaseModel):
    user_id: str
    role: str  # "buyer" | "seller"
    narrative: str
    claims: list["Claim"] = Field(default_factory=list)


class Claim(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    party_role: str               # "buyer" | "seller"
    statement: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    credibility_score: float = Field(default=0.5, ge=0.0, le=1.0)


# ── Dispute ────────────────────────────────────────────────────────────────────

class Dispute(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    dispute_type: DisputeType
    status: DisputeStatus = DisputeStatus.OPEN
    buyer_id: str
    seller_id: str
    buyer_narrative: str
    seller_narrative: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DisputeCreate(BaseModel):
    order_id: str
    dispute_type: DisputeType
    buyer_id: str
    seller_id: str
    buyer_narrative: str
    seller_narrative: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── CaseFile ───────────────────────────────────────────────────────────────────

class CaseFile(BaseModel):
    dispute_id: str
    order_id: str
    order_value: float
    dispute_type: DisputeType
    buyer: Party
    seller: Party
    evidence: list[EvidenceItem] = Field(default_factory=list)
    hard_contradictions: list[str] = Field(default_factory=list)  # human-readable descriptions
    missing_evidence_gaps: list[str] = Field(default_factory=list)
    assembled_at: datetime = Field(default_factory=datetime.utcnow)

    def evidence_by_id(self, eid: str) -> Optional[EvidenceItem]:
        return next((e for e in self.evidence if e.id == eid), None)


# ── Verdict ────────────────────────────────────────────────────────────────────

class EvidenceCitation(BaseModel):
    evidence_id: str
    evidence_source: str
    supports: str   # which claim / finding it supports


class Verdict(BaseModel):
    resolution: ResolutionType
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    citations: list[EvidenceCitation] = Field(default_factory=list)
    value_at_stake: float
    policy_clauses: list[str] = Field(default_factory=list)
    partial_refund_pct: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @field_validator("partial_refund_pct")
    @classmethod
    def partial_requires_partial_resolution(cls, v, info):
        if v is not None and info.data.get("resolution") != ResolutionType.PARTIAL_REFUND:
            raise ValueError("partial_refund_pct only valid for PARTIAL_REFUND resolution")
        return v


# ── Decision (gate output) ─────────────────────────────────────────────────────

class Decision(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dispute_id: str
    verdict: Verdict
    gate_result: GateResult
    abstention_reason: Optional[str] = None  # populated when NON_LIQUET
    actor: Actor = Actor.AGENT
    actor_id: Optional[str] = None
    decided_at: datetime = Field(default_factory=datetime.utcnow)


# ── Human queue ────────────────────────────────────────────────────────────────

class HumanReviewBrief(BaseModel):
    decision_id: str
    dispute_id: str
    order_value: float
    dispute_type: DisputeType
    buyer_narrative: str
    seller_narrative: str
    evidence_summary: list[dict[str, Any]]
    leaning_verdict: ResolutionType
    leaning_confidence: float
    abstention_reason: str
    hard_contradictions: list[str]
    missing_gaps: list[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HumanReviewAction(BaseModel):
    reviewer_id: str
    approved_resolution: ResolutionType
    override_note: Optional[str] = None
    partial_refund_pct: Optional[float] = None


# ── Audit ──────────────────────────────────────────────────────────────────────

class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    dispute_id: str
    event: str
    actor: Actor
    actor_id: Optional[str] = None
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── LLM structured outputs ─────────────────────────────────────────────────────

class ClaimExtraction(BaseModel):
    buyer_claims: list[str]
    seller_claims: list[str]


class EvidenceMapping(BaseModel):
    claim_id: str
    supporting_evidence_ids: list[str]
    contradicting_evidence_ids: list[str]
    credibility_score: float


class VerdictOutput(BaseModel):
    resolution: str
    confidence: float
    rationale: str
    policy_clauses: list[str]
    citation_evidence_ids: list[str]
    partial_refund_pct: Optional[float] = None
    hard_contradictions: list[str] = Field(default_factory=list)


class VisionAnalysis(BaseModel):
    observations: list[str]
    damage_detected: bool
    matches_listing: Optional[bool] = None
    confidence: float
    raw_description: str
