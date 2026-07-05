"""
Email Service — IMAP intake poller + SMTP sender.

Intake flow:
  1. Poll inbox via IMAP SSL every N seconds
  2. For each unread email: call qwen3.7-max to extract structured dispute fields
  3. Create dispute + start investigation via internal API
  4. Reply to sender with case reference number

Sender:
  send_email(to, subject, html) — generic SMTP helper used by all features
"""

from __future__ import annotations

import asyncio
import email as email_lib
import imaplib
import json
import smtplib
import textwrap
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header

import structlog
from openai import AsyncOpenAI

from config import settings

logger = structlog.get_logger(__name__)

# ── tracks the last UID we processed so we never double-handle ──────────────
_last_uid: int = 0
_processed_uids: set[int] = set()


def _decode_header_val(raw: str) -> str:
    parts = decode_header(raw)
    return "".join(
        part.decode(enc or "utf-8") if isinstance(part, bytes) else part
        for part, enc in parts
    )


def _get_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                return payload.decode(part.get_content_charset() or "utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return ""


async def _extract_dispute_fields(sender: str, subject: str, body: str) -> dict | None:
    """Use qwen3.7-max to parse a raw complaint email into structured dispute fields."""
    client = AsyncOpenAI(
        api_key=settings.qwen_api_key,
        base_url=settings.qwen_base_url,
    )
    system = (
        "You extract structured marketplace dispute information from customer complaint emails. "
        "Return ONLY valid JSON with these fields:\n"
        '  order_id (string, e.g. "ORD-1234" — infer from email if present, else generate plausible one),\n'
        '  dispute_type (one of: not_as_described, never_arrived, wrong_item, damaged, counterfeit),\n'
        '  buyer_narrative (string — the customer\'s complaint in their own words, max 500 chars),\n'
        '  buyer_id (string — use sender email as-is),\n'
        '  seller_id (string — "SELLER-UNKNOWN" if not mentioned)\n'
        "Return ONLY the JSON object, no markdown."
    )
    user = f"From: {sender}\nSubject: {subject}\n\n{body[:2000]}"
    try:
        resp = await client.chat.completions.create(
            model=settings.active_reasoning_model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            max_tokens=512,
            temperature=0,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        return json.loads(raw)
    except Exception as exc:
        logger.error("email_parse_failed", error=str(exc))
        return None


def send_email(to: str, subject: str, html: str) -> None:
    """Send an HTML email via SMTP. Silently skips if SMTP is not configured."""
    if not settings.email_smtp_user or not settings.email_smtp_password:
        logger.info("smtp_not_configured_skipping", to=to, subject=subject)
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.email_from
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(settings.email_smtp_host, settings.email_smtp_port) as s:
            s.ehlo()
            s.starttls()
            s.login(settings.email_smtp_user, settings.email_smtp_password)
            s.sendmail(settings.email_smtp_user, to, msg.as_string())
        logger.info("email_sent", to=to, subject=subject)
    except Exception as exc:
        logger.error("email_send_failed", to=to, error=str(exc))


async def _process_email(sender: str, subject: str, body: str, uid: int) -> None:
    """Parse one email and create a dispute + trigger investigation."""
    # Import here to avoid circular imports
    from backend.repositories.database import AsyncSessionLocal
    from backend.repositories.dispute_repo import DisputeRepository
    from backend.core.models import Dispute, DisputeType

    fields = await _extract_dispute_fields(sender, subject, body)
    if not fields:
        logger.warning("email_parse_returned_nothing", uid=uid)
        return

    try:
        dtype = DisputeType(fields.get("dispute_type", "not_as_described"))
    except ValueError:
        dtype = DisputeType.NOT_AS_DESCRIBED

    dispute = Dispute(
        order_id=fields.get("order_id", f"EMAIL-{uid}"),
        dispute_type=dtype,
        buyer_id=fields.get("buyer_id", sender),
        seller_id=fields.get("seller_id", "SELLER-UNKNOWN"),
        buyer_narrative=fields.get("buyer_narrative", body[:500]),
        seller_narrative="",
        metadata={"source": "email", "email_uid": uid, "reply_to": sender},
    )

    async with AsyncSessionLocal() as session:
        repo = DisputeRepository(session)
        await repo.save(dispute)
        await session.commit()

    logger.info("dispute_created_from_email", dispute_id=dispute.id, order_id=dispute.order_id)

    # Fire-and-forget investigation
    asyncio.create_task(_investigate(dispute.id))

    # Reply to sender
    reply_html = f"""
    <p>Hello,</p>
    <p>We received your dispute regarding order <strong>{dispute.order_id}</strong>.</p>
    <p>Your case reference is: <strong><code>{dispute.id[:8].upper()}</code></strong></p>
    <p>Liquet's autonomous agent is now investigating your claim. You will receive
    another email once a verdict has been reached (typically within a few minutes).</p>
    <p>You can track your case at:
    <a href="{settings.app_base_url}/cases/{dispute.id}">
    {settings.app_base_url}/cases/{dispute.id}</a></p>
    <hr>
    <p><small>Liquet — Autonomous Marketplace Dispute Resolution</small></p>
    """
    send_email(
        to=sender,
        subject=f"Re: {subject} — Case {dispute.id[:8].upper()} opened",
        html=reply_html,
    )


async def _investigate(dispute_id: str) -> None:
    from backend.repositories.database import AsyncSessionLocal
    from backend.repositories.dispute_repo import DisputeRepository
    from backend.services.orchestrator import DisputeOrchestrator
    try:
        async with AsyncSessionLocal() as session:
            dispute = await DisputeRepository(session).get(dispute_id)
            if dispute:
                await DisputeOrchestrator(session).run(dispute)
                await session.commit()
    except Exception as exc:
        logger.error("email_investigation_failed", dispute_id=dispute_id, error=str(exc))


async def poll_inbox_once() -> int:
    """Connect to IMAP, fetch unread emails, process new ones. Returns count processed."""
    global _processed_uids
    if not settings.email_imap_user or not settings.email_imap_password:
        return 0
    processed = 0
    try:
        loop = asyncio.get_event_loop()
        # Run blocking IMAP in thread pool
        uids_and_msgs = await loop.run_in_executor(None, _fetch_unread_imap)
        for uid, sender, subject, body in uids_and_msgs:
            if uid in _processed_uids:
                continue
            _processed_uids.add(uid)
            await _process_email(sender, subject, body, uid)
            processed += 1
        logger.info("inbox_polled", new_emails=processed)
    except Exception as exc:
        logger.error("inbox_poll_failed", error=str(exc))
    return processed


def _fetch_unread_imap() -> list[tuple[int, str, str, str]]:
    """Blocking IMAP fetch — runs in thread executor."""
    results = []
    mail = imaplib.IMAP4_SSL(settings.email_imap_host, settings.email_imap_port)
    mail.login(settings.email_imap_user, settings.email_imap_password)
    mail.select("INBOX")
    _, data = mail.search(None, "UNSEEN")
    if not data or not data[0]:
        mail.logout()
        return results
    uid_list = data[0].split()
    for uid_bytes in uid_list[-20:]:  # process at most 20 per cycle
        uid = int(uid_bytes)
        _, msg_data = mail.fetch(uid_bytes, "(RFC822)")
        raw = msg_data[0][1]
        msg = email_lib.message_from_bytes(raw)
        sender = _decode_header_val(msg.get("From", ""))
        subject = _decode_header_val(msg.get("Subject", "(no subject)"))
        body = _get_body(msg)
        results.append((uid, sender, subject, body))
    mail.logout()
    return results


async def run_email_poller() -> None:
    """Infinite loop — called once from FastAPI lifespan as a background task."""
    logger.info("email_poller_started", interval=settings.email_poll_interval_seconds)
    while True:
        await poll_inbox_once()
        await asyncio.sleep(settings.email_poll_interval_seconds)
