"""
"""Fetch player and team stats using nba_api.

The nba_api package is free and doesn't need any API keys - it just
talks to stats.nba.com directly.
"""
import logging
from typing import Dict, List
import pandas as pd
from pathlib import Path
from nba_api.stats.endpoints import (
    playergamelog,
    teamgamelog,
    leaguedashplayerstats,
    commonplayerinfo
)
from nba_api.stats.static import players, teams

logger = logging.getLogger(__name__)

class PlayerStatsFetcher:
    """Grab player and team statistics from the NBA API."""
    
    def __init__(self):
        self.cache_dir = Path("data/player_stats")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_all_players(self) -> List[Dict]:
        """Get the full list of active NBA players."""
        try:
            all_players = players.get_active_players()
            logger.info(f"✅ Found {len(all_players)} active players")
            return all_players
        except Exception as e:
            logger.error(f"Failed to fetch players: {e}")
            return []
    
    def get_player_season_stats(self, season: str = '2024-25') -> pd.DataFrame:
        """Pull season stats for all players."""
        try:
            logger.info(f"Fetching player stats for {season}...")
            stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                season_type_all_star='Regular Season'
            )
            df = stats.get_data_frames()[0]
            
            # Cache
            cache_file = self.cache_dir / f"season_stats_{season}.parquet"
            df.to_parquet(cache_file)
            
            logger.info(f"✅ Fetched stats for {len(df)} players")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch season stats: {e}")
            return pd.DataFrame()
    
    def get_player_recent_form(self, player_id: int, last_n_games: int = 5) -> Dict:
        """Check how a player has been performing in their most recent games."""
        try:
            gamelog = playergamelog.PlayerGameLog(
                player_id=player_id,
                season='2024-25'
            )
            df = gamelog.get_data_frames()[0].head(last_n_games)
            
            return {
                'avg_points': df['PTS'].mean(),
                'avg_rebounds': df['REB'].mean(),
                'avg_assists': df['AST'].mean(),
                'avg_plus_minus': df['PLUS_MINUS'].mean(),
                'games_played': len(df)
            }
        except Exception as e:
            logger.warning(f"Failed to fetch player {player_id} recent form: {e}")
            return {}
    
    def get_team_stats(self, season: str = '2024-25') -> pd.DataFrame:
        """Get aggregated stats for each team."""
        try:
            all_teams = teams.get_teams()
            team_stats = []
            
            for team in all_teams[:5]:  # Limit for demo
                team_id = team['id']
                logger.info(f"Fetching stats for {team['full_name']}...")
                
                gamelog = teamgamelog.TeamGameLog(
                    team_id=team_id,
                    season=season
                )
                df = gamelog.get_data_frames()[0]
                
                # Aggregate
                team_stats.append({
                    'team_id': team_id,
                    'team_name': team['full_name'],
                    'avg_points': df['PTS'].mean(),
                    'avg_points_against': (df['PTS'] - df['PLUS_MINUS']).mean(),
                    'wins': df['WL'].value_counts().get('W', 0),
                    'losses': df['WL'].value_counts().get('L', 0)
                })
                
            return pd.DataFrame(team_stats)
        except Exception as e:
            logger.error(f"Failed to fetch team stats: {e}")
            return pd.DataFrame()

# Global instance
stats_fetcher = PlayerStatsFetcher()
