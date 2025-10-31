"""Game data fetcher with caching and scheduling.

Fetches:
- Today's games
- Live scores
- Game details
- Historical games
- Season schedule
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from .nba_api_client import get_nba_client
from .cache_manager import get_cache_manager, cached

logger = logging.getLogger(__name__)

# Data storage paths
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


class GameFetcher:
    """Fetch NBA game data with caching."""
    
    def __init__(self):
        """Initialize game fetcher."""
        self.client = get_nba_client()
        self.cache = get_cache_manager()
        logger.info("🏀 Game fetcher initialized")
    
    @cached(cache_type="live_scores", ttl=300)  # 5 minutes
    def get_today_games(self) -> List[Dict]:
        """
        Get today's NBA games.
        
        Returns:
            List of game dictionaries with scores and status
        """
        logger.info("📅 Fetching today's games")
        today = datetime.now().strftime("%Y-%m-%d")
        
        games = self.client.get_games_today(today)
        logger.info(f"✅ Found {len(games)} games today")
        
        return games
    
    @cached(cache_type="live_scores", ttl=180)  # 3 minutes
    def get_live_scores(self) -> List[Dict]:
        """
        Get live game scores for games in progress.
        
        Returns:
            List of live game dictionaries
        """
        logger.info("⚡ Fetching live scores")
        
        today_games = self.get_today_games()
        
        # Filter for live games (status contains "in progress" or similar)
        live_games = [
            game for game in today_games
            if game.get("status", "").lower() in ["live", "in progress", "halftime", "q1", "q2", "q3", "q4"]
        ]
        
        logger.info(f"⚡ {len(live_games)} games live right now")
        return live_games
    
    @cached(cache_type="historical_games", ttl=86400)  # 24 hours
    def get_games_by_date(self, date_str: str) -> List[Dict]:
        """
        Get games for a specific date.
        
        Args:
            date_str: Date in YYYY-MM-DD format
        
        Returns:
            List of game dictionaries
        """
        logger.info(f"📅 Fetching games for {date_str}")
        
        games = self.client.get_games_today(date_str)
        logger.info(f"✅ Found {len(games)} games on {date_str}")
        
        return games
    
    def get_games_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Get games across a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            List of all games in the range
        """
        logger.info(f"📅 Fetching games from {start_date} to {end_date}")
        
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        all_games = []
        current = start
        
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            games = self.get_games_by_date(date_str)
            all_games.extend(games)
            current += timedelta(days=1)
        
        logger.info(f"✅ Fetched {len(all_games)} total games")
        return all_games
    
    def get_upcoming_games(self, days: int = 7) -> List[Dict]:
        """
        Get upcoming games for the next N days.
        
        Args:
            days: Number of days ahead to fetch
        
        Returns:
            List of upcoming games
        """
        logger.info(f"🔮 Fetching games for next {days} days")
        
        today = datetime.now()
        future = today + timedelta(days=days)
        
        return self.get_games_date_range(
            today.strftime("%Y-%m-%d"),
            future.strftime("%Y-%m-%d")
        )
    
    def get_recent_games(self, days: int = 7) -> List[Dict]:
        """
        Get recent games from the past N days.
        
        Args:
            days: Number of days back to fetch
        
        Returns:
            List of recent games
        """
        logger.info(f"📜 Fetching games from past {days} days")
        
        today = datetime.now()
        past = today - timedelta(days=days)
        
        return self.get_games_date_range(
            past.strftime("%Y-%m-%d"),
            today.strftime("%Y-%m-%d")
        )
    
    def save_games_to_file(self, games: List[Dict], filename: str):
        """
        Save games to JSON file.
        
        Args:
            games: List of game dictionaries
            filename: Output filename
        """
        import json
        
        output_path = RAW_DIR / filename
        output_path.write_text(json.dumps(games, indent=2))
        logger.info(f"💾 Saved {len(games)} games to {output_path}")


# Singleton instance
_game_fetcher: Optional[GameFetcher] = None


def get_game_fetcher() -> GameFetcher:
    """Get or create game fetcher instance."""
    global _game_fetcher
    if _game_fetcher is None:
        _game_fetcher = GameFetcher()
    return _game_fetcher
