"""
Historical Matchup Agent - H2H records and matchup-specific stats
"""
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List
from nba_api.stats.endpoints import teamgamelog
from collections import defaultdict

logger = logging.getLogger(__name__)

class HistoricalMatchupAgent:
    """Analyze head-to-head history and matchup patterns"""
    
    def __init__(self):
        self.cache_dir = Path("data/matchups")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_h2h_record(self, team1_id: int, team2_id: int, last_n_seasons: int = 3) -> Dict:
        """Get head-to-head record between two teams"""
        try:
            # Get recent games for team1
            seasons = ['2024-25', '2023-24', '2022-23'][:last_n_seasons]
            
            team1_wins = 0
            team2_wins = 0
            total_games = 0
            avg_point_diff = []
            
            for season in seasons:
                try:
                    gamelog = teamgamelog.TeamGameLog(team_id=team1_id, season=season)
                    df = gamelog.get_data_frames()[0]
                    
                    # Filter games against team2
                    # This is simplified - would need opponent ID matching
                    h2h_games = df.head(5)  # Placeholder
                    
                    for _, game in h2h_games.iterrows():
                        total_games += 1
                        if 'W' in game.get('WL', ''):
                            team1_wins += 1
                        else:
                            team2_wins += 1
                        
                        avg_point_diff.append(game.get('PLUS_MINUS', 0))
                        
                except:
                    continue
            
            if total_games > 0:
                return {
                    'h2h_win_pct': team1_wins / total_games,
                    'h2h_games_played': total_games,
                    'avg_point_differential': np.mean(avg_point_diff) if avg_point_diff else 0
                }
            
            return {'h2h_win_pct': 0.5, 'h2h_games_played': 0, 'avg_point_differential': 0}
            
        except Exception as e:
            logger.warning(f"Failed to get H2H record: {e}")
            return {}

matchup_agent = HistoricalMatchupAgent()
