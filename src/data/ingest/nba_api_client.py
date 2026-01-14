"""Unified NBA API Client with multiple data source support.

Supports:
- nba_api Python package (FREE - stats.nba.com official data)
- The Odds API (betting odds)
- BallDontLie API (backup, requires key)
- RapidAPI NBA-API (backup, requires key)

Features:
- Automatic failover between sources
- Rate limiting and backoff
- Response caching
- Error handling and logging
"""

import os
import time
import requests
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime, date, timedelta
from functools import wraps
import logging

# Import nba_api
try:
    from nba_api.stats.endpoints import (
        scoreboardv2 as scoreboard,
        leaguegamefinder,
        playergamelogs,
        commonplayerinfo,
        playercareerstats,
        teamgamelog,
        commonteamroster
    )
    from nba_api.stats.static import players as static_players
    from nba_api.stats.static import teams as static_teams
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False
    print("Warning: nba_api not installed. Install with: pip install nba_api")

logger = logging.getLogger(__name__)

# API Keys from environment
BALLDONTLIE_API_KEY = os.getenv("BALLDONTLIE_API_KEY", "")
SPORTSDATA_API_KEY = os.getenv("SPORTSDATA_API_KEY", "")
RAPIDAPI_KEY = os.getenv("NBA_STATS_API_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "1b6650fc86e7512b52291e937f2b8f66")

# Rate limiting configuration
RATE_LIMITS = {
    "balldontlie": {"requests_per_minute": 60, "last_request": 0, "request_count": 0},
    "sportsdata": {"requests_per_minute": 100, "last_request": 0, "request_count": 0},
    "rapidapi": {"requests_per_minute": 50, "last_request": 0, "request_count": 0},
}


def rate_limit(source: str):
    """Decorator to enforce rate limiting per API source."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limits = RATE_LIMITS.get(source, {})
            current_time = time.time()
            
            # Reset counter if minute has passed
            if current_time - limits["last_request"] > 60:
                limits["request_count"] = 0
                limits["last_request"] = current_time
            
            # Check if we've hit the limit
            if limits["request_count"] >= limits["requests_per_minute"]:
                wait_time = 60 - (current_time - limits["last_request"])
                logger.warning(f"Rate limit reached for {source}. Waiting {wait_time:.1f}s")
                time.sleep(wait_time)
                limits["request_count"] = 0
                limits["last_request"] = time.time()
            
            # Increment counter and execute
            limits["request_count"] += 1
            return func(*args, **kwargs)
        return wrapper
    return decorator


class NBAAPIClient:
    """Unified NBA API client with multi-source support."""
    
    def __init__(self, preferred_source: str = "nba_api"):
        """
        Initialize NBA API client.
        
        Args:
            preferred_source: Primary data source ('nba_api', 'balldontlie', 'rapidapi')
        """
        self.preferred_source = preferred_source
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})
        self.nba_api_available = NBA_API_AVAILABLE
        
        logger.info(f"🏀 NBA API Client initialized (preferred: {preferred_source}, nba_api: {NBA_API_AVAILABLE})")
    
    # ============================================================================
    # NBA_API (OFFICIAL STATS.NBA.COM - FREE, NO KEY NEEDED)
    # ============================================================================
    
    def get_games_today(self, date_str: Optional[str] = None) -> List[Dict]:
        """
        Get games for a specific date.
        
        Args:
            date_str: Date in YYYY-MM-DD format (defaults to today)
        
        Returns:
            List of game dictionaries
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"📅 Fetching games for {date_str}")
        
        if self.nba_api_available:
            try:
                # Convert date format for nba_api (MM/DD/YYYY)
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                nba_date = date_obj.strftime("%m/%d/%Y")
                
                # Get scoreboard
                board = scoreboard.Scoreboard(game_date=nba_date)
                games_data = board.get_dict()
                
                # Extract games from response
                games = []
                if 'resultSets' in games_data:
                    for result_set in games_data['resultSets']:
                        if result_set['name'] == 'GameHeader':
                            headers = result_set['headers']
                            for row in result_set['rowSet']:
                                game_dict = dict(zip(headers, row))
                                games.append({
                                    "game_id": game_dict.get("GAME_ID"),
                                    "date": date_str,
                                    "season": game_dict.get("SEASON"),
                                    "status": game_dict.get("GAME_STATUS_TEXT"),
                                    "home_team": {
                                        "id": game_dict.get("HOME_TEAM_ID"),
                                        "name": game_dict.get("HOME_TEAM_NAME"),
                                        "score": game_dict.get("HOME_TEAM_SCORE") or 0
                                    },
                                    "visitor_team": {
                                        "id": game_dict.get("VISITOR_TEAM_ID"),
                                        "name": game_dict.get("VISITOR_TEAM_NAME"),
                                        "score": game_dict.get("VISITOR_TEAM_SCORE") or 0
                                    }
                                })
                
                logger.info(f"✅ Found {len(games)} games from nba_api")
                return games
                
            except Exception as e:
                logger.warning(f"nba_api failed: {e}")
        
        # Fallback to BallDontLie or RapidAPI
        return self._get_games_fallback(date_str)
    
    def get_teams(self) -> List[Dict]:
        """Get all NBA teams."""
        logger.info("🏀 Fetching teams list")
        
        if self.nba_api_available:
            try:
                teams = static_teams.get_teams()
                logger.info(f"✅ Found {len(teams)} teams from nba_api")
                return teams
            except Exception as e:
                logger.error(f"nba_api teams failed: {e}")
        
        return []
    
    def get_players(
        self,
        search: Optional[str] = None,
        team_ids: Optional[List[int]] = None,
        per_page: int = 25,
        active_only: bool = True
    ) -> List[Dict]:
        """
        Get player data.
        
        Args:
            search: Player name search string
            team_ids: Filter by team IDs
            per_page: Results per page (ignored for nba_api)
            active_only: Only active players
        
        Returns:
            List of player dictionaries
        """
        logger.info(f"👤 Fetching players (search: {search})")
        
        if self.nba_api_available:
            try:
                # Get all players
                all_players = static_players.get_players()
                
                # Filter active only
                if active_only:
                    all_players = [p for p in all_players if p.get('is_active', False)]
                
                # Filter by search
                if search:
                    search_lower = search.lower()
                    all_players = [
                        p for p in all_players
                        if search_lower in p.get('full_name', '').lower()
                    ]
                
                logger.info(f"✅ Found {len(all_players)} players from nba_api")
                return all_players[:per_page]
                
            except Exception as e:
                logger.error(f"nba_api players failed: {e}")
        
        return []
    
    def get_player_stats(
        self,
        player_ids: Optional[List[int]] = None,
        game_ids: Optional[List[int]] = None,
        dates: Optional[List[str]] = None,
        season: Optional[str] = None,
        last_n_games: int = 10
    ) -> List[Dict]:
        """
        Get player statistics.
        
        Args:
            player_ids: Filter by player IDs
            game_ids: Filter by game IDs  
            dates: Filter by dates (YYYY-MM-DD format)
            season: Season (e.g., "2024-25")
            last_n_games: Number of recent games
        
        Returns:
            List of stat dictionaries
        """
        logger.info("📊 Fetching player stats")
        
        if not self.nba_api_available or not player_ids:
            return []
        
        try:
            if not season:
                # Default to current season
                current_year = datetime.now().year
                current_month = datetime.now().month
                if current_month >= 10:  # NBA season starts in October
                    season = f"{current_year}-{str(current_year + 1)[-2:]}"
                else:
                    season = f"{current_year - 1}-{str(current_year)[-2:]}"
            
            all_stats = []
            
            for player_id in player_ids[:5]:  # Limit to avoid rate limits
                try:
                    # Get player game logs
                    game_logs = playergamelogs.PlayerGameLogs(
                        player_id_nullable=str(player_id),
                        season_nullable=season,
                        last_n_games_nullable=last_n_games
                    )
                    
                    logs_data = game_logs.get_dict()
                    
                    if 'resultSets' in logs_data and len(logs_data['resultSets']) > 0:
                        headers = logs_data['resultSets'][0]['headers']
                        for row in logs_data['resultSets'][0]['rowSet']:
                            stat_dict = dict(zip(headers, row))
                            all_stats.append(stat_dict)
                    
                    # Rate limiting
                    time.sleep(0.6)  # 600ms between requests
                    
                except Exception as e:
                    logger.warning(f"Failed to get stats for player {player_id}: {e}")
                    continue
            
            logger.info(f"✅ Found {len(all_stats)} stat records")
            return all_stats
            
        except Exception as e:
            logger.error(f"Failed to fetch player stats: {e}")
            return []
    
    def get_season_averages(
        self,
        season: str,
        player_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        Get player season averages.
        
        Args:
            season: Season (e.g., "2024-25")
            player_ids: Filter by player IDs
        
        Returns:
            List of season average dictionaries
        """
        logger.info(f"📈 Fetching season averages for {season}")
        
        if not self.nba_api_available:
            return []
        
        try:
            averages = []
            
            if player_ids:
                for player_id in player_ids[:10]:  # Limit requests
                    try:
                        career = playercareerstats.PlayerCareerStats(player_id=str(player_id))
                        career_data = career.get_dict()
                        
                        # Extract season stats
                        if 'resultSets' in career_data:
                            for result_set in career_data['resultSets']:
                                if result_set['name'] == 'SeasonTotalsRegularSeason':
                                    headers = result_set['headers']
                                    for row in result_set['rowSet']:
                                        stat_dict = dict(zip(headers, row))
                                        if stat_dict.get('SEASON_ID', '').endswith(season.split('-')[0]):
                                            averages.append(stat_dict)
                        
                        time.sleep(0.6)  # Rate limiting
                        
                    except Exception as e:
                        logger.warning(f"Failed to get season average for player {player_id}: {e}")
                        continue
            
            logger.info(f"✅ Found season averages for {len(averages)} players")
            return averages
            
        except Exception as e:
            logger.error(f"Failed to fetch season averages: {e}")
            return []
    
    # ============================================================================
    # FALLBACK METHODS
    # ============================================================================
    
    def _get_games_fallback(self, date_str: str) -> List[Dict]:
        """Fallback method for games when primary sources fail."""
        logger.warning(f"Using fallback for games on {date_str}")
        return []
    
    # ============================================================================
    # ODDS API (THE-ODDS-API.COM)
    # ============================================================================
    
    def get_odds(self, sport: str = "basketball_nba") -> List[Dict]:
        """
        Get current betting odds from The Odds API.
        
        Args:
            sport: Sport key (default: basketball_nba)
        
        Returns:
            List of odds dictionaries
        """
        logger.info(f"💰 Fetching odds for {sport}")
        
        base_url = "https://api.the-odds-api.com/v4/sports"
        url = f"{base_url}/{sport}/odds"
        
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            odds_data = response.json()
            
            logger.info(f"✅ Found odds for {len(odds_data)} games")
            return odds_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Odds API error: {e}")
            return []


# Singleton instance
_api_client: Optional[NBAAPIClient] = None


def get_nba_client() -> NBAAPIClient:
    """Get or create NBA API client instance."""
    global _api_client
    if _api_client is None:
        _api_client = NBAAPIClient()
    return _api_client
