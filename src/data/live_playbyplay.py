"""
Live Play-by-Play Data Fetcher
Uses NBA's CDN for real-time game data (no API key required!)
Based on: https://jman4190.medium.com/how-to-accessing-live-nba-play-by-play-data-f24e02b0a976
"""
import requests
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Optional
from nba_api.stats.endpoints import leaguegamefinder
from datetime import datetime

logger = logging.getLogger(__name__)

# Headers to avoid timeout
NBA_HEADERS = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'x-nba-stats-token': 'true',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'x-nba-stats-origin': 'stats',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Referer': 'https://stats.nba.com/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
}

class LivePlayByPlayFetcher:
    """Fetch live play-by-play data from NBA CDN"""
    
    def __init__(self):
        self.cache_dir = Path("data/playbyplay")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_game_ids(self, season: str = '2024-25', season_type: str = 'Regular Season') -> List[str]:
        """Get all game IDs for a season using nba_api"""
        try:
            logger.info(f"Fetching game IDs for {season} {season_type}...")
            gamefinder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season,
                league_id_nullable='00',
                season_type_nullable=season_type
            )
            games = gamefinder.get_data_frames()[0]
            game_ids = games['GAME_ID'].unique().tolist()
            logger.info(f"✅ Found {len(game_ids)} games")
            return game_ids
        except Exception as e:
            logger.error(f"Failed to fetch game IDs: {e}")
            return []
    
    def get_live_playbyplay(self, game_id: str) -> Optional[pd.DataFrame]:
        """
        Fetch live play-by-play data for a specific game.
        This works for LIVE and completed games - no API key needed!
        """
        play_by_play_url = f"https://cdn.nba.com/static/json/liveData/playbyplay/playbyplay_{game_id}.json"
        
        try:
            response = requests.get(url=play_by_play_url, headers=NBA_HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            play_by_play = data['game']['actions']
            df = pd.DataFrame(play_by_play)
            df['gameid'] = game_id
            
            # Cache it
            cache_file = self.cache_dir / f"{game_id}.parquet"
            df.to_parquet(cache_file)
            
            return df
            
        except Exception as e:
            logger.warning(f"Failed to fetch play-by-play for {game_id}: {e}")
            return None
    
    def get_current_season_data(self, max_games: int = 100) -> pd.DataFrame:
        """Fetch play-by-play for current season (up to max_games)"""
        game_ids = self.get_game_ids('2024-25')[:max_games]
        
        all_data = []
        for i, game_id in enumerate(game_ids):
            logger.info(f"Fetching game {i+1}/{len(game_ids)}: {game_id}")
            df = self.get_live_playbyplay(game_id)
            if df is not None:
                all_data.append(df)
                
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            logger.info(f"✅ Fetched {len(combined)} play-by-play actions from {len(all_data)} games")
            return combined
        else:
            return pd.DataFrame()
    
    def extract_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract momentum and pace features from play-by-play"""
        # Sort by game and time
        df = df.sort_values(by=['gameid', 'orderNumber'])
        
        # Calculate time between actions (pace)
        df['timeActual'] = pd.to_datetime(df['timeActual'], errors='coerce')
        df['time_since_last_action'] = df.groupby('gameid')['timeActual'].diff().dt.total_seconds()
        
        # Calculate scoring runs
        df['is_score'] = df['scoreHome'].notnull() | df['scoreAway'].notnull()
        
        # Team momentum (scoring in last 5 actions)
        df['home_momentum'] = df.groupby('gameid')['scoreHome'].rolling(5, min_periods=1).sum().reset_index(0, drop=True)
        df['away_momentum'] = df.groupby('gameid')['scoreAway'].rolling(5, min_periods=1).sum().reset_index(0, drop=True)
        
        return df

# Global instance
playbyplay_fetcher = LivePlayByPlayFetcher()
