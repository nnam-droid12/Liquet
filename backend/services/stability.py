"""
Verdict Stability Scoring — run adjudicator 3× with shuffled evidence order.

If the verdict changes when evidence is presented in different orders, the case
is inherently ambiguous and the raw confidence is over-stated. We multiply by
a stability factor to get effective_confidence, then re-apply the LIQUET gate
on that adjusted figure.

stability_score:
  1.00  — all three runs agree (verdict is stable)
  0.67  — two out of three agree (minor variance)
  0.33  — all three differ   (verdict is unstable → force NON LIQUET)
"""

from __future__ import annotations

import random
from collections import Counter

import structlog

from backend.core.models import CaseFile, ClaimExtraction, StabilityResult, StabilityRun
from backend.services.adjudicator import AdjudicationPipeline

logger = structlog.get_logger(__name__)

STABILITY_RUNS = 3
STABILITY_THRESHOLD = 0.67   # require ≥ 2/3 agreement


class StabilityScorer:
    def __init__(self, adjudicator: AdjudicationPipeline):
        self.adjudicator = adjudicator

    async def score(
        self, case_file: CaseFile, claims: ClaimExtraction
    ) -> StabilityResult:
        log = logger.bind(dispute_id=case_file.dispute_id)
        runs: list[StabilityRun] = []

        for i in range(STABILITY_RUNS):
            shuffled = _shuffle_case(case_file, seed=i)
            try:
                verdict = await self.adjudicator.adjudicate_with_claims(shuffled, claims)
                runs.append(StabilityRun(
                    run_index=i,
                    resolution=verdict.resolution.value,
                    confidence=verdict.confidence,
                ))
            except Exception as exc:
                log.warning("stability_run_failed", run=i, error=str(exc))
                runs.append(StabilityRun(
                    run_index=i,
                    resolution="escalate",
                    confidence=0.0,
                ))

        resolution_counts = Counter(r.resolution for r in runs)
        max_agreement = max(resolution_counts.values()) if runs else 0

        if max_agreement == STABILITY_RUNS:
            stability_score = 1.0
        elif max_agreement >= STABILITY_RUNS - 1:
            stability_score = 0.67
        else:
            stability_score = 0.33

        avg_confidence = sum(r.confidence for r in runs) / max(len(runs), 1)
        effective_confidence = round(avg_confidence * stability_score, 4)

        log.info(
            "stability_scored",
            stability=stability_score,
            effective_conf=effective_confidence,
            distribution=dict(resolution_counts),
        )

        return StabilityResult(
            runs=runs,
            stability_score=stability_score,
            effective_confidence=effective_confidence,
            is_stable=stability_score >= STABILITY_THRESHOLD,
            verdict_distribution=dict(resolution_counts),
        )


def _shuffle_case(case_file: CaseFile, seed: int) -> CaseFile:
    """Return a copy of the CaseFile with evidence in a seeded-random order."""
    rng = random.Random(seed)
    evidence_copy = list(case_file.evidence)
    rng.shuffle(evidence_copy)
    return CaseFile(
        dispute_id=case_file.dispute_id,
        order_id=case_file.order_id,
        order_value=case_file.order_value,
        dispute_type=case_file.dispute_type,
        buyer=case_file.buyer,
        seller=case_file.seller,
        evidence=evidence_copy,
        hard_contradictions=list(case_file.hard_contradictions),
        missing_evidence_gaps=list(case_file.missing_evidence_gaps),
    )
