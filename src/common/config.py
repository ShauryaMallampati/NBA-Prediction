"""Runtime configuration for the local prediction API and artifact workspace."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load the small set of runtime settings used by the supported pipeline."""

    project_root: Path = Field(default_factory=Path.cwd, validation_alias="NBA_PROJECT_ROOT")
    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8000)
    cors_origins: str = Field(default="http://localhost:8000")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
