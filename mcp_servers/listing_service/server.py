"""Listing Service MCP server â€” product listing text and reference images."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("listing_service")

_DATA_FILE = Path(__file__).parent.parent.parent / "data" / "listings.json"
_listings: dict[str, dict] = {}


def _load_data() -> None:
    global _listings
    if _DATA_FILE.exists():
        _listings = json.loads(_DATA_FILE.read_text())
    else:
        _listings = {
            "PROD-001": {
                "product_id": "PROD-001",
                "title": "Vintage Leather Jacket - Brown, Size M",
                "description": "Genuine leather jacket in excellent condition. Color: warm brown. Size: Medium (EU 48). No visible damage, minor scuffs consistent with vintage character. All zippers fully functional.",
                "condition": "used_good",
                "images": ["https://example.com/images/jacket_front.jpg", "https://example.com/images/jacket_back.jpg"],
                "category": "clothing",
                "attributes": {"color": "brown", "size": "M", "material": "genuine leather"},
            },
            "PROD-002": {
                "product_id": "PROD-002",
                "title": "Wireless Gaming Headset - Black",
                "description": "Brand new in original box. Model: SoundBlast Pro X. Features: 7.1 surround, 50mm drivers, 20hr battery. Includes USB dongle and 3.5mm cable. Color: matte black.",
                "condition": "new",
                "images": ["https://example.com/images/headset_box.jpg", "https://example.com/images/headset_open.jpg"],
                "category": "electronics",
                "attributes": {"color": "black", "connectivity": "wireless", "warranty": "1 year"},
            },
            "PROD-003": {
                "product_id": "PROD-003",
                "title": "Handmade Ceramic Coffee Set (6 cups)",
                "description": "Artisan handmade ceramic set. Includes 6 matching cups + saucers + serving tray. Glazed in cobalt blue. Each piece individually wrapped for shipping. Dishwasher safe.",
                "condition": "new",
                "images": ["https://example.com/images/ceramic_set.jpg"],
                "category": "home_goods",
                "attributes": {"color": "cobalt blue", "pieces": 13, "material": "ceramic"},
            },
            "PROD-004": {
                "product_id": "PROD-004",
                "title": "Professional DSLR Camera Lens 50mm f/1.8",
                "description": "Canon EF 50mm f/1.8 STM lens. Excellent condition, used for 6 months. No fungus, no scratches on glass elements. Includes original lens caps and pouch. Mount: Canon EF.",
                "condition": "used_like_new",
                "images": ["https://example.com/images/lens_front.jpg", "https://example.com/images/lens_side.jpg"],
                "category": "photography",
                "attributes": {"brand": "Canon", "focal_length": "50mm", "aperture": "f/1.8", "mount": "EF"},
            },
            "PROD-005": {
                "product_id": "PROD-005",
                "title": "Yoga Mat - Purple, Non-Slip, 6mm",
                "description": "Premium TPE yoga mat in purple. Dimensions: 183cm x 61cm x 6mm. Non-slip surface on both sides. Comes with carrying strap. Suitable for all yoga styles.",
                "condition": "new",
                "images": ["https://example.com/images/yoga_mat.jpg"],
                "category": "sports",
                "attributes": {"color": "purple", "thickness": "6mm", "material": "TPE"},
            },
        }


@mcp.tool()
def get_listing(product_id: str) -> dict:
    """Get the product listing including title, description, condition, and reference image URLs."""
    _load_data()
    listing = _listings.get(product_id)
    if listing is None:
        return {"error": f"Listing {product_id} not found", "product_id": product_id}
    return listing


@mcp.tool()
def get_listing_for_order(order_id: str, product_id: str) -> dict:
    """Get listing info for an order's product (what was promised to the buyer)."""
    return get_listing(product_id)


if __name__ == "__main__":
    import os
    port = int(os.getenv("LISTING_SERVICE_PORT", "8003"))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
