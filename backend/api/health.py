"""Health and readiness endpoints."""

from __future__ import annotations

import os
import sys

from fastapi import APIRouter

from config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "liquet",
        "version": "1.1.0",
        "env": settings.app_env,
        "region": os.getenv("ALIBABA_REGION", "local"),
        "features": ["ghost_cases", "stability_scoring", "skeptic_pass", "seller_risk"],
    }


@router.get("/api/system-info")
async def system_info() -> dict:
    return {
        "service": "Liquet",
        "version": "1.1.0",
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
            "seller_risk": "Seller dispute rate analytics",
        },
        "mcp_servers": 7,
        "python": sys.version.split()[0],
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
