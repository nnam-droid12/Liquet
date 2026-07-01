"""Logistics Service MCP server â€” tracking history and carrier scan events."""


import json
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("logistics_service")

_DATA_FILE = Path(__file__).parent.parent.parent / "data" / "tracking.json"
_tracking: dict[str, dict] = {}


def _load_data() -> None:
    global _tracking
    if _DATA_FILE.exists():
        _tracking = json.loads(_DATA_FILE.read_text())
    else:
        _tracking = {
            "ORD-001": {
                "order_id": "ORD-001",
                "carrier": "FedEx",
                "tracking_number": "FX789123456",
                "status": "delivered",
                "delivered_at": "2025-11-08T14:32:00Z",
                "events": [
                    {"timestamp": "2025-11-01T09:00:00Z", "location": "Chicago, IL", "status": "picked_up"},
                    {"timestamp": "2025-11-03T22:10:00Z", "location": "Kansas City, MO", "status": "in_transit"},
                    {"timestamp": "2025-11-08T14:32:00Z", "location": "Springfield, IL", "status": "delivered", "signed_by": "J. DOE"},
                ],
            },
            "ORD-002": {
                "order_id": "ORD-002",
                "carrier": "UPS",
                "tracking_number": "1Z999AA10123456784",
                "status": "delivered",
                "delivered_at": "2025-11-12T10:15:00Z",
                "events": [
                    {"timestamp": "2025-11-05T11:00:00Z", "location": "Los Angeles, CA", "status": "picked_up"},
                    {"timestamp": "2025-11-10T18:00:00Z", "location": "San Francisco, CA", "status": "in_transit"},
                    {"timestamp": "2025-11-12T10:15:00Z", "location": "Portland, OR", "status": "delivered", "signed_by": "FRONT DOOR"},
                ],
            },
            "ORD-003": {
                "order_id": "ORD-003",
                "carrier": "USPS",
                "tracking_number": "9400111899223481087",
                "status": "delivered",
                "delivered_at": "2025-11-04T09:45:00Z",
                "events": [
                    {"timestamp": "2025-10-29T08:00:00Z", "location": "New York, NY", "status": "picked_up"},
                    {"timestamp": "2025-11-02T14:00:00Z", "location": "Dallas, TX", "status": "in_transit"},
                    {"timestamp": "2025-11-04T09:45:00Z", "location": "Austin, TX", "status": "delivered"},
                ],
                "fragile_handling": True,
            },
            "ORD-004": {
                "order_id": "ORD-004",
                "carrier": "DHL",
                "tracking_number": "DHL123456789",
                "status": "delivered",
                "delivered_at": "2025-11-17T16:00:00Z",
                "events": [
                    {"timestamp": "2025-11-10T15:00:00Z", "location": "New York, NY", "status": "picked_up"},
                    {"timestamp": "2025-11-15T10:00:00Z", "location": "Denver, CO", "status": "in_transit"},
                    {"timestamp": "2025-11-17T16:00:00Z", "location": "Seattle, WA", "status": "delivered"},
                ],
            },
            "ORD-005": {
                "order_id": "ORD-005",
                "carrier": "UPS",
                "tracking_number": "1Z999BB20987654321",
                "status": "in_transit",
                "delivered_at": None,
                "events": [
                    {"timestamp": "2025-11-15T09:00:00Z", "location": "Miami, FL", "status": "picked_up"},
                    {"timestamp": "2025-11-18T12:00:00Z", "location": "Atlanta, GA", "status": "in_transit"},
                ],
            },
        }


@mcp.tool()
def get_tracking(order_id: str) -> dict:
    """Get full tracking history and carrier scan events for an order."""
    _load_data()
    info = _tracking.get(order_id)
    if info is None:
        return {"error": f"No tracking found for order {order_id}", "order_id": order_id, "status": "unknown"}
    return info


@mcp.tool()
def was_delivered(order_id: str) -> dict:
    """Quick check: was this order delivered and when?"""
    _load_data()
    info = _tracking.get(order_id)
    if info is None:
        return {"delivered": False, "delivered_at": None, "evidence_quality": "missing"}
    return {
        "delivered": info.get("status") == "delivered",
        "delivered_at": info.get("delivered_at"),
        "carrier": info.get("carrier"),
        "tracking_number": info.get("tracking_number"),
        "evidence_quality": "carrier_scan",
    }


if __name__ == "__main__":
    import os
    port = int(os.getenv("LOGISTICS_SERVICE_PORT", "8002"))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
