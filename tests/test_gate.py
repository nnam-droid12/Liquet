"""Unit tests for the Liquet gate — the critical LIQUET/NON_LIQUET decision."""

import pytest
from backend.core.models import (
    CaseFile, DisputeType, EvidenceItem, EvidenceType, GateResult,
    Party, ResolutionType, Verdict,
)
from backend.services.liquet_gate import LiquetGate


def _make_verdict(resolution=ResolutionType.FULL_REFUND, confidence=0.92, value=89.99, partial=None):
    return Verdict(
        resolution=resolution,
        confidence=confidence,
        rationale="test rationale",
        value_at_stake=value,
        partial_refund_pct=partial if resolution == ResolutionType.PARTIAL_REFUND else None,
    )


def _make_case(order_value=89.99, hard_contradictions=None):
    return CaseFile(
        dispute_id="TEST-D001",
        order_id="ORD-001",
        order_value=order_value,
        dispute_type=DisputeType.NOT_AS_DESCRIBED,
        buyer=Party(user_id="B1", role="buyer", narrative="test"),
        seller=Party(user_id="S1", role="seller", narrative="test"),
        evidence=[],
        hard_contradictions=hard_contradictions or [],
    )


class TestLiquetGate:
    def setup_method(self):
        self.gate = LiquetGate(conf_threshold=0.80, value_threshold=500.0)

    def test_high_confidence_low_value_resolves(self):
        verdict = _make_verdict(confidence=0.92)
        case = _make_case(order_value=89.99)
        result, reason = self.gate.evaluate(verdict, case)
        assert result == GateResult.LIQUET
        assert reason is None

    def test_low_confidence_escalates(self):
        verdict = _make_verdict(confidence=0.65)
        case = _make_case(order_value=89.99)
        result, reason = self.gate.evaluate(verdict, case)
        assert result == GateResult.NON_LIQUET
        assert "threshold" in reason.lower() or "confidence" in reason.lower()

    def test_high_value_escalates(self):
        """Orders >= $500 must escalate regardless of confidence (V-001)."""
        verdict = _make_verdict(confidence=0.95)
        case = _make_case(order_value=649.00)
        result, reason = self.gate.evaluate(verdict, case)
        assert result == GateResult.NON_LIQUET
        assert "500" in reason or "value" in reason.lower()

    def test_hard_contradiction_escalates(self):
        verdict = _make_verdict(confidence=0.88)
        case = _make_case(
            order_value=89.99,
            hard_contradictions=["Buyer video shows scratch; seller photo shows clean lens"],
        )
        result, reason = self.gate.evaluate(verdict, case)
        assert result == GateResult.NON_LIQUET
        assert "contradiction" in reason.lower()

    def test_fifty_fifty_case_must_escalate(self):
        """The engineered 50/50 case must never auto-resolve."""
        verdict = _make_verdict(confidence=0.51, value=649.0)
        case = _make_case(
            order_value=649.0,
            hard_contradictions=["Symmetric conflicting photo evidence — cannot determine authenticity"],
        )
        result, reason = self.gate.evaluate(verdict, case)
        assert result == GateResult.NON_LIQUET

    def test_escalate_resolution_triggers_non_liquet(self):
        """When the adjudicator itself returns ESCALATE, gate must NON_LIQUET."""
        verdict = _make_verdict(resolution=ResolutionType.ESCALATE, confidence=0.9)
        case = _make_case(order_value=50.0)
        result, reason = self.gate.evaluate(verdict, case)
        assert result == GateResult.NON_LIQUET

    def test_at_threshold_boundary_resolves(self):
        """Exactly at threshold should resolve (>= not just >)."""
        verdict = _make_verdict(confidence=0.80)
        case = _make_case(order_value=499.99)
        result, reason = self.gate.evaluate(verdict, case)
        assert result == GateResult.LIQUET
