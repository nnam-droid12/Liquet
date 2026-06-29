"""Unit tests for core data models."""

import pytest
from backend.core.models import (
    CaseFile, Claim, Decision, Dispute, DisputeCreate, DisputeStatus,
    DisputeType, EvidenceItem, EvidenceType, GateResult, ResolutionType, Verdict,
    EvidenceCitation, Party,
)


def test_evidence_item_from_type():
    ev = EvidenceItem.from_type(
        source="order_service",
        evidence_type=EvidenceType.ORDER_RECORD,
        content={"order_id": "ORD-001"},
    )
    assert ev.reliability == 0.90
    assert ev.source == "order_service"
    assert ev.evidence_type == EvidenceType.ORDER_RECORD


def test_carrier_scan_highest_reliability():
    carrier = EvidenceItem.from_type("logistics", EvidenceType.CARRIER_SCAN, {})
    user_claim = EvidenceItem.from_type("buyer", EvidenceType.USER_CLAIM, {})
    assert carrier.reliability > user_claim.reliability


def test_verdict_partial_refund_requires_pct():
    """partial_refund_pct is only valid for PARTIAL_REFUND resolution."""
    with pytest.raises(Exception):
        Verdict(
            resolution=ResolutionType.FULL_REFUND,
            confidence=0.9,
            rationale="test",
            value_at_stake=100.0,
            partial_refund_pct=0.5,  # invalid for FULL_REFUND
        )


def test_dispute_create():
    dc = DisputeCreate(
        order_id="ORD-TEST",
        dispute_type=DisputeType.NEVER_ARRIVED,
        buyer_id="B001",
        seller_id="S001",
        buyer_narrative="Item never arrived",
    )
    assert dc.seller_narrative == ""


def test_case_file_evidence_by_id():
    ev = EvidenceItem.from_type("order_service", EvidenceType.ORDER_RECORD, {})
    case = CaseFile(
        dispute_id="D001",
        order_id="ORD-001",
        order_value=99.99,
        dispute_type=DisputeType.NOT_AS_DESCRIBED,
        buyer=Party(user_id="B1", role="buyer", narrative="test"),
        seller=Party(user_id="S1", role="seller", narrative="test"),
        evidence=[ev],
    )
    found = case.evidence_by_id(ev.id)
    assert found is not None
    assert found.id == ev.id
    assert case.evidence_by_id("nonexistent") is None
