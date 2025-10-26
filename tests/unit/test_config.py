"""Unit tests for configuration."""

from src.common.config import load_config


def test_load_config():
    """Test loading YAML config."""
    config = load_config("config")
    assert "project" in config
    assert "data" in config
    assert "models" in config
