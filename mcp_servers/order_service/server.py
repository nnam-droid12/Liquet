"""Order Service MCP server â€” returns order records and line items."""


import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("order_service")

# Seed data â€” loaded from synthetic cases
_DATA_FILE = Path(__file__).parent.parent.parent / "data" / "orders.json"
_orders: dict[str, dict] = {}


def _load_data() -> None:
    global _orders
    if _DATA_FILE.exists():
        _orders = json.loads(_DATA_FILE.read_text())
    else:
        # Fallback inline seed
        _orders = {
            "ORD-001": {
                "order_id": "ORD-001", "buyer_id": "USR-B001", "seller_id": "USR-S001",
                "product_title": "Vintage Leather Jacket - Brown, Size M",
                "product_id": "PROD-001", "quantity": 1,
                "price": 89.99, "currency": "USD",
                "status": "delivered", "order_date": "2025-11-01",
                "shipping_address": "42 Elm St, Springfield, IL 62701",
            },
            "ORD-002": {
                "order_id": "ORD-002", "buyer_id": "USR-B002", "seller_id": "USR-S002",
                "product_title": "Wireless Gaming Headset - Black",
                "product_id": "PROD-002", "quantity": 1,
                "price": 79.99, "currency": "USD",
                "status": "delivered", "order_date": "2025-11-05",
                "shipping_address": "7 Oak Ave, Portland, OR 97201",
            },
            "ORD-003": {
                "order_id": "ORD-003", "buyer_id": "USR-B003", "seller_id": "USR-S003",
                "product_title": "Handmade Ceramic Coffee Set (6 cups)",
                "product_id": "PROD-003", "quantity": 1,
                "price": 145.00, "currency": "USD",
                "status": "delivered", "order_date": "2025-10-28",
                "shipping_address": "88 Pine Rd, Austin, TX 78701",
            },
            "ORD-004": {
                "order_id": "ORD-004", "buyer_id": "USR-B004", "seller_id": "USR-S001",
                "product_title": "Professional DSLR Camera Lens 50mm",
                "product_id": "PROD-004", "quantity": 1,
                "price": 649.00, "currency": "USD",
                "status": "delivered", "order_date": "2025-11-10",
                "shipping_address": "15 Maple Dr, Seattle, WA 98101",
            },
            "ORD-005": {
                "order_id": "ORD-005", "buyer_id": "USR-B005", "seller_id": "USR-S004",
                "product_title": "Yoga Mat - Purple, Non-Slip",
                "product_id": "PROD-005", "quantity": 1,
                "price": 34.99, "currency": "USD",
                "status": "in_transit", "order_date": "2025-11-15",
                "shipping_address": "200 River Ln, Nashville, TN 37201",
            },
        }


@mcp.tool()
def get_order(order_id: str) -> dict:
    """Retrieve full order record including buyer/seller IDs, product, price, and status."""
    _load_data()
    order = _orders.get(order_id)
    if order is None:
        return {"error": f"Order {order_id} not found", "order_id": order_id}
    return order


@mcp.tool()
def list_buyer_orders(buyer_id: str) -> list:
    """List all orders for a given buyer."""
    _load_data()
    return [o for o in _orders.values() if o.get("buyer_id") == buyer_id]


if __name__ == "__main__":
    import os
    port = int(os.getenv("ORDER_SERVICE_PORT", "8001"))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
