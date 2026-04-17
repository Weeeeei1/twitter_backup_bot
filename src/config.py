"""Configuration management."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # Bot
    bot_token: str = Field(default="", alias="BOT_TOKEN")
    admin_telegram_id: int = Field(default=0, alias="ADMIN_TELEGRAM_ID")

    # Twitter
    twitter_cookies: str = Field(default="[]", alias="TWITTER_COOKIES")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/twitter_backup",
        alias="DATABASE_URL",
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Scheduler
    base_check_interval: int = Field(default=300, alias="BASE_CHECK_INTERVAL")
    min_check_interval: int = Field(default=60, alias="MIN_CHECK_INTERVAL")
    max_check_interval: int = Field(default=3600, alias="MAX_CHECK_INTERVAL")

    # Application
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    version: str = Field(default="v0.1.0", alias="VERSION")

    # Paths
    data_dir: Path = Field(default=Path("data"))

    def get_version(self) -> str:
        """Get formatted version string."""
        return f"v{self.version}" if not self.version.startswith("v") else self.version


# Global settings instance
settings = Settings()


def reload_settings() -> Settings:
    """Reload settings from environment."""
    return Settings(_env_file=".env")
