"""
Policy Engine MCP server â€” applies platform policy to a CaseFile.

Hybrid: rule checks first, then LLM reasoning over policy.md for edge cases.
Returns eligible resolutions + the controlling policy clauses.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("policy_engine")

_POLICY_PATH = Path(__file__).parent.parent.parent / "data" / "policy.md"


def _load_policy() -> str:
    if _POLICY_PATH.exists():
        return _POLICY_PATH.read_text()
    return "Standard marketplace policy applies."


def _rule_check(case_summary: dict) -> dict:
    """Fast deterministic rule checks before LLM reasoning."""
    eligible = []
    clauses = []
    hard_blocks = []

    order_value = case_summary.get("order_value", 0)
    dispute_type = case_summary.get("dispute_type", "")
    delivered = case_summary.get("delivered", None)
    tracking_missing = case_summary.get("tracking_missing", False)
    damage_in_photos = case_summary.get("damage_in_photos", False)
    color_mismatch = case_summary.get("color_mismatch", False)
    wrong_item = case_summary.get("wrong_item", False)

    # V-001: High-value auto-escalate
    if order_value >= 500:
        hard_blocks.append("V-001: Order value >= $500 requires human review")

    # T-002-A/C: Never arrived
    if dispute_type in ("never_arrived",):
        if delivered is False:
            eligible.append("full_refund")
            clauses.append("T-002-A")
        elif tracking_missing:
            eligible.append("full_refund")
            clauses.append("T-002-C")
        elif delivered:
            eligible.append("deny")
            clauses.append("T-002-B")

    # T-003: Damaged
    if dispute_type in ("damaged",):
        if damage_in_photos:
            eligible.extend(["full_refund", "partial_refund", "replacement"])
            clauses.extend(["T-003-A", "T-003-C"])
        else:
            eligible.append("deny")

    # T-001: Not as described
    if dispute_type in ("not_as_described",):
        if color_mismatch:
            eligible.extend(["full_refund", "partial_refund"])
            clauses.append("T-001-A")
        else:
            eligible.extend(["full_refund", "partial_refund", "deny"])
            clauses.append("T-001-B")

    # T-001-C: Wrong item
    if dispute_type in ("wrong_item",):
        eligible.extend(["full_refund", "replacement"])
        clauses.append("T-001-C")

    if not eligible:
        eligible = ["full_refund", "partial_refund", "replacement", "deny"]

    return {
        "eligible_resolutions": list(set(eligible)),
        "policy_clauses": list(set(clauses)),
        "hard_blocks": hard_blocks,
        "requires_escalation": len(hard_blocks) > 0,
    }


@mcp.tool()
def evaluate_policy(case_summary: dict) -> dict:
    """
    Apply platform policy rules to a case summary.
    Returns eligible resolutions, controlling clauses, and any hard escalation blocks.

    case_summary fields:
    - order_value: float
    - dispute_type: str
    - delivered: bool | None
    - tracking_missing: bool
    - damage_in_photos: bool
    - color_mismatch: bool
    - wrong_item: bool
    """
    return _rule_check(case_summary)


@mcp.tool()
def get_policy_text() -> str:
    """Return the full platform policy document for LLM reasoning."""
    return _load_policy()


@mcp.tool()
def get_policy_clause(clause_id: str) -> str:
    """Return the text of a specific policy clause by ID (e.g. 'T-001-A')."""
    policy = _load_policy()
    lines = policy.split("\n")
    result = []
    in_clause = False
    for line in lines:
        if clause_id in line:
            in_clause = True
        if in_clause:
            result.append(line)
            if result and len(result) > 1 and line.startswith("**Rule") and clause_id not in line:
                break
    return "\n".join(result) if result else f"Clause {clause_id} not found in policy."


if __name__ == "__main__":
    import os
    port = int(os.getenv("POLICY_ENGINE_PORT", "8006"))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
