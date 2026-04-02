from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AIZCODE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "ai-zcode-python-backend"
    api_prefix: str = "/api"
    cors_origins: list[str] = ["http://localhost:5173"]
    public_api_base_url: str = "http://localhost:8335/api"
    database_url: str = "sqlite:///./ai_zcode.db"
    redis_url: str = "redis://localhost:6379/0"
    session_secret: str = "change-this-session-secret"
    session_cookie_name: str = "aizcode_session"
    session_ttl_seconds: int = 60 * 60 * 24 * 30
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4.1-mini"
    openai_enable_thinking: bool | None = None
    routing_openai_api_key: str | None = None
    routing_openai_base_url: str | None = None
    routing_openai_model: str | None = None
    routing_openai_enable_thinking: bool | None = None
    testing: bool = False
    repo_root: str | None = None
    code_deploy_host: str = "http://localhost"
    good_app_cache_ttl_seconds: int = 300
    app_vo_cache_ttl_seconds: int = 300
    chat_rate_limit: int = 5
    chat_rate_interval_seconds: int = 60
    screenshot_width: int = 1600
    screenshot_height: int = 900
    screenshot_timeout_seconds: int = 30
    vue_install_command: str = "npm install"
    vue_build_command: str = "npm run build"

    @field_validator(
        "openai_api_key",
        "openai_base_url",
        "repo_root",
        "routing_openai_api_key",
        "routing_openai_base_url",
        "routing_openai_model",
        mode="before",
    )
    @classmethod
    def normalize_blank_optional_strings(cls, value: Any):
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @property
    def resolved_repo_root(self) -> Path:
        if self.repo_root:
            return Path(self.repo_root).resolve()
        return Path(__file__).resolve().parents[3]

    @property
    def code_output_root(self) -> Path:
        return self.resolved_repo_root / "tmp" / "code_output"

    @property
    def code_deploy_root(self) -> Path:
        return self.resolved_repo_root / "tmp" / "code_deploy"

    @property
    def screenshot_root(self) -> Path:
        return self.resolved_repo_root / "tmp" / "screenshots"


def build_settings(overrides: dict[str, Any] | None = None) -> Settings:
    if not overrides:
        return Settings()
    return Settings.model_validate(overrides)
