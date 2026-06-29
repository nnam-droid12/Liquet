"""
WebSocket endpoint — streams live audit events to the frontend
while an investigation is running.

Connect to: ws://localhost:8080/ws/disputes/{dispute_id}/stream

The server pushes JSON messages of the shape:
  {"type": "audit", "entry": {AuditEntry fields…}}
  {"type": "done",  "gate": "LIQUET" | "NON_LIQUET"}
  {"type": "error", "message": "…"}

The client sends no messages; close the socket when done.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import Dispute, DisputeStatus
from backend.repositories.database import AsyncSessionLocal
from backend.repositories.dispute_repo import (
    AuditRepository, DecisionRepository, DisputeRepository,
)
from backend.services.orchestrator import DisputeOrchestrator

router = APIRouter()
log = structlog.get_logger(__name__)

# Per-dispute broadcast registry: dispute_id -> list of active WebSocket connections
_subscribers: dict[str, list[WebSocket]] = {}


def _register(dispute_id: str, ws: WebSocket) -> None:
    _subscribers.setdefault(dispute_id, []).append(ws)


def _unregister(dispute_id: str, ws: WebSocket) -> None:
    subs = _subscribers.get(dispute_id, [])
    if ws in subs:
        subs.remove(ws)


async def _send(ws: WebSocket, msg: dict) -> bool:
    try:
        await ws.send_text(json.dumps(msg))
        return True
    except Exception:
        return False


async def broadcast(dispute_id: str, msg: dict) -> None:
    """Called by the orchestrator to push an event to all subscribers."""
    dead: list[WebSocket] = []
    for ws in list(_subscribers.get(dispute_id, [])):
        if not await _send(ws, msg):
            dead.append(ws)
    for ws in dead:
        _unregister(dispute_id, ws)


@router.websocket("/ws/disputes/{dispute_id}/stream")
async def dispute_stream(websocket: WebSocket, dispute_id: str) -> None:
    """
    Subscribe to live audit events for a dispute.

    If the investigation hasn't started yet, we trigger it from here.
    If it's already running or done, we replay existing audit entries
    then stream new ones until the dispute reaches a terminal state.
    """
    await websocket.accept()
    _register(dispute_id, websocket)
    log.info("ws_connected", dispute_id=dispute_id)

    try:
        async with AsyncSessionLocal() as session:
            dispute_repo = DisputeRepository(session)
            audit_repo = AuditRepository(session)
            decision_repo = DecisionRepository(session)

            dispute = await dispute_repo.get(dispute_id)
            if dispute is None:
                await _send(websocket, {"type": "error", "message": "Dispute not found"})
                return

            # Replay existing audit entries so the client gets history on connect
            existing_audit = await audit_repo.get_for_dispute(dispute_id)
            for entry in existing_audit:
                await _send(websocket, {
                    "type": "audit",
                    "entry": {
                        "id": entry.id,
                        "event": entry.event,
                        "actor": entry.actor.value if hasattr(entry.actor, 'value') else entry.actor,
                        "data": entry.data,
                        "timestamp": entry.timestamp.isoformat(),
                    },
                })

            # If already decided, send done and close
            existing_decision = await decision_repo.get_by_dispute(dispute_id)
            if existing_decision:
                await _send(websocket, {
                    "type": "done",
                    "gate": existing_decision.gate_result.value,
                    "resolution": existing_decision.verdict.resolution.value,
                })
                return

            # If open, kick off investigation and stream
            if dispute.status == DisputeStatus.OPEN:
                orch = DisputeOrchestrator(session)
                # Wrap the orchestrator so it broadcasts each audit write
                _patch_audit_repo(orch.audit_repo, dispute_id)
                decision = await orch.run(dispute)
                await broadcast(dispute_id, {
                    "type": "done",
                    "gate": decision.gate_result.value,
                    "resolution": decision.verdict.resolution.value,
                })
                return

            # If already investigating (kicked off elsewhere), poll for completion
            if dispute.status == DisputeStatus.INVESTIGATING:
                last_seen_count = len(existing_audit)
                for _ in range(120):  # max 60s at 0.5s intervals
                    await asyncio.sleep(0.5)
                    async with AsyncSessionLocal() as inner:
                        new_audit = await AuditRepository(inner).get_for_dispute(dispute_id)
                        for entry in new_audit[last_seen_count:]:
                            await _send(websocket, {
                                "type": "audit",
                                "entry": {
                                    "id": entry.id,
                                    "event": entry.event,
                                    "actor": entry.actor.value if hasattr(entry.actor, 'value') else entry.actor,
                                    "data": entry.data,
                                    "timestamp": entry.timestamp.isoformat(),
                                },
                            })
                        last_seen_count = len(new_audit)
                        dec = await DecisionRepository(inner).get_by_dispute(dispute_id)
                        if dec:
                            await _send(websocket, {
                                "type": "done",
                                "gate": dec.gate_result.value,
                                "resolution": dec.verdict.resolution.value,
                            })
                            return
                await _send(websocket, {"type": "error", "message": "Investigation timed out"})

    except WebSocketDisconnect:
        log.info("ws_disconnected", dispute_id=dispute_id)
    except Exception as exc:
        log.exception("ws_error", dispute_id=dispute_id, error=str(exc))
        await _send(websocket, {"type": "error", "message": str(exc)})
    finally:
        _unregister(dispute_id, websocket)


def _patch_audit_repo(audit_repo: Any, dispute_id: str) -> None:
    """
    Monkeypatch the AuditRepository.append method to broadcast each
    audit entry to WebSocket subscribers in real time.
    """
    original_append = audit_repo.append.__func__

    async def patched_append(self, entry):  # type: ignore[override]
        await original_append(self, entry)
        await broadcast(dispute_id, {
            "type": "audit",
            "entry": {
                "id": entry.id,
                "event": entry.event,
                "actor": entry.actor.value if hasattr(entry.actor, 'value') else entry.actor,
                "data": entry.data,
                "timestamp": entry.timestamp.isoformat(),
            },
        })

    import types
    audit_repo.append = types.MethodType(patched_append, audit_repo)
