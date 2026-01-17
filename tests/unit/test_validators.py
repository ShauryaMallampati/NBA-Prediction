"""Unit tests for validators."""

import pytest
from unittest.mock import patch, MagicMock

from src.common.validators import ValidationError, validate_api_keys


def test_validate_api_keys_missing():
    """Test that missing keys raise ValidationError."""
    # Create a mock settings with require_real_data=True and empty key
    mock_settings = MagicMock()
    mock_settings.require_real_data = True
    mock_settings.nba_stats_api_key = ""  # Empty key should trigger error
    
    with patch('src.common.validators.settings', mock_settings):
        with pytest.raises(ValidationError):
            validate_api_keys(["nba_stats_api_key"])


def test_validate_api_keys_present():
    """Test that present keys pass validation."""
    # Create a mock settings with require_real_data=True and valid key
    mock_settings = MagicMock()
    mock_settings.require_real_data = True
    mock_settings.nba_stats_api_key = "test_key_123"
    
    with patch('src.common.validators.settings', mock_settings):
        # Should not raise
        validate_api_keys(["nba_stats_api_key"])


def test_validate_api_keys_skipped_when_not_required():
    """Test that validation is skipped when require_real_data is False."""
    mock_settings = MagicMock()
    mock_settings.require_real_data = False
    mock_settings.nba_stats_api_key = ""  # Empty but should not raise
    
    with patch('src.common.validators.settings', mock_settings):
        # Should not raise because require_real_data is False
        validate_api_keys(["nba_stats_api_key"])

