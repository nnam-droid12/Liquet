"""
Human-in-the-loop approval endpoint.

GET  /api/cases/{dispute_id}/approve?token=...&decision_id=...&action=approve|override&resolution=...
  → validates token, shows HTML review page OR executes the action immediately

The reviewer receives this link by email. Clicking it either:
  - approve   → executes the agent's leaning verdict
  - override  → executes the human-chosen resolution instead

After execution:
  - Resolution webhook is posted
  - Buyer/seller notified by email
  - Dispute status set to resolved
  - Confirmation HTML page returned
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.database import get_session
from backend.repositories.dispute_repo import (
    AuditRepository, DecisionRepository, DisputeRepository, HumanQueueRepository,
)
from backend.core.models import Actor, AuditEntry, DisputeStatus, ResolutionType
from backend.services.resolution_executor import verify_approval_token, notify_resolution
from config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

_CSS = """
<style>
  body{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 20px;color:#111}
  h1{color:#1e3a5f;border-bottom:2px solid #e5e7eb;padding-bottom:12px}
  .card{background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin:16px 0}
  .label{font-size:.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:.05em}
  .value{font-weight:600;margin-top:2px}
  blockquote{border-left:3px solid #3b82f6;margin:0;padding:8px 16px;
             background:#eff6ff;border-radius:0 6px 6px 0;font-size:.9rem}
  .seller blockquote{border-left-color:#f97316;background:#fff7ed}
  .btn{display:inline-block;padding:12px 28px;border-radius:6px;font-weight:700;
       text-decoration:none;margin:8px 8px 8px 0;font-size:1rem}
  .approve{background:#16a34a;color:#fff}
  .deny{background:#dc2626;color:#fff}
  .refund{background:#2563eb;color:#fff}
  .success{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:24px;text-align:center}
  .error{background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:24px;text-align:center}
  .badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.75rem;font-weight:700}
  .liquet{background:#d1fae5;color:#065f46}
  .nl{background:#fef3c7;color:#92400e}
</style>
"""


def _html(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(f"<!doctype html><html><head><meta charset=utf-8><title>{title}</title>{_CSS}</head><body>{body}</body></html>")


def _resolution_label(r: str) -> str:
    return r.replace("_", " ").title()


@router.get("/api/cases/{dispute_id}/approve", response_class=HTMLResponse)
async def approve_or_review(
    dispute_id: str,
    token: str = Query(...),
    decision_id: str = Query(...),
    action: str = Query("review"),      # review | approve | override
    resolution: str = Query(""),        # used when action=override
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    """
    Entry point for human reviewer.
    - action=review  → show the brief HTML page with buttons
    - action=approve → execute agent's leaning verdict
    - action=override + resolution → execute chosen resolution
    """
    # ── Token validation ──────────────────────────────────────────────────────
    if not verify_approval_token(dispute_id, decision_id, token):
        return _html("Invalid Link", """
            <div class="error">
              <h2>⚠ Link invalid or expired</h2>
              <p>This approval link has expired (72h) or is invalid.
                 Open the case directly in Liquet to take action.</p>
            </div>""")

    # ── Load data ─────────────────────────────────────────────────────────────
    dispute = await DisputeRepository(session).get(dispute_id)
    decision = await DecisionRepository(session).get(decision_id)

    if not dispute or not decision:
        return _html("Not Found", '<div class="error"><h2>Case not found</h2></div>')

    # Already resolved?
    if dispute.status in (DisputeStatus.RESOLVED, DisputeStatus.CLOSED):
        return _html("Already Resolved", f"""
            <div class="success">
              <h2>✓ This dispute is already resolved</h2>
              <p>Status: <strong>{dispute.status.value}</strong></p>
              <p><a href="{settings.app_base_url}/cases/{dispute_id}">View case →</a></p>
            </div>""")

    verdict = decision.verdict
    leaning = verdict.resolution.value
    leaning_label = _resolution_label(leaning)
    confidence = round(verdict.confidence * 100)
    case_url = f"{settings.app_base_url}/cases/{dispute_id}"

    base_params = f"token={token}&decision_id={decision_id}"

    # ── Execute action ────────────────────────────────────────────────────────
    if action in ("approve", "override"):
        chosen_resolution = leaning if action == "approve" else resolution
        if not chosen_resolution:
            return _html("Bad Request", '<div class="error"><h2>No resolution specified</h2></div>')

        try:
            chosen_type = ResolutionType(chosen_resolution)
        except ValueError:
            chosen_type = ResolutionType(leaning)

        # Update dispute status
        await DisputeRepository(session).update_status(dispute_id, DisputeStatus.RESOLVED)

        # Mark queue item resolved
        queue_repo = HumanQueueRepository(session)
        await queue_repo.mark_resolved(decision_id)

        # Audit
        await AuditRepository(session).append(AuditEntry(
            dispute_id=dispute_id,
            event="human_approved" if action == "approve" else "human_override",
            actor=Actor.HUMAN,
            data={
                "action": action,
                "chosen_resolution": chosen_resolution,
                "original_leaning": leaning,
            },
        ))
        await session.commit()

        # Fire notification webhook + emails
        buyer_email = dispute.metadata.get("reply_to", "")
        await notify_resolution(
            dispute_id=dispute_id,
            order_id=dispute.order_id,
            resolution=chosen_resolution,
            confidence=verdict.confidence,
            rationale=verdict.rationale,
            amount=verdict.value_at_stake or 0.0,
            buyer_id=dispute.buyer_id,
            seller_id=dispute.seller_id,
            buyer_email=buyer_email,
        )

        action_word = "approved" if action == "approve" else "overridden"
        return _html("Decision Executed", f"""
            <div class="success">
              <h2>✓ Decision {action_word} and executed</h2>
              <p><strong>Resolution:</strong> {_resolution_label(chosen_resolution)}</p>
              <p>The buyer and seller have been notified. The resolution webhook has been fired.</p>
              <p><a href="{case_url}">View full case →</a></p>
            </div>""")

    # ── Review page (action=review or default) ────────────────────────────────
    approve_url = f"/api/cases/{dispute_id}/approve?{base_params}&action=approve"
    override_deny_url = f"/api/cases/{dispute_id}/approve?{base_params}&action=override&resolution=deny_claim"
    override_refund_url = f"/api/cases/{dispute_id}/approve?{base_params}&action=override&resolution=full_refund"
    override_partial_url = f"/api/cases/{dispute_id}/approve?{base_params}&action=override&resolution=partial_refund"

    return _html(f"Review Dispute {dispute_id[:8].upper()}", f"""
        <h1>⚖ NON LIQUET — Human Review Required</h1>
        <span class="badge nl">NON LIQUET</span>

        <div class="card">
          <div class="label">Order</div><div class="value">{dispute.order_id}</div>
          <div class="label" style="margin-top:8px">Dispute type</div>
          <div class="value">{dispute.dispute_type.value.replace("_"," ").title()}</div>
          <div class="label" style="margin-top:8px">Value at stake</div>
          <div class="value">${verdict.value_at_stake or 0:.2f}</div>
        </div>

        <div class="card">
          <div class="label">Agent's leaning verdict</div>
          <div class="value">{leaning_label} ({confidence}% confidence)</div>
          <div class="label" style="margin-top:8px">Why it abstained</div>
          <div>{decision.abstention_reason or "Confidence or value threshold not met."}</div>
        </div>

        <div class="card">
          <div class="label">Rationale</div>
          <div>{verdict.rationale}</div>
        </div>

        <div class="card">
          <div class="label">Buyer's account</div>
          <blockquote>{dispute.buyer_narrative}</blockquote>
        </div>

        <div class="card seller">
          <div class="label">Seller's account</div>
          <blockquote>{dispute.seller_narrative or "<em>No response provided</em>"}</blockquote>
        </div>

        <h2>Your decision</h2>
        <a href="{approve_url}" class="btn approve">✓ Approve — {leaning_label}</a>
        <a href="{override_deny_url}" class="btn deny">✗ Override → Deny Claim</a>
        <a href="{override_refund_url}" class="btn refund">Override → Full Refund</a>
        <a href="{override_partial_url}" class="btn" style="background:#7c3aed;color:#fff">
          Override → Partial Refund
        </a>

        <p style="margin-top:24px;color:#6b7280;font-size:.85rem">
          <a href="{case_url}">Open full case in Liquet →</a>
          &nbsp;·&nbsp; This link expires 72 hours after the case was escalated.
        </p>
    """)
