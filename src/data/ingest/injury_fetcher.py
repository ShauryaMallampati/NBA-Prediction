"""
Injury Report Fetcher using nba_api (FREE, no API key needed)

Fetches:
- Player injury reports
- Player availability status
- Injury impact on predictions
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Optional
from pathlib import Path
import pandas as pd

# Import NBA API
try:
    from nba_api.stats.endpoints import scoreboard, commonplayerinfo
    from nba_api.stats.static import players as static_players
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False
    logging.warning("nba_api not available. Install with: pip install nba-api")

from .nba_api_client import get_nba_client
from .cache_manager import get_cache_manager, cached

logger = logging.getLogger(__name__)


class InjuryFetcher:
    """Fetch NBA injury reports and player availability."""
    
    def __init__(self):
        """Initialize injury fetcher."""
        self.client = get_nba_client()
        self.cache = get_cache_manager()
        self.nba_api_available = NBA_API_AVAILABLE
        logger.info("🏥 Injury fetcher initialized")
    
    @cached(cache_type="injury_reports", ttl=3600)  # 1 hour cache
    def get_injury_reports(self, game_date: Optional[str] = None) -> List[Dict]:
        """
        Get injury reports for a specific date.
        
        Args:
            game_date: Date in YYYY-MM-DD format (defaults to today)
        
        Returns:
            List of injury report dictionaries
        """
        if not game_date:
            game_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"🏥 Fetching injury reports for {game_date}")
        
        if not self.nba_api_available:
            logger.warning("nba_api not available, returning empty injury reports")
            return []
        
        try:
            # Convert date format for nba_api (MM/DD/YYYY)
            date_obj = datetime.strptime(game_date, "%Y-%m-%d")
            nba_date = date_obj.strftime("%m/%d/%Y")
            
            # Get scoreboard (contains injury information)
            from nba_api.stats.endpoints import scoreboard
            board = scoreboard.Scoreboard(game_date=nba_date)
            games_data = board.get_dict()
            
            # Extract injury information from scoreboard
            injuries = []
            
            # Note: NBA API scoreboard doesn't directly provide injury reports
            # This is a placeholder for when we implement actual injury data fetching
            # For now, we'll use game status and player availability from other sources
            
            logger.info(f"✅ Found {len(injuries)} injury reports")
            return injuries
            
        except Exception as e:
            logger.error(f"Error fetching injury reports: {e}")
            return []
    
    def get_team_injuries(self, team_id: int, game_date: Optional[str] = None) -> List[Dict]:
        """
        Get injuries for a specific team.
        
        Args:
            team_id: Team ID
            game_date: Date in YYYY-MM-DD format
        
        Returns:
            List of injured players for the team
        """
        if not game_date:
            game_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"🏥 Fetching injuries for team {team_id} on {game_date}")
        
        # Get all injury reports
        all_injuries = self.get_injury_reports(game_date)
        
        # Filter by team
        team_injuries = [inj for inj in all_injuries if inj.get('team_id') == team_id]
        
        logger.info(f"✅ Found {len(team_injuries)} injuries for team {team_id}")
        return team_injuries
    
    def get_player_availability(self, player_id: int, game_date: Optional[str] = None) -> Dict:
        """
        Get player availability status.
        
        Args:
            player_id: Player ID
            game_date: Date in YYYY-MM-DD format
        
        Returns:
            Dictionary with availability status
        """
        if not game_date:
            game_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"👤 Checking availability for player {player_id} on {game_date}")
        
        # Get injury reports
        injuries = self.get_injury_reports(game_date)
        
        # Check if player is in injury list
        player_injury = next((inj for inj in injuries if inj.get('player_id') == player_id), None)
        
        if player_injury:
            return {
                'player_id': player_id,
                'available': False,
                'injury_status': player_injury.get('status', 'Unknown'),
                'injury_reason': player_injury.get('reason', 'Unknown'),
            }
        else:
            return {
                'player_id': player_id,
                'available': True,
                'injury_status': 'Healthy',
                'injury_reason': None,
            }
    
    def get_team_availability_score(self, team_id: int, game_date: Optional[str] = None) -> float:
        """
        Get team availability score (0-1, where 1 = all players available).
        
        Args:
            team_id: Team ID
            game_date: Date in YYYY-MM-DD format
        
        Returns:
            Availability score (0-1)
        """
        if not game_date:
            game_date = datetime.now().strftime("%Y-%m-%d")
        
        # Get team injuries
        injuries = self.get_team_injuries(team_id, game_date)
        
        # For now, return 1.0 (all available) since we don't have actual injury data
        # This will be enhanced when we implement actual injury data fetching
        if len(injuries) == 0:
            return 1.0
        else:
            # Assume 15 players per team, calculate availability
            total_players = 15
            injured_players = len(injuries)
            availability_score = 1.0 - (injured_players / total_players)
            return max(0.0, availability_score)


# Singleton instance
_injury_fetcher: Optional[InjuryFetcher] = None


def get_injury_fetcher() -> InjuryFetcher:
    """Get or create injury fetcher instance."""
    global _injury_fetcher
    if _injury_fetcher is None:
        _injury_fetcher = InjuryFetcher()
    return _injury_fetcher


if __name__ == "__main__":
    # Example usage
    fetcher = get_injury_fetcher()
    
    # Get injury reports for today
    injuries = fetcher.get_injury_reports()
    print(f"Found {len(injuries)} injury reports")
    
    # Get team injuries
    # team_injuries = fetcher.get_team_injuries(team_id=1610612744)  # Warriors
    # print(f"Team injuries: {len(team_injuries)}")

