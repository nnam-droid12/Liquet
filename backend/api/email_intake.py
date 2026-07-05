"""
Email Intake API — status endpoint + manual trigger for the email poller.

GET  /api/email/status      → poller health + last poll stats
POST /api/email/poll        → manually trigger one inbox poll (for demos)
"""

from __future__ import annotations

import time

import structlog
from fastapi import APIRouter

from config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

_poll_stats: dict = {
    "last_poll_at": None,
    "total_processed": 0,
    "last_count": 0,
}


@router.get("/api/email/status")
async def email_status() -> dict:
    """Return email intake configuration status."""
    return {
        "enabled": settings.email_polling_enabled,
        "imap_host": settings.email_imap_host,
        "imap_user": settings.email_imap_user or "(not configured)",
        "poll_interval_seconds": settings.email_poll_interval_seconds,
        "reviewer_email": settings.reviewer_email or "(not configured)",
        "resolution_webhook": bool(settings.resolution_webhook_url),
        "escalation_webhook": bool(settings.escalation_webhook_url),
        **_poll_stats,
    }


@router.post("/api/email/poll")
async def trigger_poll() -> dict:
    """Manually trigger one inbox poll — useful for demos."""
    from backend.services.email_service import poll_inbox_once
    count = await poll_inbox_once()
    _poll_stats["last_poll_at"] = int(time.time())
    _poll_stats["total_processed"] += count
    _poll_stats["last_count"] = count
    return {"processed": count, "message": f"Processed {count} new email(s)"}
