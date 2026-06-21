"""Application settings loaded from environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    db_path: Path = Path("/data/todo.db")
    host: str = "0.0.0.0"
    port: int = 8100
    log_level: str = "info"
    webhook_secret: str = ""
    person_sync_interval_hours: int = 6
    materialise_interval_minutes: int = 60

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.db_path}"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
