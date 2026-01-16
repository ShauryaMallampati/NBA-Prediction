"""Configuration management."""

import os
from pathlib import Path
from typing import Any, Dict


from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # API Keys
    nba_stats_api_key: str = Field(default="", alias="NBA_STATS_API_KEY")
    x_bearer_token: str = Field(default="", alias="X_BEARER_TOKEN")
    reddit_client_id: str = Field(default="", alias="REDDIT_CLIENT_ID")
    reddit_client_secret: str = Field(default="", alias="REDDIT_CLIENT_SECRET")
    youtube_api_key: str = Field(default="", alias="YOUTUBE_API_KEY")
    ors_api_key: str = Field(default="", alias="ORS_API_KEY")
    odds_api_key: str = Field(default="", alias="ODDS_API_KEY")
    rapidapi_key: str = Field(default="", alias="RAPIDAPI_KEY")

    # Database
    database_url: str = Field(default="postgresql://postgres:postgres@localhost:5432/nba_intel")
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Supabase
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_key: str = Field(default="", alias="SUPABASE_KEY")

    # Application
    simplified_mode: bool = Field(default=True)
    allow_mock_data: bool = Field(default=False)
    require_real_data: bool = Field(default=True)
    enable_chemistry: bool = Field(default=True)
    enable_sentiment: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    device: str = Field(default="mps")

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    cors_origins: str = Field(default="http://localhost:3000")

    # Betting Strategy (Kelly Criterion)
    bankroll: float = Field(default=1000.0, alias="BANKROLL")
    kelly_fraction: float = Field(default=0.25, alias="KELLY_FRACTION")
    min_edge: float = Field(default=0.05, alias="MIN_EDGE")
    max_bet_pct: float = Field(default=0.05, alias="MAX_BET_PCT")

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )



# Global settings instance
settings = Settings()
