"""Policy browser endpoint — expose the platform's policy rules as structured data."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

_POLICY_PATH = Path(__file__).parent.parent.parent / "data" / "policy.md"


def _parse_clauses(text: str) -> list[dict]:
    """Extract clause codes and their descriptions from policy.md."""
    clauses = []
    # Match lines like: **T-001-A**: description or T-001-A: description
    for line in text.splitlines():
        m = re.match(r'\*?\*?([A-Z]-\d{3}[A-Z-]*):\*?\*?\s*(.*)', line.strip())
        if m:
            clauses.append({
                "code": m.group(1),
                "description": m.group(2).strip().rstrip('.'),
            })
    return clauses


@router.get("/api/policy")
async def get_policy() -> dict:
    """Return platform policy as structured data for the policy browser."""
    if not _POLICY_PATH.exists():
        return {"raw": "Policy not available.", "clauses": []}

    text = _POLICY_PATH.read_text()
    clauses = _parse_clauses(text)

    # Group by first letter (T=Type, V=Value, Q=Quality, etc.)
    groups: dict[str, list] = {}
    for c in clauses:
        prefix = c["code"][0]
        groups.setdefault(prefix, []).append(c)

    return {
        "raw": text,
        "clauses": clauses,
        "groups": groups,
        "clause_count": len(clauses),
    }
