"""Path management for data and artifacts."""

from pathlib import Path


class Paths:
    """Centralized path management."""

    ROOT = Path(__file__).parent.parent.parent
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
        """Create all necessary directories."""
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, Path) and not attr_name.startswith("_"):
                attr.mkdir(parents=True, exist_ok=True)


# Ensure directories exist on import
Paths.ensure_dirs()
