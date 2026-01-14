
import logging
import asyncio
from datetime import date, timedelta, datetime
from typing import Optional, Union
from src.data.ingest.player_fetcher import get_player_fetcher

logger = logging.getLogger(__name__)

def _fetch_minutes_sync(player_name: str, current_date: date) -> float:
    """Synchronous implementation of minutes fetching."""
    try:
        # Ensure current_date is a date object
        if isinstance(current_date, datetime):
            current_date = current_date.date()

        yesterday = current_date - timedelta(days=1)

        fetcher = get_player_fetcher()

        # 1. Find player
        players = fetcher.search_players(player_name)
        if not players:
            logger.warning(f"Player {player_name} not found when fetching yesterday's minutes")
            return 0.0

        # Use the first match (usually the most relevant one)
        player_id = players[0]['id']

        # 2. Get recent stats (last 5 games should be enough to cover yesterday)
        stats = fetcher.get_player_stats(player_id, last_n_games=5)

        if not stats:
            return 0.0

        # 3. Check for game on yesterday
        for game in stats:
            # game['GAME_DATE'] is like '2026-01-13T00:00:00' or maybe 'YYYY-MM-DD' depending on endpoint
            game_date_str = game.get('GAME_DATE', '')
            if not game_date_str:
                continue

            # Handle different formats if necessary. ISO format usually.
            try:
                if 'T' in game_date_str:
                    game_date_dt = datetime.fromisoformat(game_date_str).date()
                else:
                    game_date_dt = datetime.strptime(game_date_str, "%Y-%m-%d").date()
            except ValueError:
                logger.warning(f"Could not parse game date: {game_date_str}")
                continue

            if game_date_dt == yesterday:
                minutes = game.get('MIN', 0.0)
                return float(minutes)

        return 0.0

    except Exception as e:
        logger.error(f"Error fetching minutes yesterday for {player_name}: {e}")
        return 0.0

async def fetch_minutes_yesterday(player_name: str, current_date: Union[date, datetime]) -> float:
    """
    Fetch minutes played by a player on the day before the current_date.
    Non-blocking async wrapper around the synchronous NBA API calls.

    Args:
        player_name: Name of the player.
        current_date: The date of the game we are predicting for.

    Returns:
        Minutes played yesterday (float), or 0.0 if no game/not found.
    """
    return await asyncio.to_thread(_fetch_minutes_sync, player_name, current_date)
