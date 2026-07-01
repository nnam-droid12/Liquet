"""Liquet FastAPI application entry point."""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is importable when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.logging_config import configure_logging
from backend.core.llm_client import smoke_test
from backend.api.disputes import router as disputes_router
from backend.api.cases import router as cases_router
from backend.api.queue import router as queue_router
from backend.api.health import router as health_router
from backend.api.ws import router as ws_router
from backend.api.stats import router as stats_router
from backend.api.seller_risk import router as seller_risk_router
from backend.api.export import router as export_router
from backend.repositories.database import init_db
from config import settings

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Liquet starting",
        env=settings.app_env,
        reasoning_model=settings.active_reasoning_model,
        vision_model=settings.model_vision,
        conf_threshold=settings.conf_threshold,
        value_threshold=settings.value_threshold,
    )
    await init_db()
    try:
        result = await smoke_test()
        logger.info("QwenCloud smoke test", **result)
    except Exception as exc:
        logger.warning("QwenCloud smoke test failed — offline mode", error=str(exc))

    print(
        f"\n{'='*60}\n"
        f"  LIQUET — Marketplace Dispute Resolution Agent\n"
        f"  Track 4: Autopilot Agent | QwenCloud Hackathon\n"
        f"  Env: {settings.app_env} | Region: {os.getenv('ALIBABA_REGION', 'local')}\n"
        f"  Conf threshold: {settings.conf_threshold} | Value threshold: ${settings.value_threshold}\n"
        f"{'='*60}\n"
    )
    yield
    logger.info("Liquet shutting down")


app = FastAPI(
    title="Liquet",
    description="Autonomous marketplace dispute-resolution agent",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(disputes_router, prefix="/api/disputes", tags=["disputes"])
app.include_router(cases_router, prefix="/api/cases", tags=["cases"])
app.include_router(queue_router, prefix="/api/queue", tags=["queue"])
app.include_router(ws_router, tags=["websocket"])
app.include_router(stats_router, tags=["stats"])
app.include_router(seller_risk_router, tags=["analytics"])
app.include_router(export_router, tags=["export"])


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )
