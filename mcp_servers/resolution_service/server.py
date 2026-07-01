"""
Resolution Service MCP server â€” executes chosen resolution actions.

All actions are reversible/auditable and recorded in a mock ledger.
In production this would call payment processors, warehouse systems, etc.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("resolution_service")

_LEDGER_PATH = Path(__file__).parent.parent.parent / "data" / "resolution_ledger.json"


def _load_ledger() -> list:
    if _LEDGER_PATH.exists():
        return json.loads(_LEDGER_PATH.read_text())
    return []


def _save_ledger(entries: list) -> None:
    _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    _LEDGER_PATH.write_text(json.dumps(entries, indent=2, default=str))


def _record(action: str, dispute_id: str, order_id: str, amount: Optional[float], details: dict) -> dict:
    entry = {
        "id": str(uuid.uuid4())[:8],
        "action": action,
        "dispute_id": dispute_id,
        "order_id": order_id,
        "amount": amount,
        "details": details,
        "executed_at": datetime.utcnow().isoformat(),
        "status": "executed",
    }
    ledger = _load_ledger()
    ledger.append(entry)
    _save_ledger(ledger)
    return entry


@mcp.tool()
def issue_full_refund(dispute_id: str, order_id: str, amount: float, buyer_id: str) -> dict:
    """Issue a full refund to the buyer. Records in the audit ledger."""
    return _record("full_refund", dispute_id, order_id, amount, {
        "buyer_id": buyer_id,
        "refund_type": "full",
        "payment_method": "original_payment",
        "estimated_processing_days": 3,
    })


@mcp.tool()
def issue_partial_refund(
    dispute_id: str, order_id: str, full_amount: float,
    refund_pct: float, buyer_id: str, reason: str
) -> dict:
    """Issue a partial refund. refund_pct is 0.0â€“1.0."""
    refund_amount = round(full_amount * refund_pct, 2)
    return _record("partial_refund", dispute_id, order_id, refund_amount, {
        "buyer_id": buyer_id,
        "refund_pct": refund_pct,
        "full_amount": full_amount,
        "refund_amount": refund_amount,
        "reason": reason,
        "estimated_processing_days": 3,
    })


@mcp.tool()
def initiate_replacement(dispute_id: str, order_id: str, buyer_id: str, seller_id: str) -> dict:
    """Initiate a replacement shipment request to the seller."""
    return _record("replacement", dispute_id, order_id, None, {
        "buyer_id": buyer_id,
        "seller_id": seller_id,
        "replacement_order_id": f"RPL-{order_id}",
        "seller_deadline_days": 5,
        "message_to_seller": "Please ship a replacement item to the buyer within 5 business days.",
    })


@mcp.tool()
def deny_claim(dispute_id: str, order_id: str, buyer_id: str, reason: str) -> dict:
    """Record a claim denial. No financial action taken."""
    return _record("deny", dispute_id, order_id, None, {
        "buyer_id": buyer_id,
        "denial_reason": reason,
        "appeal_window_days": 7,
    })


@mcp.tool()
def initiate_return_then_refund(
    dispute_id: str, order_id: str, buyer_id: str, seller_id: str, amount: float
) -> dict:
    """Create a return label for the buyer; refund issued on confirmed return."""
    return _record("return_then_refund", dispute_id, order_id, amount, {
        "buyer_id": buyer_id,
        "seller_id": seller_id,
        "return_label": f"RTN-{order_id}-{dispute_id[:8]}",
        "refund_held_until_return": True,
        "return_window_days": 14,
    })


@mcp.tool()
def get_ledger(dispute_id: str = "") -> list:
    """Retrieve resolution ledger entries, optionally filtered by dispute_id."""
    ledger = _load_ledger()
    if dispute_id:
        return [e for e in ledger if e.get("dispute_id") == dispute_id]
    return ledger


if __name__ == "__main__":
    import os
    port = int(os.getenv("RESOLUTION_SERVICE_PORT", "8007"))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
