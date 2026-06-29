"""
In-process tool client — calls MCP server logic directly (no HTTP) for the demo.

In production, replace with async MCP client calls over SSE/HTTP.
This design keeps the interface identical so the swap is transparent.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Optional

# Ensure mcp_servers is importable
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _import_server(package: str):
    return importlib.import_module(f"mcp_servers.{package}.server")


class ToolClient:
    """Thin wrapper that calls MCP server functions in-process."""

    # ── Order service ─────────────────────────────────────────────────────────
    async def get_order(self, order_id: str) -> dict[str, Any]:
        mod = _import_server("order_service")
        return mod.get_order(order_id)

    # ── Logistics service ─────────────────────────────────────────────────────
    async def get_tracking(self, order_id: str) -> dict[str, Any]:
        mod = _import_server("logistics_service")
        return mod.get_tracking(order_id)

    async def was_delivered(self, order_id: str) -> dict[str, Any]:
        mod = _import_server("logistics_service")
        return mod.was_delivered(order_id)

    # ── Listing service ───────────────────────────────────────────────────────
    async def get_listing(self, product_id: str) -> dict[str, Any]:
        mod = _import_server("listing_service")
        return mod.get_listing(product_id)

    # ── Comms service ─────────────────────────────────────────────────────────
    async def get_messages(self, order_id: str) -> list[dict[str, Any]]:
        mod = _import_server("comms_service")
        return mod.get_messages(order_id)

    async def get_message_summary(self, order_id: str) -> dict[str, Any]:
        mod = _import_server("comms_service")
        return mod.get_message_summary(order_id)

    # ── Vision intake ─────────────────────────────────────────────────────────
    async def analyze_image(self, image_url: str, listing_description: str = "") -> dict[str, Any]:
        mod = _import_server("vision_intake")
        use_real = False
        try:
            from config import settings
            use_real = bool(settings.qwen_api_key and not settings.qwen_api_key.startswith("sk-your"))
        except Exception:
            pass

        if use_real:
            import asyncio
            return await mod._analyze_image_async(image_url, listing_description or None)
        else:
            return mod.analyze_image_mock(image_url, listing_description or None)

    # ── Policy engine ─────────────────────────────────────────────────────────
    async def evaluate_policy(self, case_summary: dict[str, Any]) -> dict[str, Any]:
        mod = _import_server("policy_engine")
        return mod.evaluate_policy(case_summary)

    async def get_policy_text(self) -> str:
        mod = _import_server("policy_engine")
        return mod.get_policy_text()

    # ── Resolution service ────────────────────────────────────────────────────
    async def issue_full_refund(self, dispute_id: str, order_id: str, amount: float, buyer_id: str) -> dict[str, Any]:
        mod = _import_server("resolution_service")
        return mod.issue_full_refund(dispute_id, order_id, amount, buyer_id)

    async def issue_partial_refund(
        self, dispute_id: str, order_id: str, full_amount: float,
        refund_pct: float, buyer_id: str, reason: str
    ) -> dict[str, Any]:
        mod = _import_server("resolution_service")
        return mod.issue_partial_refund(dispute_id, order_id, full_amount, refund_pct, buyer_id, reason)

    async def initiate_replacement(
        self, dispute_id: str, order_id: str, buyer_id: str, seller_id: str
    ) -> dict[str, Any]:
        mod = _import_server("resolution_service")
        return mod.initiate_replacement(dispute_id, order_id, buyer_id, seller_id)

    async def deny_claim(self, dispute_id: str, order_id: str, buyer_id: str, reason: str) -> dict[str, Any]:
        mod = _import_server("resolution_service")
        return mod.deny_claim(dispute_id, order_id, buyer_id, reason)

    async def initiate_return_then_refund(
        self, dispute_id: str, order_id: str, buyer_id: str, seller_id: str, amount: float
    ) -> dict[str, Any]:
        mod = _import_server("resolution_service")
        return mod.initiate_return_then_refund(dispute_id, order_id, buyer_id, seller_id, amount)
