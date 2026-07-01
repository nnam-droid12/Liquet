"""MCP server status endpoint — verify all tool servers load correctly."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter()

_MCP_SERVERS = [
    "order_service",
    "logistics_service",
    "listing_service",
    "comms_service",
    "vision_intake",
    "policy_engine",
    "resolution_service",
]


@router.get("/api/mcp-status")
async def get_mcp_status() -> dict:
    """Check which MCP tool servers are importable and list their tools."""
    results = {}

    for server_name in _MCP_SERVERS:
        try:
            module_path = f"mcp_servers.{server_name}.server"
            if module_path in sys.modules:
                mod = sys.modules[module_path]
            else:
                mod = importlib.import_module(module_path)

            # Introspect FastMCP instance for tools
            mcp_instance = getattr(mod, "mcp", None)
            tool_names: list[str] = []
            if mcp_instance is not None:
                try:
                    tool_names = [t.name for t in mcp_instance._tool_manager.tools.values()]
                except Exception:
                    tool_names = []

            results[server_name] = {
                "status": "ok",
                "tools": tool_names,
                "tool_count": len(tool_names),
            }
        except Exception as exc:
            results[server_name] = {
                "status": "error",
                "error": str(exc),
                "tools": [],
                "tool_count": 0,
            }

    healthy = sum(1 for v in results.values() if v["status"] == "ok")

    return {
        "servers": results,
        "total": len(_MCP_SERVERS),
        "healthy": healthy,
        "all_healthy": healthy == len(_MCP_SERVERS),
    }
