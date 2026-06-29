"""Health and readiness endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter

from config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "liquet",
        "version": "1.0.0",
        "env": settings.app_env,
        "region": os.getenv("ALIBABA_REGION", "local"),
    }


@router.get("/")
async def root() -> dict:
    return {
        "service": "Liquet",
        "description": "Autonomous marketplace dispute-resolution agent",
        "track": "Track 4: Autopilot Agent",
        "docs": "/docs",
    }
