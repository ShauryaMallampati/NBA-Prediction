"""Unit tests for configuration."""

from src.common.config import settings


def test_settings_loads():
    """Test that settings are loaded and have expected attributes."""
    assert hasattr(settings, "log_level")
    assert hasattr(settings, "api_port")
    assert hasattr(settings, "database_url")
    assert hasattr(settings, "supabase_url")
    assert hasattr(settings, "supabase_key")


def test_settings_defaults():
    """Test default values are set correctly."""
    # These should have defaults
    assert settings.api_port == 8000
    assert settings.log_level == "INFO"
    assert settings.simplified_mode is True
