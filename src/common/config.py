"""App configuration - loads settings from environment variables."""

import os
from pathlib import Path
from typing import Any, Dict


from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main settings for the app - loaded from .env file if it exists."""

    # Database connections (we don't strictly need these)
    database_url: str = Field(default="postgresql://postgres:postgres@localhost:5432/nba_intel")
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Main app settings
    simplified_mode: bool = Field(default=True)
    allow_mock_data: bool = Field(default=False)
    require_real_data: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    device: str = Field(default="mps")

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    cors_origins: str = Field(default="http://localhost:8000")

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )



# Create the global settings object (used everywhere)
settings = Settings()
