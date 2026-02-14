"""Validation helpers that fail early if something's wrong."""

from pathlib import Path
from typing import List, Optional

from src.common.config import settings
from src.common.logger import setup_logger

logger = setup_logger(__name__)


class ValidationError(Exception):
    """Thrown when something doesn't pass validation."""

    pass


def validate_api_keys(required_keys: Optional[List[str]] = None) -> None:
    """Check that all the API keys we need are actually set."""
    if not settings.require_real_data:
        logger.warning("REQUIRE_REAL_DATA=false, skipping key validation")
        return

    if required_keys is None:
        required_keys = []

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

Or set REQUIRE_REAL_DATA=false in .env to skip validation (not recommended).
"""
        raise ValidationError(error_msg)

    logger.info(f"✓ All required API keys present ({len(required_keys)} keys)")


def validate_data_exists(data_path: Path, min_rows: int = 100) -> None:
    """Make sure a data file exists and has enough rows to be useful."""
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


def guard_mock_allowed() -> None:
    """Prevent using fake data when we're supposed to use real data."""
    if settings.require_real_data:
        raise ValidationError("Mock data requested but REQUIRE_REAL_DATA=true")
