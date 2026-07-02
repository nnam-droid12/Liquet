"""Health and readiness endpoints."""

from __future__ import annotations

import os
import platform
import sys
import time

from fastapi import APIRouter

from config import settings

router = APIRouter(tags=["health"])

_START_TIME = time.time()
VERSION = "1.2.0"


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "liquet",
        "version": VERSION,
        "env": settings.app_env,
        "region": os.getenv("ALIBABA_REGION", "local"),
        "uptime_seconds": round(time.time() - _START_TIME),
        "features": [
            "ghost_cases",
            "stability_scoring",
            "skeptic_pass",
            "seller_risk",
            "reviewer_notes",
            "daily_metrics",
            "confidence_histogram",
            "batch_disputes",
        ],
    }


@router.get("/api/system-info")
async def system_info() -> dict:
    return {
        "service": "Liquet",
        "version": VERSION,
        "description": "Autonomous marketplace dispute-resolution agent",
        "models": {
            "reasoning": settings.model_reasoning,
            "vision": settings.model_vision,
        },
        "gate": {
            "confidence_threshold": settings.conf_threshold,
            "value_threshold": settings.value_threshold,
        },
        "features": {
            "ghost_cases": "Cross-dispute seller pattern mining",
            "stability_scoring": "3x shuffled adjudication with variance-weighted confidence",
            "skeptic_pass": "Adversarial devil-advocate rebuttal challenge",
            "seller_risk": "Seller dispute rate analytics with per-seller drill-down",
            "reviewer_notes": "Human annotator notes on any case",
            "daily_metrics": "Day-by-day volume and resolution trends",
            "confidence_histogram": "Distribution of verdict confidence scores",
        },
        "mcp_servers": 7,
        "python": sys.version.split()[0],
        "platform": platform.system(),
        "uptime_seconds": round(time.time() - _START_TIME),
        "docs": "/docs",
    }


@router.get("/")
async def root() -> dict:
    return {
        "service": "Liquet",
        "description": "Autonomous marketplace dispute-resolution agent",
        "docs": "/docs",
        "health": "/health",
        "system_info": "/api/system-info",
    }
