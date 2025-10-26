"""Data validation and fail-fast checks."""

from pathlib import Path
from typing import List, Optional

from src.common.config import settings
from src.common.logger import setup_logger

logger = setup_logger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def validate_api_keys(required_keys: Optional[List[str]] = None) -> None:
    """Validate that required API keys are present."""
    if not settings.require_real_data:
        logger.warning("REQUIRE_REAL_DATA=false, skipping key validation")
        return

    if required_keys is None:
        required_keys = [
            "nba_stats_api_key",
            "ors_api_key",
        ]
        if settings.enable_sentiment:
            required_keys.extend(
                ["x_bearer_token", "reddit_client_id", "reddit_client_secret", "youtube_api_key"]
            )

    missing_keys = []
    for key in required_keys:
        value = getattr(settings, key, "")
        if not value or value == "PUT_KEY_HERE":
            missing_keys.append(key.upper())

    if missing_keys:
        error_msg = f"""
╔══════════════════════════════════════════════════════════════╗
║  MISSING REQUIRED API KEYS                                   ║
╚══════════════════════════════════════════════════════════════╝

The following API keys are required but not set:

{chr(10).join(f"  ✗ {key}" for key in missing_keys)}

To fix this:
1. Copy .env.example to .env
2. Fill in the missing keys (see KEYS.md for instructions)
3. Run 'make key-audit' to verify

Or set REQUIRE_REAL_DATA=false in .env to skip validation (not recommended).
"""
        raise ValidationError(error_msg)

    logger.info(f"✓ All required API keys present ({len(required_keys)} keys)")


def validate_data_exists(data_path: Path, min_rows: int = 100) -> None:
    """Validate that required data files exist and are non-empty."""
    if not settings.require_real_data:
        return

    if not data_path.exists():
        raise ValidationError(f"Required data file not found: {data_path}")

    # For parquet files, check row count
    if data_path.suffix == ".parquet":
        import pandas as pd

        df = pd.read_parquet(data_path)
        if len(df) < min_rows:
            raise ValidationError(
                f"Data file has insufficient rows: {data_path} ({len(df)} < {min_rows})"
            )
        logger.info(f"✓ Data validated: {data_path.name} ({len(df)} rows)")
