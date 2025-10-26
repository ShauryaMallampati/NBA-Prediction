"""Unit tests for validators."""

import pytest

from src.common.validators import ValidationError, validate_api_keys


def test_validate_api_keys_missing(monkeypatch):
    """Test that missing keys raise ValidationError."""
    monkeypatch.setenv("REQUIRE_REAL_DATA", "true")
    monkeypatch.setenv("NBA_STATS_API_KEY", "")

    with pytest.raises(ValidationError):
        validate_api_keys(["nba_stats_api_key"])


def test_validate_api_keys_present(monkeypatch):
    """Test that present keys pass validation."""
    monkeypatch.setenv("REQUIRE_REAL_DATA", "true")
    monkeypatch.setenv("NBA_STATS_API_KEY", "test_key_123")

    # Should not raise
    validate_api_keys(["nba_stats_api_key"])
