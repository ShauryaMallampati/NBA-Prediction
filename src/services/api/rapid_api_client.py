"""
Comprehensive RapidAPI NBA Data Client
Integrates all NBA-related APIs from RapidAPI for data collection and training
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.common.config import settings

logger = logging.getLogger(__name__)


class RapidAPIClient:
    """Unified client for all NBA RapidAPI endpoints"""
    
    BASE_HEADERS = {
        "X-RapidAPI-Key": settings.nba_stats_api_key,
    }
    
    # API Hosts configuration
    API_HOSTS = {
        "nba_free_data": "nba-api-free-data.p.rapidapi.com",
        "player_props": "nba-player-props-odds.p.rapidapi.com",
        "injury_data": "nba-injury-data.p.rapidapi.com",
        "live_odds": "odds.p.rapidapi.com",
        "nba_schedule": "nba-schedule.p.rapidapi.com",
        "daily_leaders": "nba-daily-leaders.p.rapidapi.com",
        "latest_news": "nba-latest-news.p.rapidapi.com",
        "free_nba": "free-nba.p.rapidapi.com",
        "nba_stats_api": "nba-stats-api1.p.rapidapi.com",
        "nba_results_pro": "nba-results-pro.p.rapidapi.com",
        "fantasy_sports": "fantasy-sports.p.rapidapi.com",
        "basketball_data": "basketball-data.p.rapidapi.com",
        "nba_backtest": "nba-backtest.p.rapidapi.com",
        "sports_odds_api": "sports-odds-api.p.rapidapi.com",
    }
    
    def __init__(self):
        """Initialize the RapidAPI client with retry logic"""
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def _make_request(
        self,
        host: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET"
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request to RapidAPI"""
        headers = self.BASE_HEADERS.copy()
        headers["X-RapidAPI-Host"] = host
        
        url = f"https://{host}/{endpoint}"
        
        try:
            logger.info(f"Requesting {url} with params: {params}")
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
    
    # ==================== NBA API Free Data ====================
    
    def get_nba_league_info(self) -> Optional[Dict[str, Any]]:
        """Get NBA league information"""
        return self._make_request(
            self.API_HOSTS["nba_free_data"],
            "nba-league-info"
        )
    
    def get_nba_sport_info(self) -> Optional[Dict[str, Any]]:
        """Get NBA sport information"""
        return self._make_request(
            self.API_HOSTS["nba_free_data"],
            "nba-sport-info"
        )
    
    def get_nba_teams(self) -> Optional[Dict[str, Any]]:
        """Get all NBA teams"""
        return self._make_request(
            self.API_HOSTS["nba_free_data"],
            "nba-teams"
        )
    
    def get_nba_scoreboard(self, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get NBA scoreboard for a specific date"""
        params = {}
        if date:
            params["date"] = date
        return self._make_request(
            self.API_HOSTS["nba_free_data"],
            "nba-scoreboard",
            params
        )
    
    def get_nba_schedule(self, season: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get NBA schedule"""
        params = {}
        if season:
            params["season"] = season
        return self._make_request(
            self.API_HOSTS["nba_free_data"],
            "nba-schedule",
            params
        )
    
    def get_nba_standings(self, season: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get NBA standings"""
        params = {}
        if season:
            params["season"] = season
        return self._make_request(
            self.API_HOSTS["nba_free_data"],
            "nba-standings",
            params
        )
    
    def get_nba_players(self, team_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get NBA players"""
        params = {}
        if team_id:
            params["teamId"] = team_id
        return self._make_request(
            self.API_HOSTS["nba_free_data"],
            "nba-players",
            params
        )
    
    def get_nba_statistics(
        self,
        season: Optional[str] = None,
        player_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get NBA statistics"""
        params = {}
        if season:
            params["season"] = season
        if player_id:
            params["playerId"] = player_id
        return self._make_request(
            self.API_HOSTS["nba_free_data"],
            "nba-statistics",
            params
        )
    
    # ==================== NBA Player Props Odds ====================
    
    def get_player_odds_for_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get player prop odds for a specific event"""
        return self._make_request(
            self.API_HOSTS["player_props"],
            f"get-player-odds/{event_id}"
        )
    
    def get_events_for_today(self) -> Optional[Dict[str, Any]]:
        """Get NBA events for today"""
        return self._make_request(
            self.API_HOSTS["player_props"],
            "get-events-today"
        )
    
    def get_all_markets(self) -> Optional[Dict[str, Any]]:
        """Get all betting markets"""
        return self._make_request(
            self.API_HOSTS["player_props"],
            "get-all-markets"
        )
    
    def get_all_bookies(self) -> Optional[Dict[str, Any]]:
        """Get all bookmakers"""
        return self._make_request(
            self.API_HOSTS["player_props"],
            "get-all-bookies"
        )
    
    # ==================== NBA Injury Data ====================
    
    def get_injury_reports(self, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get NBA injury reports for a specific date (YYYY-MM-DD)"""
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        return self._make_request(
            self.API_HOSTS["injury_data"],
            f"injuries/nba/{date}"
        )
    
    # ==================== Live Sports Odds ====================
    
    def get_sports_list(self) -> Optional[Dict[str, Any]]:
        """Get list of available sports"""
        return self._make_request(
            self.API_HOSTS["live_odds"],
            "v4/sports"
        )
    
    def get_nba_odds(
        self,
        regions: str = "us",
        markets: str = "h2h,spreads,totals",
        odds_format: str = "american"
    ) -> Optional[Dict[str, Any]]:
        """Get NBA betting odds"""
        params = {
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format
        }
        return self._make_request(
            self.API_HOSTS["live_odds"],
            "v4/sports/basketball_nba/odds",
            params
        )
    
    def get_nba_scores(self, days_from: int = 3) -> Optional[Dict[str, Any]]:
        """Get NBA scores"""
        params = {"daysFrom": days_from}
        return self._make_request(
            self.API_HOSTS["live_odds"],
            "v4/sports/basketball_nba/scores",
            params
        )
    
    # ==================== NBA Schedule API ====================
    
    def get_schedule_data(
        self,
        season: Optional[str] = None,
        team: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get NBA schedule data"""
        params = {}
        if season:
            params["season"] = season
        if team:
            params["team"] = team
        return self._make_request(
            self.API_HOSTS["nba_schedule"],
            "schedule",
            params
        )
    
    # ==================== NBA Daily Leaders ====================
    
    def get_daily_leaders(self, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get NBA daily statistical leaders"""
        params = {}
        if date:
            params["date"] = date
        return self._make_request(
            self.API_HOSTS["daily_leaders"],
            "stats",
            params
        )
    
    # ==================== NBA Latest News ====================
    
    def get_latest_news(
        self,
        source: Optional[str] = None,
        team: Optional[str] = None,
        player: Optional[str] = None,
        limit: int = 10
    ) -> Optional[Dict[str, Any]]:
        """Get latest NBA news articles"""
        params = {"limit": limit}
        if source:
            params["source"] = source  # nba, espn, bleacher-report, yahoo, slam
        if team:
            params["team"] = team
        if player:
            params["player"] = player
        return self._make_request(
            self.API_HOSTS["latest_news"],
            "articles",
            params
        )
    
    # ==================== Free NBA API ====================
    
    def get_all_players(
        self,
        page: int = 1,
        per_page: int = 25,
        search: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get all NBA players"""
        params = {"page": page, "per_page": per_page}
        if search:
            params["search"] = search
        return self._make_request(
            self.API_HOSTS["free_nba"],
            "api/v1/players",
            params
        )
    
    def get_player_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """Get specific player by ID"""
        return self._make_request(
            self.API_HOSTS["free_nba"],
            f"api/v1/players/{player_id}"
        )
    
    def get_all_teams(
        self,
        page: int = 1,
        per_page: int = 30
    ) -> Optional[Dict[str, Any]]:
        """Get all NBA teams"""
        params = {"page": page, "per_page": per_page}
        return self._make_request(
            self.API_HOSTS["free_nba"],
            "api/v1/teams",
            params
        )
    
    def get_team_by_id(self, team_id: int) -> Optional[Dict[str, Any]]:
        """Get specific team by ID"""
        return self._make_request(
            self.API_HOSTS["free_nba"],
            f"api/v1/teams/{team_id}"
        )
    
    def get_all_games(
        self,
        page: int = 1,
        per_page: int = 25,
        seasons: Optional[List[int]] = None,
        team_ids: Optional[List[int]] = None,
        dates: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get all NBA games"""
        params = {"page": page, "per_page": per_page}
        if seasons:
            params["seasons[]"] = seasons
        if team_ids:
            params["team_ids[]"] = team_ids
        if dates:
            params["dates[]"] = dates
        return self._make_request(
            self.API_HOSTS["free_nba"],
            "api/v1/games",
            params
        )
    
    def get_game_by_id(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Get specific game by ID"""
        return self._make_request(
            self.API_HOSTS["free_nba"],
            f"api/v1/games/{game_id}"
        )
    
    def get_all_stats(
        self,
        page: int = 1,
        per_page: int = 25,
        seasons: Optional[List[int]] = None,
        player_ids: Optional[List[int]] = None,
        game_ids: Optional[List[int]] = None,
        dates: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get all NBA stats"""
        params = {"page": page, "per_page": per_page}
        if seasons:
            params["seasons[]"] = seasons
        if player_ids:
            params["player_ids[]"] = player_ids
        if game_ids:
            params["game_ids[]"] = game_ids
        if dates:
            params["dates[]"] = dates
        return self._make_request(
            self.API_HOSTS["free_nba"],
            "api/v1/stats",
            params
        )
    
    # ==================== NBA Results Pro ====================
    
    def get_teams_info(self) -> Optional[Dict[str, Any]]:
        """Get teams information"""
        return self._make_request(
            self.API_HOSTS["nba_results_pro"],
            "v1/teams"
        )
    
    def get_team_roster(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Get team roster by team ID"""
        return self._make_request(
            self.API_HOSTS["nba_results_pro"],
            f"v1/teams/{team_id}/roster"
        )
    
    def get_team_season_info(self, team_id: str, season: str) -> Optional[Dict[str, Any]]:
        """Get team information for a specific season"""
        return self._make_request(
            self.API_HOSTS["nba_results_pro"],
            f"v1/teams/{team_id}/season/{season}"
        )
    
    def get_games_info(
        self,
        date: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get games information"""
        params = {}
        if date:
            params["date"] = date
        if team_id:
            params["teamId"] = team_id
        return self._make_request(
            self.API_HOSTS["nba_results_pro"],
            "v1/games",
            params
        )
    
    def get_player_info(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get player information"""
        return self._make_request(
            self.API_HOSTS["nba_results_pro"],
            f"v1/players/{player_id}"
        )
    
    def get_league_leaders(self, season: str, stat_type: str) -> Optional[Dict[str, Any]]:
        """Get league leaders for a specific stat"""
        return self._make_request(
            self.API_HOSTS["nba_results_pro"],
            f"v1/league/leaders/{season}/{stat_type}"
        )
    
    # ==================== Fantasy Sports ====================
    
    def get_nba_fantasy_rest_of_season(self, position: str) -> Optional[Dict[str, Any]]:
        """Get NBA fantasy projections for rest of season by position"""
        return self._make_request(
            self.API_HOSTS["fantasy_sports"],
            f"v1/nba/rest-of-season/{position}"
        )
    
    def get_nba_fantasy_current_week(self, position: str) -> Optional[Dict[str, Any]]:
        """Get NBA fantasy projections for current week by position"""
        return self._make_request(
            self.API_HOSTS["fantasy_sports"],
            f"v1/nba/current-week/{position}"
        )
    
    # ==================== Basketball Data ====================
    
    def get_games_list(
        self,
        season: str,
        team: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get list of basketball games"""
        params = {"season": season}
        if team:
            params["team"] = team
        return self._make_request(
            self.API_HOSTS["basketball_data"],
            "v1/games/list",
            params
        )
    
    def get_game_box_scores(self, team: str, date: str) -> Optional[Dict[str, Any]]:
        """Get box scores for a specific game"""
        params = {"team": team, "date": date}
        return self._make_request(
            self.API_HOSTS["basketball_data"],
            "v1/games",
            params
        )
    
    # ==================== NBA Backtest ====================
    
    def get_sim_day(self) -> Optional[Dict[str, Any]]:
        """Get simulated day of NBA games for backtesting"""
        return self._make_request(
            self.API_HOSTS["nba_backtest"],
            "v1/simulation/day"
        )
    
    def get_sim_week(self) -> Optional[Dict[str, Any]]:
        """Get simulated week of NBA games for backtesting"""
        return self._make_request(
            self.API_HOSTS["nba_backtest"],
            "v1/simulation/week"
        )
    
    def get_sim_month(self) -> Optional[Dict[str, Any]]:
        """Get simulated month of NBA games for backtesting"""
        return self._make_request(
            self.API_HOSTS["nba_backtest"],
            "v1/simulation/month"
        )
    
    def get_random_set(self, size: int = 100) -> Optional[Dict[str, Any]]:
        """Get random set of NBA games for training"""
        params = {"size": size}
        return self._make_request(
            self.API_HOSTS["nba_backtest"],
            "v1/random",
            params
        )
    
    # ==================== Sports Odds API ====================
    
    def get_nba_futures(
        self,
        group_name: str = "nbafinals",
        season: str = "2024"
    ) -> Optional[Dict[str, Any]]:
        """Get NBA futures betting odds"""
        params = {"groupName": group_name, "season": season}
        return self._make_request(
            self.API_HOSTS["sports_odds_api"],
            "nba/futures",
            params
        )
    
    def get_nba_game_odds(self) -> Optional[Dict[str, Any]]:
        """Get NBA game odds"""
        return self._make_request(
            self.API_HOSTS["sports_odds_api"],
            "nba/odds"
        )
    
    # ==================== Bulk Data Collection ====================
    
    async def collect_all_data_async(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Async version: Collect data from all available endpoints
        """
        import asyncio
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Starting async data collection for {date}")
        
        data = {
            "collection_date": date,
            "timestamp": datetime.now().isoformat(),
            "data": {}
        }
        
        endpoints = [
            ("league_info", lambda: self.get_nba_league_info()),
            ("teams", lambda: self.get_nba_teams()),
            ("scoreboard", lambda: self.get_nba_scoreboard(date)),
            ("schedule", lambda: self.get_nba_schedule()),
            ("standings", lambda: self.get_nba_standings()),
            ("players", lambda: self.get_nba_players()),
            ("statistics", lambda: self.get_nba_statistics()),
            ("injury_reports", lambda: self.get_injury_reports(date)),
            ("live_odds", lambda: self.get_nba_odds()),
            ("scores", lambda: self.get_nba_scores()),
            ("daily_leaders", lambda: self.get_daily_leaders(date)),
            ("latest_news", lambda: self.get_latest_news()),
            ("events_today", lambda: self.get_events_for_today()),
            ("all_markets", lambda: self.get_all_markets()),
            ("all_bookies", lambda: self.get_all_bookies()),
            ("nba_futures", lambda: self.get_nba_futures()),
        ]
        
        for name, func in endpoints:
            try:
                # API calls are still sync here using requests, but sleep is async
                result = await asyncio.to_thread(func)
                if result:
                    data["data"][name] = result
                await asyncio.sleep(0.5)  # Async rate limiting
            except Exception as e:
                logger.error(f"✗ Error fetching {name}: {e}")
                data["data"][name] = {"error": str(e)}
        
        return data

    def collect_all_data(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Collect data from all available endpoints
        Returns a comprehensive dictionary with all data sources
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Starting comprehensive data collection for {date}")
        
        data = {
            "collection_date": date,
            "timestamp": datetime.now().isoformat(),
            "data": {}
        }
        
        # Collect from all endpoints
        endpoints = [
            ("league_info", lambda: self.get_nba_league_info()),
            ("teams", lambda: self.get_nba_teams()),
            ("scoreboard", lambda: self.get_nba_scoreboard(date)),
            ("schedule", lambda: self.get_nba_schedule()),
            ("standings", lambda: self.get_nba_standings()),
            ("players", lambda: self.get_nba_players()),
            ("statistics", lambda: self.get_nba_statistics()),
            ("injury_reports", lambda: self.get_injury_reports(date)),
            ("live_odds", lambda: self.get_nba_odds()),
            ("scores", lambda: self.get_nba_scores()),
            ("daily_leaders", lambda: self.get_daily_leaders(date)),
            ("latest_news", lambda: self.get_latest_news()),
            ("events_today", lambda: self.get_events_for_today()),
            ("all_markets", lambda: self.get_all_markets()),
            ("all_bookies", lambda: self.get_all_bookies()),
            ("nba_futures", lambda: self.get_nba_futures()),
        ]
        
        for name, func in endpoints:
            try:
                logger.info(f"Fetching {name}...")
                result = func()
                if result:
                    data["data"][name] = result
                    logger.info(f"✓ Successfully fetched {name}")
                else:
                    logger.warning(f"✗ No data returned for {name}")
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"✗ Error fetching {name}: {e}")
                data["data"][name] = {"error": str(e)}
        
        logger.info(f"Data collection complete. Collected {len(data['data'])} datasets")
        return data


# Global instance
rapid_api_client = RapidAPIClient()
