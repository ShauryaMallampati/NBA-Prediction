"""Fetch player data with smart caching.

We grab:
- Player profiles and basic info
- Season stats and averages
- Recent game performance
- Career statistics
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


class PlayerFetcher:
    """Grab player data and cache it so we're not fetching repeatedly."""
    
    def __init__(self):
        """Set up the player data fetcher."""
        self.client = get_nba_client()
        self.cache = get_cache_manager()
        logger.info("👤 Player fetcher initialized")
    
    @cached(cache_type="players_list", ttl=86400)  # 24 hours
    def get_all_players(self, per_page: int = 100) -> List[Dict]:
        """
        Get all NBA players.
        
        Args:
            per_page: Results per page
        
        Returns:
            List of player dictionaries
        """
        logger.info("👥 Fetching all players")
        
        players = self.client.get_players(per_page=per_page)
        logger.info(f"✅ Found {len(players)} players")
        
        return players
    
    @cached(cache_type="players_list", ttl=3600)  # 1 hour
    def search_players(self, name: str) -> List[Dict]:
        """
        Search for players by name.
        
        Args:
            name: Player name search string
        
        Returns:
            List of matching players
        """
        logger.info(f"🔍 Searching for player: {name}")
        
        players = self.client.get_players(search=name)
        logger.info(f"✅ Found {len(players)} players matching '{name}'")
        
        return players
    
    @cached(cache_type="player_stats", ttl=3600)  # 1 hour
    def get_player_stats(
        self,
        player_id: int,
        season: Optional[int] = None,
        last_n_games: Optional[int] = None
    ) -> List[Dict]:
        """
        Get statistics for a specific player.
        
        Args:
            player_id: Player ID
            season: Season year (e.g., 2024)
            last_n_games: Limit to last N games
        
        Returns:
            List of stat dictionaries
        """
        logger.info(f"📊 Fetching stats for player {player_id}")
        
        params = {"player_ids": [player_id]}
        if season:
            params["season"] = season
        
        stats = self.client.get_player_stats(**params)
        
        # Sort by date descending and limit if requested
        if stats:
            stats.sort(key=lambda x: x.get("game", {}).get("date", ""), reverse=True)
            if last_n_games:
                stats = stats[:last_n_games]
        
        logger.info(f"✅ Found {len(stats)} stat records")
        return stats
    
    @cached(cache_type="season_averages", ttl=86400)  # 24 hours
    def get_season_averages(
        self,
        season: int,
        player_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Get season averages for players.
        
        Args:
            season: Season year
            player_ids: Specific player IDs (None for all)
        
        Returns:
            List of season average dictionaries
        """
        logger.info(f"📈 Fetching season averages for {season}")
        
        averages = self.client.get_season_averages(season, player_ids)
        logger.info(f"✅ Found season averages for {len(averages)} players")
        
        return averages
    
    def get_recent_performance(self, player_id: int, games: int = 5) -> Dict:
        """
        Get recent performance summary for a player.
        
        Args:
            player_id: Player ID
            games: Number of recent games
        
        Returns:
            Performance summary with averages
        """
        logger.info(f"📊 Calculating recent performance for player {player_id} (L{games})")
        
        stats = self.get_player_stats(player_id, last_n_games=games)
        
        if not stats:
            logger.warning(f"No stats found for player {player_id}")
            return {}
        
        # Calculate averages
        totals = {
            "points": 0,
            "assists": 0,
            "rebounds": 0,
            "steals": 0,
            "blocks": 0,
            "turnovers": 0,
            "fg_pct": 0,
            "fg3_pct": 0,
            "ft_pct": 0,
            "minutes": 0
        }
        
        games_played = len(stats)
        
        for stat in stats:
            # nba_api returns uppercase field names
            totals["points"] += stat.get("PTS", 0) or 0
            totals["assists"] += stat.get("AST", 0) or 0
            totals["rebounds"] += stat.get("REB", 0) or 0
            totals["steals"] += stat.get("STL", 0) or 0
            totals["blocks"] += stat.get("BLK", 0) or 0
            totals["turnovers"] += stat.get("TOV", 0) or 0
            totals["fg_pct"] += stat.get("FG_PCT", 0) or 0
            totals["fg3_pct"] += stat.get("FG3_PCT", 0) or 0
            totals["ft_pct"] += stat.get("FT_PCT", 0) or 0
            totals["minutes"] += stat.get("MIN", 0) or 0
        
        # Calculate averages
        averages = {
            "player_id": player_id,
            "games_analyzed": games_played,
            "ppg": round(totals["points"] / games_played, 1),
            "apg": round(totals["assists"] / games_played, 1),
            "rpg": round(totals["rebounds"] / games_played, 1),
            "spg": round(totals["steals"] / games_played, 1),
            "bpg": round(totals["blocks"] / games_played, 1),
            "tpg": round(totals["turnovers"] / games_played, 1),
            "fg_pct": round(totals["fg_pct"] / games_played * 100, 1),
            "fg3_pct": round(totals["fg3_pct"] / games_played * 100, 1),
            "ft_pct": round(totals["ft_pct"] / games_played * 100, 1),
            "mpg": round(totals["minutes"] / games_played, 1)
        }
        
        logger.info(f"✅ Performance: {averages['ppg']} PPG, {averages['apg']} APG, {averages['rpg']} RPG")
        return averages
    
    def get_player_by_team(self, team_id: int) -> List[Dict]:
        """
        Get all players for a specific team.
        
        Args:
            team_id: Team ID
        
        Returns:
            List of player dictionaries
        """
        logger.info(f"🏀 Fetching players for team {team_id}")
        
        players = self.client.get_players(team_ids=[team_id])
        logger.info(f"✅ Found {len(players)} players")
        
        return players
    
    def save_players_to_file(self, players: List[Dict], filename: str):
        """
        Save players to JSON file.
        
        Args:
            players: List of player dictionaries
            filename: Output filename
        """
        import json
        
        output_path = RAW_DIR / filename
        output_path.write_text(json.dumps(players, indent=2))
        logger.info(f"💾 Saved {len(players)} players to {output_path}")


# Singleton instance
_player_fetcher: Optional[PlayerFetcher] = None


def get_player_fetcher() -> PlayerFetcher:
    """Get or create player fetcher instance."""
    global _player_fetcher
    if _player_fetcher is None:
        _player_fetcher = PlayerFetcher()
    return _player_fetcher
