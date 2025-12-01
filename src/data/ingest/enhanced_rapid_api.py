"""
Enhanced NBA Data Ingestion with RapidAPI Integration
Integrates the new RapidAPI client into the data pipeline
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.services.api.rapid_api_client import rapid_api_client
from src.common.config import settings

logger = logging.getLogger(__name__)


class EnhancedNBADataIngestion:
    """Enhanced data ingestion using comprehensive RapidAPI integration"""
    
    def __init__(self):
        """Initialize enhanced data ingestion"""
        self.api_client = rapid_api_client
        
    def fetch_game_data(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch comprehensive game data for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format, defaults to today
            
        Returns:
            Dictionary with all game-related data
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        logger.info(f"Fetching game data for {date}")
        
        game_data = {
            "date": date,
            "scoreboard": self.api_client.get_nba_scoreboard(date),
            "scores": self.api_client.get_nba_scores(days_from=1),
            "games_list": self.api_client.get_games_info(date=date),
            "box_scores": [],
        }
        
        # Get detailed game info if games exist
        if game_data["scoreboard"]:
            games = game_data["scoreboard"].get("games", [])
            for game in games:
                game_id = game.get("id")
                if game_id:
                    details = self.api_client.get_game_by_id(game_id)
                    if details:
                        game_data["box_scores"].append(details)
        
        return game_data
    
    def fetch_player_data(
        self,
        player_ids: Optional[List[int]] = None,
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive player data
        
        Args:
            player_ids: List of specific player IDs to fetch
            team_id: Fetch all players from specific team
            
        Returns:
            Dictionary with player data
        """
        logger.info("Fetching player data")
        
        player_data = {
            "players": [],
            "statistics": [],
            "daily_leaders": self.api_client.get_daily_leaders(),
        }
        
        if team_id:
            # Get team roster
            team_players = self.api_client.get_nba_players(team_id=team_id)
            player_data["players"].extend(team_players.get("players", []))
        elif player_ids:
            # Get specific players
            for player_id in player_ids:
                player = self.api_client.get_player_by_id(player_id)
                if player:
                    player_data["players"].append(player)
                    
                # Get player stats
                stats = self.api_client.get_all_stats(player_ids=[player_id])
                if stats:
                    player_data["statistics"].extend(stats.get("data", []))
        else:
            # Get all players (paginated)
            all_players = self.api_client.get_all_players(per_page=100)
            player_data["players"] = all_players.get("data", [])
        
        return player_data
    
    def fetch_team_data(
        self,
        team_ids: Optional[List[str]] = None,
        season: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch comprehensive team data
        
        Args:
            team_ids: List of specific team IDs
            season: Season year (e.g., "2024")
            
        Returns:
            Dictionary with team data
        """
        logger.info("Fetching team data")
        
        team_data = {
            "teams": self.api_client.get_nba_teams(),
            "all_teams": self.api_client.get_all_teams(),
            "standings": self.api_client.get_nba_standings(season),
            "rosters": [],
        }
        
        if team_ids:
            for team_id in team_ids:
                # Get team roster
                roster = self.api_client.get_team_roster(team_id)
                if roster:
                    team_data["rosters"].append({
                        "team_id": team_id,
                        "roster": roster
                    })
                
                # Get team season info
                if season:
                    season_info = self.api_client.get_team_season_info(team_id, season)
                    if season_info:
                        team_data.setdefault("season_info", []).append(season_info)
        
        return team_data
    
    def fetch_betting_data(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch comprehensive betting data
        
        Args:
            date: Date for betting data
            
        Returns:
            Dictionary with betting odds and props
        """
        logger.info("Fetching betting data")
        
        betting_data = {
            "live_odds": self.api_client.get_nba_odds(
                regions="us",
                markets="h2h,spreads,totals"
            ),
            "game_odds": self.api_client.get_nba_game_odds(),
            "futures": self.api_client.get_nba_futures(),
            "events_today": self.api_client.get_events_for_today(),
            "markets": self.api_client.get_all_markets(),
            "bookies": self.api_client.get_all_bookies(),
            "player_props": [],
        }
        
        # Get player props for today's events
        if betting_data["events_today"]:
            events = betting_data["events_today"].get("events", [])
            for event in events[:10]:  # Limit to 10 events to avoid rate limits
                event_id = event.get("id")
                if event_id:
                    props = self.api_client.get_player_odds_for_event(event_id)
                    if props:
                        betting_data["player_props"].append({
                            "event_id": event_id,
                            "event_name": event.get("name"),
                            "props": props
                        })
        
        return betting_data
    
    def fetch_injury_data(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch injury reports
        
        Args:
            date: Date for injury report (YYYY-MM-DD)
            
        Returns:
            Dictionary with injury data
        """
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
        logger.info(f"Fetching injury data for {date}")
        
        return {
            "date": date,
            "injuries": self.api_client.get_injury_reports(date)
        }
    
    def fetch_news_data(
        self,
        sources: Optional[List[str]] = None,
        teams: Optional[List[str]] = None,
        players: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch NBA news from multiple sources
        
        Args:
            sources: List of news sources (espn, nba, bleacher-report, etc.)
            teams: List of team names
            players: List of player names
            
        Returns:
            Dictionary with news articles
        """
        logger.info("Fetching news data")
        
        news_data = {
            "all_news": self.api_client.get_latest_news(limit=100),
            "by_source": {},
            "by_team": {},
            "by_player": {},
        }
        
        if sources:
            for source in sources:
                news = self.api_client.get_latest_news(source=source, limit=50)
                if news:
                    news_data["by_source"][source] = news
        
        if teams:
            for team in teams:
                news = self.api_client.get_latest_news(team=team, limit=30)
                if news:
                    news_data["by_team"][team] = news
        
        if players:
            for player in players:
                news = self.api_client.get_latest_news(player=player, limit=30)
                if news:
                    news_data["by_player"][player] = news
        
        return news_data
    
    def fetch_fantasy_data(self) -> Dict[str, Any]:
        """
        Fetch fantasy sports projections
        
        Returns:
            Dictionary with fantasy projections
        """
        logger.info("Fetching fantasy data")
        
        positions = ["G", "PG", "SG", "F", "PF", "SF", "C"]
        
        fantasy_data = {
            "rest_of_season": {},
            "current_week": {},
        }
        
        for position in positions:
            ros = self.api_client.get_nba_fantasy_rest_of_season(position)
            if ros:
                fantasy_data["rest_of_season"][position] = ros
            
            week = self.api_client.get_nba_fantasy_current_week(position)
            if week:
                fantasy_data["current_week"][position] = week
        
        return fantasy_data
    
    def fetch_schedule_data(
        self,
        season: Optional[str] = None,
        teams: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fetch schedule data
        
        Args:
            season: Season year
            teams: List of team names for team-specific schedules
            
        Returns:
            Dictionary with schedule data
        """
        logger.info("Fetching schedule data")
        
        schedule_data = {
            "full_schedule": self.api_client.get_nba_schedule(season),
            "schedule_details": self.api_client.get_schedule_data(season=season),
            "team_schedules": {},
        }
        
        if teams:
            for team in teams:
                team_schedule = self.api_client.get_schedule_data(season=season, team=team)
                if team_schedule:
                    schedule_data["team_schedules"][team] = team_schedule
        
        return schedule_data
    
    def fetch_historical_training_data(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        Fetch historical data for model training
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Dictionary with historical training data
        """
        logger.info(f"Fetching historical training data: {start_date} to {end_date}")
        
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Calculate seasons
        seasons = []
        current = start
        while current <= end:
            year = current.year
            if current.month >= 10:  # NBA season starts in October
                seasons.append(year)
            current = datetime(current.year + 1, 1, 1)
        
        training_data = {
            "date_range": {"start": start_date, "end": end_date},
            "seasons": list(set(seasons)),
            "games": [],
            "stats": [],
            "backtest_data": {},
        }
        
        # Fetch games for each season
        for season in training_data["seasons"]:
            games = self.api_client.get_all_games(
                seasons=[season],
                per_page=100
            )
            if games:
                training_data["games"].extend(games.get("data", []))
            
            stats = self.api_client.get_all_stats(
                seasons=[season],
                per_page=100
            )
            if stats:
                training_data["stats"].extend(stats.get("data", []))
        
        # Get backtesting simulation data
        training_data["backtest_data"]["sim_month"] = self.api_client.get_sim_month()
        training_data["backtest_data"]["random_set"] = self.api_client.get_random_set(size=500)
        
        return training_data
    
    def fetch_complete_dataset(
        self,
        date: Optional[str] = None,
        include_historical: bool = False
    ) -> Dict[str, Any]:
        """
        Fetch complete dataset with all available data
        
        Args:
            date: Target date for current data
            include_historical: Whether to include historical training data
            
        Returns:
            Complete dataset dictionary
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        logger.info(f"Fetching complete dataset for {date}")
        
        dataset = {
            "collection_date": date,
            "timestamp": datetime.now().isoformat(),
            "games": self.fetch_game_data(date),
            "teams": self.fetch_team_data(),
            "players": self.fetch_player_data(),
            "betting": self.fetch_betting_data(date),
            "injuries": self.fetch_injury_data(date),
            "news": self.fetch_news_data(
                sources=["espn", "nba", "bleacher-report"],
            ),
            "fantasy": self.fetch_fantasy_data(),
            "schedule": self.fetch_schedule_data(),
        }
        
        if include_historical:
            # Fetch last 30 days of historical data
            end_date = datetime.strptime(date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=30)
            
            dataset["historical"] = self.fetch_historical_training_data(
                start_date.strftime("%Y-%m-%d"),
                date
            )
        
        return dataset


# Global instance
enhanced_ingestion = EnhancedNBADataIngestion()
