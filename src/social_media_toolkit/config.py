"""Typed application configuration loaded from environment variables."""

from enum import StrEnum
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Category(StrEnum):
    """Categories currently available in the local media library."""

    DOG = "dog"
    CAT = "cat"
    ENTERTAINMENT = "entertainment"
    UNCATEGORIZED = "uncategorized"


class Settings(BaseSettings):
    """Per-device settings; secrets and absolute drive paths stay outside Git."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    media_library_root: Path
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    default_category: Category = Category.UNCATEGORIZED
    log_level: str = "INFO"
    auto_start_jobs: bool = True

    @field_validator("app_host")
    @classmethod
    def require_loopback_host(cls, value: str) -> str:
        """Keep the unauthenticated first release accessible only on this device."""

        if value not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("APP_HOST must be a loopback address")
        return value

    @field_validator("app_port")
    @classmethod
    def require_valid_port(cls, value: int) -> int:
        if not 1 <= value <= 65535:
            raise ValueError("APP_PORT must be between 1 and 65535")
        return value

    @property
    def database_path(self) -> Path:
        return self.media_library_root / "library.db"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"
