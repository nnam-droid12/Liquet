"""
Scene Reconstruction endpoint — generates an AI image of the dispute scenario
using wan2.6-t2i (Alibaba Cloud text-to-image model).

POST /api/cases/{id}/visualize    →  submits task, returns task_id
GET  /api/cases/{id}/scene        →  polls task, returns image_url when ready
"""

from __future__ import annotations

import asyncio

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.database import get_session
from backend.repositories.dispute_repo import CaseFileRepository, DecisionRepository, DisputeRepository
from config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

DASHSCOPE_IMG_URL = "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
DASHSCOPE_TASK_URL = "https://dashscope-intl.aliyuncs.com/api/v1/tasks/{task_id}"
IMAGE_MODEL = "wan2.6-t2i"

# In-memory cache of completed images per dispute
_image_cache: dict[str, dict] = {}


def _build_image_prompt(dispute, case_file, decision) -> tuple[str, str]:
    """Build a descriptive prompt for the dispute scene."""
    dtype = dispute.dispute_type.replace("_", " ")
    narrative = dispute.buyer_narrative[:300]
    order_id = dispute.order_id

    evidence_hints = []
    if case_file:
        for ev in case_file.evidence[:3]:
            if ev.evidence_type in ("photo", "listing_data", "carrier_scan"):
                c = ev.content if isinstance(ev.content, str) else str(ev.content)
                evidence_hints.append(c[:100])

    ev_context = ". ".join(evidence_hints) if evidence_hints else ""

    prompt = (
        f"A realistic product photograph showing a marketplace dispute scenario: {dtype}. "
        f"Scene context: {narrative[:200]}. "
        f"{ev_context} "
        f"Professional product photography, e-commerce style, neutral white background, "
        f"high detail, realistic lighting, documentary photo."
    )

    negative = (
        "cartoon, illustration, anime, text, watermark, people, faces, "
        "blur, low quality, distorted"
    )

    return prompt[:800], negative


@router.post("/api/cases/{dispute_id}/visualize")
async def start_scene_reconstruction(
    dispute_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Submit a wan2.6-t2i image generation task for this dispute.
    Returns immediately with a task_id; poll /scene to check status.
    """
    if dispute_id in _image_cache:
        return {"dispute_id": dispute_id, "status": "cached", **_image_cache[dispute_id]}

    dispute_repo = DisputeRepository(session)
    dispute = await dispute_repo.get(dispute_id)
    if dispute is None:
        raise HTTPException(status_code=404, detail="Dispute not found")

    case_repo = CaseFileRepository(session)
    case_file = await case_repo.get(dispute_id)
    decision_repo = DecisionRepository(session)
    decision = await decision_repo.get_by_dispute(dispute_id)

    prompt, negative = _build_image_prompt(dispute, case_file, decision)
    logger.info("scene_reconstruction_started", dispute_id=dispute_id)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                DASHSCOPE_IMG_URL,
                headers={
                    "Authorization": f"Bearer {settings.qwen_api_key}",
                    "Content-Type": "application/json",
                    "X-DashScope-Async": "enable",
                },
                json={
                    "model": IMAGE_MODEL,
                    "input": {
                        "prompt": prompt,
                        "negative_prompt": negative,
                    },
                    "parameters": {
                        "size": "1024*576",
                        "n": 1,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()

        task_id = data.get("output", {}).get("task_id")
        if not task_id:
            raise ValueError(f"No task_id in response: {data}")

        logger.info("scene_task_submitted", dispute_id=dispute_id, task_id=task_id)
        return {
            "dispute_id": dispute_id,
            "task_id": task_id,
            "status": "pending",
            "prompt_preview": prompt[:120],
            "model": IMAGE_MODEL,
        }

    except httpx.HTTPStatusError as exc:
        logger.error("image_api_error", status=exc.response.status_code, body=exc.response.text[:300])
        raise HTTPException(status_code=502, detail=f"wan2.6-t2i API error: {exc.response.status_code}")
    except Exception as exc:
        logger.error("scene_reconstruction_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=f"Scene reconstruction failed: {exc}")


@router.get("/api/cases/{dispute_id}/scene")
async def get_scene_status(
    dispute_id: str,
    task_id: str,
) -> dict:
    """Poll a wan2.6-t2i task and return the image URL when ready."""
    if dispute_id in _image_cache:
        return {"dispute_id": dispute_id, "status": "succeeded", **_image_cache[dispute_id]}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                DASHSCOPE_TASK_URL.format(task_id=task_id),
                headers={"Authorization": f"Bearer {settings.qwen_api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()

        output = data.get("output", {})
        task_status = output.get("task_status", "PENDING").lower()

        if task_status == "succeeded":
            results = output.get("results", [])
            image_url = results[0].get("url") if results else None
            entry = {
                "image_url": image_url,
                "task_id": task_id,
                "model": IMAGE_MODEL,
            }
            _image_cache[dispute_id] = entry
            return {"dispute_id": dispute_id, "status": "succeeded", **entry}

        if task_status == "failed":
            return {"dispute_id": dispute_id, "status": "failed", "task_id": task_id,
                    "error": output.get("message", "Unknown error")}

        return {"dispute_id": dispute_id, "status": task_status, "task_id": task_id}

    except Exception as exc:
        logger.error("scene_poll_failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
