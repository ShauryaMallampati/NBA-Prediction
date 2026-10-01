"""Centralized file paths so we don't hardcode them everywhere."""

from pathlib import Path

from src.common.config import settings


class Paths:
    """All the important file paths in one place."""

    ROOT = settings.project_root.expanduser().resolve()
    DATA = ROOT / "data"
    CACHE = DATA / "cache"
    RAW = DATA / "raw"
    PROCESSED = DATA / "processed"
    ARTIFACTS = ROOT / "artifacts"
    MODELS = ARTIFACTS / "models"
    PLOTS = ARTIFACTS / "plots"
    CONFIGS = ROOT / "configs"
    LOGS = ROOT / "logs"

    @classmethod
    def ensure_dirs(cls) -> None:
        """Make sure all these directories exist."""
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, Path) and not attr_name.startswith("_"):
                attr.mkdir(parents=True, exist_ok=True)
