"""
Rest & Fatigue Agent - Calculates rest days and travel fatigue
"""
import pandas as pd
import numpy as np
import logging
import time
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta
from nba_api.stats.endpoints import teamgamelog

logger = logging.getLogger(__name__)

class RestFatigueAgent:
    """Calculate rest days and back-to-back games"""
    
    def __init__(self):
        self.cache_dir = Path("data/rest_fatigue")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.gamelog_cache = {}  # Cache gamelogs per team
        self.last_api_call = 0
        
    def calculate_rest_days(self, team_id: int, target_date: str, season='2024-25') -> Dict:
        """Calculate days of rest before a game"""
        cache_key = f"{team_id}_{season}"
        
        # Use cached gamelog if available
        if cache_key not in self.gamelog_cache:
            try:
                # Rate limit: 1 request per second
                time_since_last = time.time() - self.last_api_call
                if time_since_last < 1.0:
                    time.sleep(1.0 - time_since_last)
                
                gamelog = teamgamelog.TeamGameLog(team_id=team_id, season=season, timeout=60)
                self.last_api_call = time.time()
                df = gamelog.get_data_frames()[0]
                
                # Sort by date
                df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], format='%b %d, %Y')
                df = df.sort_values('GAME_DATE', ascending=False)
                
                self.gamelog_cache[cache_key] = df
            except Exception as e:
                logger.warning(f"Failed to fetch gamelog for team {team_id}: {e}")
                return {'rest_days': 1, 'is_back_to_back': False, 'games_in_last_7_days': 0}
        
        try:
            df = self.gamelog_cache[cache_key]
            
            target = pd.to_datetime(target_date)
            
            # Find last game before target
            past_games = df[df['GAME_DATE'] < target]
            if len(past_games) > 0:
                last_game = past_games.iloc[0]['GAME_DATE']
                rest_days = (target - last_game).days
                is_back_to_back = rest_days == 1
                
                return {
                    'rest_days': rest_days,
                    'is_back_to_back': is_back_to_back,
                    'games_in_last_7_days': len(past_games[past_games['GAME_DATE'] >= target - timedelta(days=7)])
                }
            
            return {'rest_days': 7, 'is_back_to_back': False, 'games_in_last_7_days': 0}
            
        except Exception as e:
            logger.warning(f"Failed to calculate rest for team {team_id}: {e}")
            return {}

rest_fatigue_agent = RestFatigueAgent()
