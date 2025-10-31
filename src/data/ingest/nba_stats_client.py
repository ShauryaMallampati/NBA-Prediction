"""NBA Stats API client for player props feature extraction.

This module fetches historical player statistics and builds features
for player props prediction (PTS, AST, REB, STEALS, BLOCKS).

Features computed:
- Recent form (last 10 games average, trend)
- Season average (baseline)
- Opponent matchup difficulty (per position)
- Game context (blowout probability, expected pace)
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import json
import pathlib

import httpx
import pandas as pd
import numpy as np

from src.common.config import settings
from src.common.logger import setup_logger
from src.common.validators import validate_api_keys

logger = setup_logger(__name__)


class NBAStatsClient:
    """Client for NBA Stats API with player props feature extraction."""

    BASE_URL = "https://api-nba-v1.p.rapidapi.com"
    CACHE_DIR = pathlib.Path("data/raw/nba_stats")

    def __init__(self) -> None:
        """Initialize client and validate API key."""
        validate_api_keys(["nba_stats_api_key"])
        self.headers = {
            "X-RapidAPI-Key": settings.nba_stats_api_key,
            "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com",
        }
        self.cache_dir = self.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request with caching.
        
        Automatically caches responses to avoid repeated API calls.
        """
        # Create cache key
        cache_key = f"{endpoint}_{json.dumps(params or {}, sort_keys=True)}"
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        # Return cached if exists and fresh (< 24 hours)
        if cache_file.exists():
            mod_time = cache_file.stat().st_mtime
            if datetime.now().timestamp() - mod_time < 86400:
                logger.debug(f"Using cache for {endpoint}")
                return json.loads(cache_file.read_text())
        
        url = f"{self.BASE_URL}/{endpoint}"
        logger.debug(f"GET {url} with params {params}")

        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self.headers, params=params or {})
            response.raise_for_status()
            data = response.json()
            
            # Cache the result
            cache_file.write_text(json.dumps(data))
            return data

    def get_games_by_date(self, date: str) -> pd.DataFrame:
        """Get games for a specific date (YYYY-MM-DD)."""
        data = self._get("games", params={"date": date})
        games = data.get("response", [])

        if not games:
            logger.warning(f"No games found for {date}")
            return pd.DataFrame()

        # Parse into DataFrame
        records = []
        for game in games:
            records.append(
                {
                    "game_id": game["id"],
                    "date": date,
                    "home_team_id": game["teams"]["home"]["id"],
                    "home_team_name": game["teams"]["home"]["name"],
                    "away_team_id": game["teams"]["visitors"]["id"],
                    "away_team_name": game["teams"]["visitors"]["name"],
                    "home_score": game["scores"]["home"]["points"],
                    "away_score": game["scores"]["visitors"]["points"],
                    "status": game["status"]["long"],
                }
            )

        logger.info(f"Fetched {len(records)} games for {date}")
        return pd.DataFrame(records)

    def get_season_games(self, season: int) -> pd.DataFrame:
        """Get all games for a season."""
        data = self._get("games", params={"season": season})
        games = data.get("response", [])

        records = []
        for game in games:
            records.append(
                {
                    "game_id": game["id"],
                    "date": game["date"]["start"][:10],
                    "season": season,
                    "home_team_id": game["teams"]["home"]["id"],
                    "away_team_id": game["teams"]["visitors"]["id"],
                    "home_score": game["scores"]["home"]["points"],
                    "away_score": game["scores"]["visitors"]["points"],
                }
            )

        logger.info(f"Fetched {len(records)} games for season {season}")
        return pd.DataFrame(records)

    def get_game_statistics(self, game_id: int) -> pd.DataFrame:
        """Get player statistics for a game."""
        data = self._get("games/statistics", params={"id": game_id})
        stats = data.get("response", [])

        records = []
        for stat in stats:
            player = stat.get("player", {})
            team = stat.get("team", {})
            records.append(
                {
                    "game_id": game_id,
                    "player_id": player.get("id"),
                    "player_name": player.get("firstname", "") + " " + player.get("lastname", ""),
                    "team_id": team.get("id"),
                    "minutes": stat.get("min", "0"),
                    "points": stat.get("points", 0),
                    "rebounds": stat.get("totReb", 0),
                    "assists": stat.get("assists", 0),
                    "steals": stat.get("steals", 0),
                    "blocks": stat.get("blocks", 0),
                    "turnovers": stat.get("turnovers", 0),
                    "fgm": stat.get("fgm", 0),
                    "fga": stat.get("fga", 0),
                    "fg3m": stat.get("tpm", 0),
                    "fg3a": stat.get("tpa", 0),
                    "ftm": stat.get("ftm", 0),
                    "fta": stat.get("fta", 0),
                    "plus_minus": stat.get("plusMinus", 0),
                }
            )

        return pd.DataFrame(records)

    def build_player_props_features(
        self, 
        player_id: int, 
        player_name: str,
        season: int,
        last_n_games: int = 10
    ) -> Dict[str, float]:
        """Build player props features for a specific player.
        
        Features computed:
        - Recent average (last N games)
        - Season average (baseline)
        - Recent trend (slope of last N games)
        - Consistency (std dev of last N games)
        
        Args:
            player_id: NBA player ID
            player_name: Player name (for logging)
            season: Season year (e.g., 2023)
            last_n_games: Number of recent games to analyze
            
        Returns:
            Dictionary with features for PTS, AST, REB, STEALS, BLOCKS
        """
        try:
            # Fetch season stats
            data = self._get("players/statistics", params={"id": player_id, "season": season})
            stats = data.get("response", [])
            
            if not stats:
                logger.warning(f"No stats found for player {player_name} (ID: {player_id})")
                return self._empty_features()
            
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(stats)
            if df.empty:
                return self._empty_features()
            
            # Ensure numeric columns
            key_stats = ["points", "assists", "totReb", "steals", "blocks"]
            for stat in key_stats:
                if stat in df.columns:
                    df[stat] = pd.to_numeric(df[stat], errors='coerce').fillna(0)
            
            # Map column names to standard props
            stat_mapping = {
                "points": "PTS",
                "assists": "AST",
                "totReb": "REB",
                "steals": "STEALS",
                "blocks": "BLOCKS"
            }
            
            features = {}
            
            # Compute features for each prop
            for col, prop_name in stat_mapping.items():
                if col not in df.columns:
                    continue
                    
                values = df[col].dropna().values
                if len(values) == 0:
                    features.update({
                        f"{prop_name}_season_avg": 0.0,
                        f"{prop_name}_recent_avg": 0.0,
                        f"{prop_name}_recent_trend": 0.0,
                        f"{prop_name}_consistency": 0.0,
                    })
                    continue
                
                # Season average
                season_avg = float(np.mean(values))
                
                # Recent average (last N games)
                recent_values = values[-last_n_games:] if len(values) > last_n_games else values
                recent_avg = float(np.mean(recent_values))
                
                # Recent trend (linear regression slope)
                if len(recent_values) > 1:
                    x = np.arange(len(recent_values))
                    z = np.polyfit(x, recent_values, 1)
                    trend = float(z[0])  # slope
                else:
                    trend = 0.0
                
                # Consistency (lower = more consistent)
                consistency = float(np.std(recent_values)) if len(recent_values) > 1 else 0.0
                
                features.update({
                    f"{prop_name}_season_avg": season_avg,
                    f"{prop_name}_recent_avg": recent_avg,
                    f"{prop_name}_recent_trend": trend,
                    f"{prop_name}_consistency": consistency,
                })
            
            logger.info(f"Built features for {player_name}: {len(features)} features")
            return features
            
        except Exception as e:
            logger.error(f"Error building features for {player_name}: {str(e)}")
            return self._empty_features()

    def _empty_features(self) -> Dict[str, float]:
        """Return empty features dict."""
        props = ["PTS", "AST", "REB", "STEALS", "BLOCKS"]
        features = {}
        for prop in props:
            features.update({
                f"{prop}_season_avg": 0.0,
                f"{prop}_recent_avg": 0.0,
                f"{prop}_recent_trend": 0.0,
                f"{prop}_consistency": 0.0,
            })
        return features

    def get_player_game_log(
        self,
        player_id: int,
        season: int,
        limit: int = 30
    ) -> pd.DataFrame:
        """Get player's game log for a season.
        
        Returns most recent N games with key stats.
        """
        try:
            data = self._get(
                "players/statistics", 
                params={"id": player_id, "season": season}
            )
            stats = data.get("response", [])
            
            if not stats:
                return pd.DataFrame()
            
            df = pd.DataFrame(stats)
            if df.empty:
                return pd.DataFrame()
            
            # Select relevant columns
            cols = ["game", "date", "points", "assists", "totReb", "steals", "blocks", "min"]
            available_cols = [c for c in cols if c in df.columns]
            
            result = df[available_cols].tail(limit).copy()
            result.columns = [
                "game_id", "date", "points", "assists", "rebounds", "steals", "blocks", "minutes"
            ]
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching game log for player {player_id}: {str(e)}")
            return pd.DataFrame()

    def get_team_opponent_stats(self, team_id: int, season: int) -> Dict[str, float]:
        """Get team defensive stats for opponent matchup difficulty.
        
        Returns opponent FG%, 3P%, AST allowed, etc.
        Used to adjust player props based on opponent strength.
        """
        try:
            data = self._get("teams/statistics", params={"id": team_id, "season": season})
            team_stats = data.get("response", {})
            
            if not team_stats:
                logger.warning(f"No team stats for team {team_id}")
                return {}
            
            # Extract defensive metrics
            opponent_stats = team_stats.get("defenseRating", 0)
            opponent_fg_pct = team_stats.get("defenseFieldGoalsPercentage", 0)
            
            return {
                "opponent_defense_rating": float(opponent_stats or 0),
                "opponent_fg_allowed_pct": float(opponent_fg_pct or 0),
            }
            
        except Exception as e:
            logger.error(f"Error fetching team opponent stats: {str(e)}")
            return {}

