"""
The Liquet Gate — the central decision on whether to resolve autonomously or escalate.

LIQUET  → confidence ≥ CONF_THRESHOLD AND order_value < VALUE_THRESHOLD AND no hard contradictions
NON_LIQUET → any of those conditions is violated

This is the brand: Liquet knows when it's clear — and admits when it isn't.
"""

from __future__ import annotations

from typing import Optional

import structlog

from backend.core.models import (
    CaseFile, GateResult, ResolutionType, SkepticResult, StabilityResult, Verdict,
)
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

    def evaluate(
        self,
        verdict: Verdict,
        case_file: CaseFile,
        stability: Optional[StabilityResult] = None,
        skeptic: Optional[SkepticResult] = None,
    ) -> tuple[GateResult, Optional[str]]:
        """
        Returns (GateResult, abstention_reason).

        Applies three layers on top of classic confidence/value/contradiction gates:
        - Stability: if verdict changed across shuffled runs, use effective_confidence
        - Skeptic:   if rebuttal was weak, force NON_LIQUET regardless of confidence
        """
        reasons: list[str] = []

        # Use stability-adjusted confidence when available
        effective_conf = verdict.confidence
        if stability is not None:
            effective_conf = stability.effective_confidence
            if not stability.is_stable:
                reasons.append(
                    f"Verdict is unstable across evidence orderings "
                    f"(stability={stability.stability_score:.0%}, distribution={stability.verdict_distribution}) "
                    f"— effective confidence reduced to {effective_conf:.2f}"
                )

        # Confidence gate (using effective confidence)
        if effective_conf < self.conf_threshold:
            reasons.append(
                f"Effective confidence {effective_conf:.2f} is below threshold "
                f"{self.conf_threshold:.2f}"
            )

        # Value gate
        if case_file.order_value >= self.value_threshold:
            reasons.append(
                f"Order value ${case_file.order_value:.2f} exceeds "
                f"${self.value_threshold:.2f} limit (policy V-001)"
            )

        # Hard contradiction gate
        if case_file.hard_contradictions:
            reasons.append(
                f"Unresolved hard contradiction: {case_file.hard_contradictions[0]}"
            )

        # LLM self-escalation
        if verdict.resolution == ResolutionType.ESCALATE:
            reasons.append("Adjudicator flagged case as requiring human review")

        # Skeptic veto — if the adjudicator couldn't rebut its own challenge
        if skeptic is not None and skeptic.verdict_contested:
            reasons.append(
                f"Skeptic pass contested verdict (rebuttal strength "
                f"{skeptic.rebuttal_strength:.0%} < 55%): {skeptic.contest_summary}"
            )

        if reasons:
            abstention = " | ".join(reasons)
            logger.info("gate_non_liquet", reasons=reasons)
            return GateResult.NON_LIQUET, abstention

        logger.info(
            "gate_liquet",
            confidence=verdict.confidence,
            effective_conf=effective_conf,
            value=case_file.order_value,
        )
        return GateResult.LIQUET, None
