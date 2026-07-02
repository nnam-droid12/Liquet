"""
Verdict Narration endpoint — converts verdict text to speech via CosyVoice v3 Plus.

POST /api/cases/{id}/narrate  →  { audio_b64: "...", duration_hint: N, text: "..." }
"""

from __future__ import annotations

import base64
import textwrap

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.database import get_session
from backend.repositories.dispute_repo import CaseFileRepository, DecisionRepository, DisputeRepository
from config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

DASHSCOPE_TTS_URL = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text2speech/completion"
TTS_MODEL = "cosyvoice-v3-plus"
TTS_VOICE = "longxiaochun_v2"


def _build_narration(dispute, case_file, decision) -> str:
    """Craft a natural-language narration script for the verdict."""
    gate = decision.gate_result.value
    resolution = decision.verdict.resolution.value.replace("_", " ")
    confidence = round(decision.verdict.confidence * 100)
    rationale = decision.verdict.rationale

    if gate == "LIQUET":
        opener = "Liquet has reviewed this dispute and reached a clear decision."
        conclusion = (
            f"The resolution is: {resolution}. "
            f"The adjudication confidence is {confidence} percent. "
        )
    else:
        opener = "Liquet has reviewed this dispute, but the evidence is insufficient for autonomous resolution."
        conclusion = (
            f"This case has been escalated for human review. "
            f"The agent's leaning verdict is {resolution}, with {confidence} percent confidence. "
        )

    if decision.stability_result:
        runs = decision.stability_result.runs
        stab = round(decision.stability_result.stability_score * 100)
        conclusion += f"Verdict stability across three independent reasoning runs was {stab} percent. "

    if decision.skeptic_result:
        if decision.skeptic_result.verdict_contested:
            conclusion += "Note: the adversarial skeptic pass contested this verdict. "
        else:
            strength = round(decision.skeptic_result.rebuttal_strength * 100)
            conclusion += f"The verdict withstood adversarial challenge with a rebuttal strength of {strength} percent. "

    return f"{opener} {rationale} {conclusion}"


@router.post("/api/cases/{dispute_id}/narrate")
async def narrate_verdict(
    dispute_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Generate an audio narration of the verdict using CosyVoice v3 Plus."""
    decision_repo = DecisionRepository(session)
    decision = await decision_repo.get_by_dispute(dispute_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="No decision found — investigate first")

    dispute_repo = DisputeRepository(session)
    dispute = await dispute_repo.get(dispute_id)
    case_repo = CaseFileRepository(session)
    case_file = await case_repo.get(dispute_id)

    narration_text = _build_narration(dispute, case_file, decision)
    logger.info("narrating_verdict", dispute_id=dispute_id, chars=len(narration_text))

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                DASHSCOPE_TTS_URL,
                headers={
                    "Authorization": f"Bearer {settings.qwen_api_key}",
                    "Content-Type": "application/json",
                    "X-DashScope-DataInspection": "disable",
                },
                json={
                    "model": TTS_MODEL,
                    "input": {"text": narration_text},
                    "parameters": {
                        "voice": TTS_VOICE,
                        "format": "mp3",
                        "sample_rate": 22050,
                        "volume": 50,
                        "rate": 1.0,
                        "pitch": 1.0,
                    },
                },
            )
            resp.raise_for_status()

            ct = resp.headers.get("content-type", "")
            if "audio" in ct or "octet-stream" in ct:
                audio_bytes = resp.content
            else:
                data = resp.json()
                if "output" in data and "audio" in data["output"]:
                    raw = data["output"]["audio"]
                    audio_bytes = base64.b64decode(raw) if isinstance(raw, str) else raw
                else:
                    raise ValueError(f"Unexpected TTS response: {list(data.keys())}")

        audio_b64 = base64.b64encode(audio_bytes).decode()
        logger.info("narration_generated", dispute_id=dispute_id, bytes=len(audio_bytes))

        return {
            "dispute_id": dispute_id,
            "text": narration_text,
            "audio_b64": audio_b64,
            "model": TTS_MODEL,
            "voice": TTS_VOICE,
            "format": "mp3",
            "gate": decision.gate_result.value,
        }

    except httpx.HTTPStatusError as exc:
        logger.error("tts_api_error", status=exc.response.status_code, body=exc.response.text[:300])
        raise HTTPException(status_code=502, detail=f"CosyVoice API error: {exc.response.status_code}")
    except Exception as exc:
        logger.error("narration_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Narration failed: {exc}")


@router.get("/api/cases/{dispute_id}/narrate/audio")
async def stream_narration_audio(
    dispute_id: str,
    session: AsyncSession = Depends(get_session),
) -> Response:
    """Stream MP3 audio for direct <audio> tag src usage."""
    result = await narrate_verdict(dispute_id, session)
    audio_bytes = base64.b64decode(result["audio_b64"])
    return Response(content=audio_bytes, media_type="audio/mpeg")
