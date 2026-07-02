"""
Reasoning Glass — WebSocket endpoint that streams qwen3.7-max thinking tokens
in real time as the AI deliberates on a dispute.

Connect to: ws://.../ws/disputes/{id}/think
Receives:
  {"type": "thinking", "content": "..."}   — raw reasoning tokens
  {"type": "verdict",  "content": "..."}   — final answer content
  {"type": "done"}
  {"type": "error",   "message": "..."}
"""

from __future__ import annotations

import json

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI
import httpx

from backend.repositories.database import AsyncSessionLocal
from backend.repositories.dispute_repo import CaseFileRepository, DecisionRepository, DisputeRepository
from config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

THINKING_MODEL = "qwen3.7-max"


def _make_thinking_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.qwen_api_key,
        base_url=settings.qwen_base_url,
        timeout=httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=5.0),
        max_retries=0,
    )


def _build_reasoning_prompt(dispute, case_file, decision) -> list[dict]:
    """Build the messages for the reasoning trace."""
    evidence_text = ""
    if case_file:
        items = []
        for ev in case_file.evidence:
            c = ev.content if isinstance(ev.content, str) else json.dumps(ev.content)
            items.append(f"[{ev.id}] {ev.source} (reliability {ev.reliability:.0%}): {c[:200]}")
        evidence_text = "\n".join(items)

    prior_verdict = ""
    if decision:
        prior_verdict = (
            f"\nPrior adjudication result: {decision.verdict.resolution.value} "
            f"with {decision.verdict.confidence:.0%} confidence.\n"
            f"Gate: {decision.gate_result.value}\n"
            f"Rationale: {decision.verdict.rationale}"
        )

    system = (
        "You are an expert legal arbitrator reasoning about a marketplace dispute. "
        "Think carefully through the evidence, identify contradictions, assess credibility, "
        "and reason step by step toward a verdict. Be thorough and analytical."
    )

    user = f"""Dispute: {dispute.order_id}
Type: {dispute.dispute_type}

Buyer's account:
{dispute.buyer_narrative}

Seller's account:
{dispute.seller_narrative or '(no response)'}

Evidence gathered:
{evidence_text or '(no evidence assembled yet)'}
{prior_verdict}

Reason step by step: Who is more credible? What does the evidence support? What are the key contradictions? What should the resolution be?"""

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


@router.websocket("/ws/disputes/{dispute_id}/think")
async def reasoning_glass(websocket: WebSocket, dispute_id: str) -> None:
    """
    Stream qwen3.7-max thinking tokens to the client in real time.
    The client sees the AI deliberating — each thinking chunk is pushed immediately.
    """
    await websocket.accept()
    logger.info("reasoning_glass_connected", dispute_id=dispute_id)

    async def send(msg: dict) -> None:
        try:
            await websocket.send_text(json.dumps(msg))
        except Exception:
            pass

    try:
        async with AsyncSessionLocal() as session:
            dispute = await DisputeRepository(session).get(dispute_id)
            if dispute is None:
                await send({"type": "error", "message": "Dispute not found"})
                return

            case_file = await CaseFileRepository(session).get(dispute_id)
            decision = await DecisionRepository(session).get_by_dispute(dispute_id)

        messages = _build_reasoning_prompt(dispute, case_file, decision)
        client = _make_thinking_client()

        stream = await client.chat.completions.create(
            model=THINKING_MODEL,
            messages=messages,
            stream=True,
            max_tokens=8192,
            extra_body={"enable_thinking": True},
        )

        thinking_buf = []
        content_buf = []

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue

            # Reasoning/thinking tokens
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning:
                thinking_buf.append(reasoning)
                await send({"type": "thinking", "content": reasoning})

            # Final answer tokens
            if delta.content:
                content_buf.append(delta.content)
                await send({"type": "verdict", "content": delta.content})

        await send({"type": "done", "thinking_length": len("".join(thinking_buf))})
        logger.info("reasoning_glass_done", dispute_id=dispute_id)

    except WebSocketDisconnect:
        logger.info("reasoning_glass_disconnected", dispute_id=dispute_id)
    except Exception as exc:
        logger.error("reasoning_glass_error", error=str(exc))
        await send({"type": "error", "message": str(exc)})
