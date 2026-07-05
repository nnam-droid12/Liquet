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

    # ── Email intake (IMAP) ────────────────────────────────────────────────────
    email_polling_enabled: bool = False
    email_imap_host: str = "imap.gmail.com"
    email_imap_port: int = 993
    email_imap_user: str = ""
    email_imap_password: str = ""          # Gmail: use an App Password
    email_poll_interval_seconds: int = 60

    # ── Email sending (SMTP) ───────────────────────────────────────────────────
    email_smtp_host: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_smtp_user: str = ""
    email_smtp_password: str = ""
    email_from: str = "Liquet Disputes <noreply@liquet.ai>"
    reviewer_email: str = ""               # Where NON LIQUET escalation alerts go

    # ── Webhooks ───────────────────────────────────────────────────────────────
    resolution_webhook_url: str = ""       # POST when LIQUET auto-resolves
    escalation_webhook_url: str = ""       # POST when NON LIQUET escalates

    # ── Human approval ─────────────────────────────────────────────────────────
    approval_secret: str = "change-me"
    app_base_url: str = "http://localhost:8000"

    # ── Paths ──────────────────────────────────────────────────────────────────
    root_dir: Path = Path(__file__).parent
    data_dir: Path = Path(__file__).parent / "data"
    cases_dir: Path = Path(__file__).parent / "data" / "cases"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
