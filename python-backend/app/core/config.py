from __future__ import annotations

from pathlib import Path
from typing import Any

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
    database_url: str = "sqlite:///./ai_zcode.db"
    redis_url: str = "redis://localhost:6379/0"
    session_secret: str = "change-this-session-secret"
    session_cookie_name: str = "aizcode_session"
    session_ttl_seconds: int = 60 * 60 * 24 * 30
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4.1-mini"
    testing: bool = False
    repo_root: str | None = None
    code_deploy_host: str = "http://localhost"
    vue_install_command: str = "npm install"
    vue_build_command: str = "npm run build"

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


def build_settings(overrides: dict[str, Any] | None = None) -> Settings:
    if not overrides:
        return Settings()
    return Settings.model_validate(overrides)
