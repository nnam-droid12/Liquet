"""
The Liquet Gate — the central decision on whether to resolve autonomously or escalate.

LIQUET  → confidence ≥ CONF_THRESHOLD AND order_value < VALUE_THRESHOLD AND no hard contradictions
NON_LIQUET → any of those conditions is violated

This is the brand: Liquet knows when it's clear — and admits when it isn't.
"""

from __future__ import annotations

from typing import Optional

import structlog

from backend.core.models import CaseFile, GateResult, ResolutionType, Verdict
from config import settings

logger = structlog.get_logger(__name__)


class LiquetGate:
    def __init__(
        self,
        conf_threshold: Optional[float] = None,
        value_threshold: Optional[float] = None,
    ):
        self.conf_threshold = conf_threshold or settings.conf_threshold
        self.value_threshold = value_threshold or settings.value_threshold

    def evaluate(self, verdict: Verdict, case_file: CaseFile) -> tuple[GateResult, Optional[str]]:
        """
        Returns (GateResult, abstention_reason).
        abstention_reason is None for LIQUET, a human-readable explanation for NON_LIQUET.
        """
        reasons: list[str] = []

        # Confidence gate
        if verdict.confidence < self.conf_threshold:
            reasons.append(
                f"Confidence {verdict.confidence:.2f} is below threshold {self.conf_threshold:.2f} — "
                f"evidence is insufficient for autonomous resolution"
            )

        # Value gate
        if case_file.order_value >= self.value_threshold:
            reasons.append(
                f"Order value ${case_file.order_value:.2f} exceeds ${self.value_threshold:.2f} limit "
                f"(policy V-001: high-value orders require human review)"
            )

        # Hard contradiction gate
        if case_file.hard_contradictions:
            reasons.append(
                f"Unresolved hard contradiction: {case_file.hard_contradictions[0]}"
            )

        # Resolution == ESCALATE means LLM itself flagged it
        if verdict.resolution == ResolutionType.ESCALATE:
            reasons.append("Adjudicator flagged case as requiring human review")

        if reasons:
            abstention = " | ".join(reasons)
            logger.info("gate_non_liquet", reasons=reasons)
            return GateResult.NON_LIQUET, abstention

        logger.info("gate_liquet", confidence=verdict.confidence, value=case_file.order_value)
        return GateResult.LIQUET, None
