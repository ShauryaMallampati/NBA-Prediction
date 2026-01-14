
import logging
from datetime import datetime, timedelta, date
from typing import Optional, Union

from src.data.ingest.game_fetcher import get_game_fetcher

logger = logging.getLogger(__name__)

def is_team_back_to_back(team_id: int, game_date: Union[date, str]) -> bool:
    """
    Check if a team played on the day before the game_date.

    Args:
        team_id: NBA Team ID
        game_date: Date of the current game (date object or YYYY-MM-DD string)

    Returns:
        True if the team played the day before, False otherwise.
    """
    if isinstance(game_date, str):
        current_date = datetime.strptime(game_date, "%Y-%m-%d").date()
    else:
        current_date = game_date

    yesterday = current_date - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")

    # Use GameFetcher which has caching
    fetcher = get_game_fetcher()
    games_yesterday = fetcher.get_games_by_date(yesterday_str)

    for game in games_yesterday:
        try:
            home_id = game.get("home_team", {}).get("id")
            visitor_id = game.get("visitor_team", {}).get("id")

            if home_id == team_id or visitor_id == team_id:
                return True
        except (AttributeError, KeyError):
            continue

    return False
