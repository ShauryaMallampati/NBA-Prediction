"""
Lineup Fetcher using nba_api (FREE, no API key needed)

Fetches:
- Starting lineups
- Player rotations
- Lineup performance metrics
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Import NBA API
try:
    from nba_api.stats.endpoints import commonteamroster, boxscoretraditionalv2
    from nba_api.stats.static import teams as static_teams
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False
    logging.warning("nba_api not available. Install with: pip install nba-api")

from .nba_api_client import get_nba_client
from .cache_manager import get_cache_manager, cached

logger = logging.getLogger(__name__)


class LineupFetcher:
    """Fetch NBA lineups and rotations."""
    
    def __init__(self):
        """Initialize lineup fetcher."""
        self.client = get_nba_client()
        self.cache = get_cache_manager()
        self.nba_api_available = NBA_API_AVAILABLE
        logger.info("👥 Lineup fetcher initialized")
    
    @cached(cache_type="lineups", ttl=3600)  # 1 hour cache
    def get_team_roster(self, team_id: int, season: Optional[str] = None) -> List[Dict]:
        """
        Get team roster.
        
        Args:
            team_id: Team ID
            season: Season (e.g., "2023-24")
        
        Returns:
            List of player dictionaries
        """
        if not season:
            # Get current season
            current_year = datetime.now().year
            current_month = datetime.now().month
            if current_month >= 10:  # October or later
                season = f"{current_year}-{str(current_year + 1)[-2:]}"
            else:
                season = f"{current_year - 1}-{str(current_year)[-2:]}"
        
        logger.info(f"👥 Fetching roster for team {team_id} ({season})")
        
        if not self.nba_api_available:
            logger.warning("nba_api not available, returning empty roster")
            return []
        
        try:
            roster = commonteamroster.CommonTeamRoster(team_id=team_id, season=season)
            roster_data = roster.get_dict()
            
            players = []
            if 'resultSets' in roster_data:
                for result_set in roster_data['resultSets']:
                    if result_set['name'] == 'CommonTeamRoster':
                        headers = result_set['headers']
                        for row in result_set['rowSet']:
                            player_dict = dict(zip(headers, row))
                            players.append({
                                'player_id': player_dict.get('PLAYER_ID'),
                                'player_name': player_dict.get('PLAYER'),
                                'position': player_dict.get('POSITION'),
                                'height': player_dict.get('HEIGHT'),
                                'weight': player_dict.get('WEIGHT'),
                                'age': player_dict.get('AGE'),
                            })
            
            logger.info(f"✅ Found {len(players)} players on roster")
            return players
            
        except Exception as e:
            logger.error(f"Error fetching roster: {e}")
            return []
    
    def get_starting_lineup(self, game_id: str) -> Dict:
        """
        Get starting lineup for a game.
        
        Args:
            game_id: Game ID
        
        Returns:
            Dictionary with home and away starting lineups
        """
        logger.info(f"👥 Fetching starting lineup for game {game_id}")
        
        if not self.nba_api_available:
            logger.warning("nba_api not available, returning empty lineup")
            return {
                'home_lineup': [],
                'away_lineup': [],
            }
        
        try:
            # Get box score (contains starting lineup information)
            boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
            boxscore_data = boxscore.get_dict()
            
            # Extract starting lineups
            home_lineup = []
            away_lineup = []
            
            if 'resultSets' in boxscore_data:
                for result_set in boxscore_data['resultSets']:
                    if result_set['name'] == 'PlayerStats':
                        headers = result_set['headers']
                        for row in result_set['rowSet']:
                            player_dict = dict(zip(headers, row))
                            # Starting players have START_POSITION != ''
                            if player_dict.get('START_POSITION'):
                                player_info = {
                                    'player_id': player_dict.get('PLAYER_ID'),
                                    'player_name': player_dict.get('PLAYER_NAME'),
                                    'position': player_dict.get('START_POSITION'),
                                    'team_id': player_dict.get('TEAM_ID'),
                                }
                                
                                # Determine if home or away (need game context)
                                # For now, add to both (will be filtered later)
                                home_lineup.append(player_info)
                                away_lineup.append(player_info)
            
            logger.info(f"✅ Found {len(home_lineup)} home starters, {len(away_lineup)} away starters")
            return {
                'home_lineup': home_lineup[:5],  # Starting 5
                'away_lineup': away_lineup[:5],  # Starting 5
            }
            
        except Exception as e:
            logger.error(f"Error fetching starting lineup: {e}")
            return {
                'home_lineup': [],
                'away_lineup': [],
            }
    
    def get_lineup_strength(self, lineup: List[Dict]) -> float:
        """
        Calculate lineup strength score (0-1).
        
        Args:
            lineup: List of player dictionaries
        
        Returns:
            Lineup strength score (0-1)
        """
        if len(lineup) == 0:
            return 0.5  # Average
        
        # For now, return average strength
        # This can be enhanced with player ratings/statistics
        return 0.75  # Placeholder


# Singleton instance
_lineup_fetcher: Optional[LineupFetcher] = None


def get_lineup_fetcher() -> LineupFetcher:
    """Get or create lineup fetcher instance."""
    global _lineup_fetcher
    if _lineup_fetcher is None:
        _lineup_fetcher = LineupFetcher()
    return _lineup_fetcher


if __name__ == "__main__":
    # Example usage
    fetcher = get_lineup_fetcher()
    
    # Get team roster
    # roster = fetcher.get_team_roster(team_id=1610612744)  # Warriors
    # print(f"Team roster: {len(roster)} players")
    
    # Get starting lineup
    # lineup = fetcher.get_starting_lineup(game_id="0022400001")
    # print(f"Starting lineups: {lineup}")

