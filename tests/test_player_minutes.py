
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime
import sys
import os
import asyncio

# Add src to path if needed, though usually pytest handles this
sys.path.append(os.getcwd())

from src.services.player_minutes import fetch_minutes_yesterday

class TestFetchMinutesYesterday:

    @pytest.mark.asyncio
    @patch('src.services.player_minutes.get_player_fetcher')
    async def test_fetch_minutes_yesterday_success(self, mock_get_fetcher):
        # Setup mock
        mock_fetcher = MagicMock()
        mock_get_fetcher.return_value = mock_fetcher

        # Mock search_players
        mock_fetcher.search_players.return_value = [{'id': 123, 'full_name': 'Test Player'}]

        # Mock get_player_stats
        # Assuming current_date is 2024-10-26, yesterday is 2024-10-25
        mock_fetcher.get_player_stats.return_value = [
            {'GAME_DATE': '2024-10-25T00:00:00', 'MIN': 30.5},
            {'GAME_DATE': '2024-10-23T00:00:00', 'MIN': 28.0}
        ]

        player_name = "Test Player"
        current_date = date(2024, 10, 26)

        minutes = await fetch_minutes_yesterday(player_name, current_date)

        assert minutes == 30.5
        mock_fetcher.search_players.assert_called_with(player_name)
        mock_fetcher.get_player_stats.assert_called_with(123, last_n_games=5)

    @pytest.mark.asyncio
    @patch('src.services.player_minutes.get_player_fetcher')
    async def test_fetch_minutes_yesterday_no_game(self, mock_get_fetcher):
        # Setup mock
        mock_fetcher = MagicMock()
        mock_get_fetcher.return_value = mock_fetcher

        # Mock search_players
        mock_fetcher.search_players.return_value = [{'id': 123, 'full_name': 'Test Player'}]

        # Mock get_player_stats - No game yesterday
        mock_fetcher.get_player_stats.return_value = [
            {'GAME_DATE': '2024-10-23T00:00:00', 'MIN': 28.0}
        ]

        player_name = "Test Player"
        current_date = date(2024, 10, 26)

        minutes = await fetch_minutes_yesterday(player_name, current_date)

        assert minutes == 0.0

    @pytest.mark.asyncio
    @patch('src.services.player_minutes.get_player_fetcher')
    async def test_fetch_minutes_yesterday_player_not_found(self, mock_get_fetcher):
        # Setup mock
        mock_fetcher = MagicMock()
        mock_get_fetcher.return_value = mock_fetcher

        # Mock search_players - Not found
        mock_fetcher.search_players.return_value = []

        player_name = "Unknown Player"
        current_date = date(2024, 10, 26)

        minutes = await fetch_minutes_yesterday(player_name, current_date)

        assert minutes == 0.0

    @pytest.mark.asyncio
    @patch('src.services.player_minutes.get_player_fetcher')
    async def test_fetch_minutes_yesterday_different_date_format(self, mock_get_fetcher):
         # Setup mock
        mock_fetcher = MagicMock()
        mock_get_fetcher.return_value = mock_fetcher

        # Mock search_players
        mock_fetcher.search_players.return_value = [{'id': 123, 'full_name': 'Test Player'}]

        # Mock get_player_stats with different date format (YYYY-MM-DD)
        mock_fetcher.get_player_stats.return_value = [
            {'GAME_DATE': '2024-10-25', 'MIN': 35.0}
        ]

        player_name = "Test Player"
        current_date = date(2024, 10, 26)

        minutes = await fetch_minutes_yesterday(player_name, current_date)

        assert minutes == 35.0

    @pytest.mark.asyncio
    @patch('src.services.player_minutes.get_player_fetcher')
    async def test_fetch_minutes_yesterday_with_datetime(self, mock_get_fetcher):
         # Setup mock
        mock_fetcher = MagicMock()
        mock_get_fetcher.return_value = mock_fetcher

        # Mock search_players
        mock_fetcher.search_players.return_value = [{'id': 123, 'full_name': 'Test Player'}]

        # Mock get_player_stats
        mock_fetcher.get_player_stats.return_value = [
            {'GAME_DATE': '2024-10-25T00:00:00', 'MIN': 30.5}
        ]

        player_name = "Test Player"
        # Passing datetime instead of date
        current_date = datetime(2024, 10, 26, 12, 0, 0)

        minutes = await fetch_minutes_yesterday(player_name, current_date)

        assert minutes == 30.5

if __name__ == "__main__":
    pytest.main([__file__])
