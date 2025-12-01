"""
Advanced Stats Agent - Scrapes advanced analytics with caching
"""
import requests
import pandas as pd
import numpy as np
import logging
import time
from pathlib import Path
from typing import Dict, List
from nba_api.stats.endpoints import (
    leaguedashteamstats,
    teamdashboardbygeneralsplits,
    playerdashboardbygeneralsplits
)

logger = logging.getLogger(__name__)

class AdvancedStatsAgent:
    """Fetch advanced team and player analytics"""
    
    def __init__(self):
        self.cache_dir = Path("data/advanced_stats")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.stats_cache = {}  # In-memory cache
        self.last_api_call = 0
        
    def get_team_advanced_stats(self, season='2024-25') -> pd.DataFrame:
        """Get advanced team stats (Offensive/Defensive Rating, Pace, etc.)"""
        # Check cache first
        cache_key = f"team_advanced_{season}"
        if cache_key in self.stats_cache:
            return self.stats_cache[cache_key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.parquet"
        if cache_file.exists():
            df = pd.read_parquet(cache_file)
            self.stats_cache[cache_key] = df
            logger.info(f"✅ Loaded cached advanced stats for {len(df)} teams")
            return df
        
        try:
            # Rate limit: 1 request per second
            time_since_last = time.time() - self.last_api_call
            if time_since_last < 1.0:
                time.sleep(1.0 - time_since_last)
            
            logger.info("Fetching advanced team stats...")
            stats = leaguedashteamstats.LeagueDashTeamStats(
                season=season,
                measure_type_detailed_defense='Advanced',
                per_mode_detailed='PerGame',
                timeout=60
            )
            self.last_api_call = time.time()
            df = stats.get_data_frames()[0]
            
            # Cache both in memory and disk
            self.stats_cache[cache_key] = df
            df.to_parquet(cache_file)
            logger.info(f"✅ Fetched advanced stats for {len(df)} teams")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch team advanced stats: {e}")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['TEAM_ID', 'OFF_RATING', 'DEF_RATING', 'NET_RATING', 'PACE', 'TS_PCT'])
    
    def get_team_home_away_splits(self, team_id: int, season='2024-25') -> Dict:
        """Get home/away performance splits"""
        cache_key = f"splits_{team_id}_{season}"
        if cache_key in self.stats_cache:
            return self.stats_cache[cache_key]
        
        try:
            # Rate limit
            time_since_last = time.time() - self.last_api_call
            if time_since_last < 1.0:
                time.sleep(1.0 - time_since_last)
            
            dashboard = teamdashboardbygeneralsplits.TeamDashboardByGeneralSplits(
                team_id=team_id,
                season=season,
                timeout=60
            )
            self.last_api_call = time.time()
            splits = dashboard.get_data_frames()[0]
            
            home = splits[splits['GROUP_VALUE'] == 'Home']
            away = splits[splits['GROUP_VALUE'] == 'Road']
            
            result = {
                'home_win_pct': home['W_PCT'].values[0] if len(home) > 0 else 0.5,
                'away_win_pct': away['W_PCT'].values[0] if len(away) > 0 else 0.5,
                'home_ppg': home['PTS'].values[0] if len(home) > 0 else 0,
                'away_ppg': away['PTS'].values[0] if len(away) > 0 else 0
            }
            self.stats_cache[cache_key] = result
            return result
        except Exception as e:
            logger.warning(f"Failed to fetch splits for team {team_id}: {e}")
            return {}

advanced_stats_agent = AdvancedStatsAgent()
