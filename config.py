"""Central configuration for Liquet. All settings read from environment / .env file."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # ── QwenCloud ──────────────────────────────────────────────────────────────
    qwen_api_key: str = Field(..., env="QWEN_API_KEY")
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    # Two-model design: perception vs. judgment
    model_reasoning: str = "qwen-plus"   # qwen3.7-max when available in intl API
    model_vision: str = "qwen-vl-plus"   # qwen3.6-plus (vision-language)
    cheap_mode: bool = Field(default=False, env="CHEAP_MODE")

    @property
    def active_reasoning_model(self) -> str:
        return self.model_vision if self.cheap_mode else self.model_reasoning

    # ── Alibaba Cloud ──────────────────────────────────────────────────────────
    alibaba_access_key_id: str = Field(default="", env="ALIBABA_CLOUD_ACCESS_KEY_ID")
    alibaba_access_key_secret: str = Field(default="", env="ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    oss_bucket_name: str = Field(default="liquet-evidence", env="OSS_BUCKET_NAME")
    oss_endpoint: str = Field(default="oss-us-east-1.aliyuncs.com", env="OSS_ENDPOINT")
    oss_region: str = Field(default="us-east-1", env="OSS_REGION")

    # ── Database ───────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="sqlite+aiosqlite:///./liquet.db", env="DATABASE_URL"
    )

    # ── App ────────────────────────────────────────────────────────────────────
    app_env: str = Field(default="development", env="APP_ENV")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    secret_key: str = Field(default="dev-secret-change-me", env="SECRET_KEY")

    # ── Liquet gate thresholds ─────────────────────────────────────────────────
    conf_threshold: float = Field(default=0.80, env="CONF_THRESHOLD")
    value_threshold: float = Field(default=500.00, env="VALUE_THRESHOLD")

    # ── MCP server ports ──────────────────────────────────────────────────────
    order_service_port: int = Field(default=8001, env="ORDER_SERVICE_PORT")
    logistics_service_port: int = Field(default=8002, env="LOGISTICS_SERVICE_PORT")
    listing_service_port: int = Field(default=8003, env="LISTING_SERVICE_PORT")
    comms_service_port: int = Field(default=8004, env="COMMS_SERVICE_PORT")
    vision_intake_port: int = Field(default=8005, env="VISION_INTAKE_PORT")
    policy_engine_port: int = Field(default=8006, env="POLICY_ENGINE_PORT")
    resolution_service_port: int = Field(default=8007, env="RESOLUTION_SERVICE_PORT")

    # ── Paths ──────────────────────────────────────────────────────────────────
    root_dir: Path = Path(__file__).parent
    data_dir: Path = Path(__file__).parent / "data"
    cases_dir: Path = Path(__file__).parent / "data" / "cases"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Convenience alias
settings = get_settings()
