"""
Resolution Executor — fires webhooks and sends email notifications when Liquet
makes a decision.

Called by the orchestrator in two cases:
  1. LIQUET auto-resolved  → POST resolution webhook + email buyer + seller
  2. NON LIQUET escalated  → POST escalation webhook + email reviewer with approval link
"""

from __future__ import annotations

import hashlib
import hmac
import time

import httpx
import structlog

from config import settings

logger = structlog.get_logger(__name__)


# ── Approval token ────────────────────────────────────────────────────────────

def make_approval_token(dispute_id: str, decision_id: str, ttl_hours: int = 72) -> str:
    """Create a signed, time-limited approval token."""
    expiry = int(time.time()) + ttl_hours * 3600
    payload = f"{dispute_id}:{decision_id}:{expiry}"
    sig = hmac.new(  # noqa: S324
        settings.approval_secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{expiry}.{sig}"


def verify_approval_token(dispute_id: str, decision_id: str, token: str) -> bool:
    """Return True if the token is valid and not expired."""
    try:
        expiry_str, sig = token.split(".", 1)
        expiry = int(expiry_str)
        if time.time() > expiry:
            return False
        payload = f"{dispute_id}:{decision_id}:{expiry}"
        expected = hmac.new(
            settings.approval_secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(sig, expected)
    except Exception:
        return False


# ── Webhook helper ────────────────────────────────────────────────────────────

async def _post_webhook(url: str, payload: dict) -> None:
    if not url:
        logger.debug("webhook_url_not_configured_skipping")
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            r.raise_for_status()
        logger.info("webhook_posted", url=url, status=r.status_code)
    except Exception as exc:
        logger.error("webhook_failed", url=url, error=str(exc))


# ── Resolution notification (LIQUET) ─────────────────────────────────────────

async def notify_resolution(
    dispute_id: str,
    order_id: str,
    resolution: str,
    confidence: float,
    rationale: str,
    amount: float,
    buyer_id: str,
    seller_id: str,
    buyer_email: str = "",
    seller_email: str = "",
) -> None:
    """Called when LIQUET gate passes. Fires webhook + emails both parties."""
    payload = {
        "event": "dispute.resolved",
        "dispute_id": dispute_id,
        "order_id": order_id,
        "resolution": resolution,
        "confidence": round(confidence, 3),
        "amount": amount,
        "rationale": rationale,
        "gate": "LIQUET",
        "timestamp": int(time.time()),
    }
    await _post_webhook(settings.resolution_webhook_url, payload)

    from backend.services.email_service import send_email

    resolution_label = resolution.replace("_", " ").title()
    case_url = f"{settings.app_base_url}/cases/{dispute_id}"

    if buyer_email:
        send_email(
            to=buyer_email,
            subject=f"Your dispute for {order_id} has been resolved — {resolution_label}",
            html=f"""
            <p>Hello,</p>
            <p>Liquet has resolved your dispute for order <strong>{order_id}</strong>.</p>
            <p><strong>Decision:</strong> {resolution_label}</p>
            <p><strong>Confidence:</strong> {round(confidence * 100)}%</p>
            <p><strong>Rationale:</strong> {rationale}</p>
            <p><a href="{case_url}">View full case →</a></p>
            <hr><small>Liquet Autonomous Dispute Resolution</small>
            """,
        )

    if seller_email:
        send_email(
            to=seller_email,
            subject=f"Dispute resolved for order {order_id} — {resolution_label}",
            html=f"""
            <p>Hello,</p>
            <p>A dispute for order <strong>{order_id}</strong> has been resolved by Liquet.</p>
            <p><strong>Decision:</strong> {resolution_label}</p>
            <p><strong>Rationale:</strong> {rationale}</p>
            <p><a href="{case_url}">View full case →</a></p>
            <hr><small>Liquet Autonomous Dispute Resolution</small>
            """,
        )

    logger.info("resolution_notified", dispute_id=dispute_id, resolution=resolution)


# ── Escalation notification (NON LIQUET) ─────────────────────────────────────

async def notify_escalation(
    dispute_id: str,
    decision_id: str,
    order_id: str,
    order_value: float,
    dispute_type: str,
    leaning_verdict: str,
    leaning_confidence: float,
    abstention_reason: str,
    buyer_narrative: str,
    seller_narrative: str,
) -> None:
    """Called when NON LIQUET gate fires. Posts escalation webhook + emails reviewer."""
    brief_url = f"{settings.app_base_url}/cases/{dispute_id}"
    token = make_approval_token(dispute_id, decision_id)
    approve_url = (
        f"{settings.app_base_url}/api/cases/{dispute_id}/approve"
        f"?token={token}&decision_id={decision_id}&action=approve"
    )
    override_deny_url = (
        f"{settings.app_base_url}/api/cases/{dispute_id}/approve"
        f"?token={token}&decision_id={decision_id}&action=override&resolution=deny_claim"
    )
    override_refund_url = (
        f"{settings.app_base_url}/api/cases/{dispute_id}/approve"
        f"?token={token}&decision_id={decision_id}&action=override&resolution=full_refund"
    )

    payload = {
        "event": "dispute.escalated",
        "dispute_id": dispute_id,
        "decision_id": decision_id,
        "order_id": order_id,
        "order_value": order_value,
        "dispute_type": dispute_type,
        "leaning_verdict": leaning_verdict,
        "leaning_confidence": round(leaning_confidence, 3),
        "abstention_reason": abstention_reason,
        "review_url": brief_url,
        "approve_url": approve_url,
        "gate": "NON_LIQUET",
        "timestamp": int(time.time()),
    }
    await _post_webhook(settings.escalation_webhook_url, payload)

    from backend.services.email_service import send_email

    if settings.reviewer_email:
        send_email(
            to=settings.reviewer_email,
            subject=f"[REVIEW NEEDED] Dispute {dispute_id[:8].upper()} — {order_id} (${order_value:.2f})",
            html=f"""
            <div style="font-family:sans-serif;max-width:680px">
            <h2 style="color:#b45309">⚠ NON LIQUET — Human Review Required</h2>
            <table style="border-collapse:collapse;width:100%">
              <tr><td style="padding:6px;color:#6b7280">Order</td>
                  <td style="padding:6px;font-weight:bold">{order_id}</td></tr>
              <tr style="background:#f9fafb"><td style="padding:6px;color:#6b7280">Value</td>
                  <td style="padding:6px">${order_value:.2f}</td></tr>
              <tr><td style="padding:6px;color:#6b7280">Type</td>
                  <td style="padding:6px">{dispute_type.replace("_"," ").title()}</td></tr>
              <tr style="background:#f9fafb"><td style="padding:6px;color:#6b7280">Agent's lean</td>
                  <td style="padding:6px">{leaning_verdict.replace("_"," ").title()}
                  ({round(leaning_confidence*100)}% confidence)</td></tr>
              <tr><td style="padding:6px;color:#6b7280">Why abstained</td>
                  <td style="padding:6px">{abstention_reason}</td></tr>
            </table>
            <h3>Buyer's account</h3>
            <blockquote style="border-left:3px solid #3b82f6;padding-left:12px;color:#374151">
              {buyer_narrative[:600]}
            </blockquote>
            <h3>Seller's account</h3>
            <blockquote style="border-left:3px solid #f97316;padding-left:12px;color:#374151">
              {seller_narrative[:600] if seller_narrative else "<em>No response</em>"}
            </blockquote>
            <div style="margin-top:24px">
              <a href="{approve_url}"
                 style="background:#16a34a;color:white;padding:12px 24px;border-radius:6px;
                        text-decoration:none;font-weight:bold;margin-right:12px">
                ✓ Approve Agent Verdict
              </a>
              <a href="{override_deny_url}"
                 style="background:#dc2626;color:white;padding:12px 24px;border-radius:6px;
                        text-decoration:none;font-weight:bold;margin-right:12px">
                Override → Deny Claim
              </a>
              <a href="{override_refund_url}"
                 style="background:#2563eb;color:white;padding:12px 24px;border-radius:6px;
                        text-decoration:none;font-weight:bold">
                Override → Full Refund
              </a>
            </div>
            <p style="margin-top:16px">
              <a href="{brief_url}">View full case in Liquet →</a>
            </p>
            <hr>
            <small style="color:#9ca3af">Liquet Autonomous Dispute Resolution ·
            This link expires in 72 hours.</small>
            </div>
            """,
        )

    logger.info("escalation_notified", dispute_id=dispute_id, reviewer=settings.reviewer_email)
