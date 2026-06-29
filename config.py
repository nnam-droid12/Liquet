"""Central configuration for Liquet. All settings read from environment / .env file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    # ── QwenCloud ──────────────────────────────────────────────────────────────
    qwen_api_key: str = "sk-placeholder"
    qwen_base_url: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

    # Two-model design: perception vs. judgment
    model_reasoning: str = "qwen-plus"
    model_vision: str = "qwen-vl-plus"
    cheap_mode: bool = False

    @property
    def active_reasoning_model(self) -> str:
        return self.model_vision if self.cheap_mode else self.model_reasoning

    # ── Alibaba Cloud ──────────────────────────────────────────────────────────
    alibaba_cloud_access_key_id: str = ""
    alibaba_cloud_access_key_secret: str = ""
    oss_bucket_name: str = "liquet-evidence"
    oss_endpoint: str = "oss-us-east-1.aliyuncs.com"
    oss_region: str = "us-east-1"

    # ── Database ───────────────────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./liquet.db"

    # ── App ────────────────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "dev-secret-change-me"

    # ── Liquet gate thresholds ─────────────────────────────────────────────────
    conf_threshold: float = 0.80
    value_threshold: float = 500.00

    # ── MCP server ports ──────────────────────────────────────────────────────
    order_service_port: int = 8001
    logistics_service_port: int = 8002
    listing_service_port: int = 8003
    comms_service_port: int = 8004
    vision_intake_port: int = 8005
    policy_engine_port: int = 8006
    resolution_service_port: int = 8007

    # ── Paths ──────────────────────────────────────────────────────────────────
    root_dir: Path = Path(__file__).parent
    data_dir: Path = Path(__file__).parent / "data"
    cases_dir: Path = Path(__file__).parent / "data" / "cases"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
