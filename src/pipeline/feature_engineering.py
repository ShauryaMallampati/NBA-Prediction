"""
Master Feature Engineering Pipeline
Combines all agent data into rich feature sets
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import logging
from typing import Dict, List
from src.agents.advanced_stats_agent import advanced_stats_agent
from src.agents.rest_fatigue_agent import rest_fatigue_agent
from src.agents.betting_market_agent import betting_market_agent
from src.agents.matchup_agent import matchup_agent
from src.data.live_playbyplay import playbyplay_fetcher
from src.data.player_stats import stats_fetcher
from src.data.web_scraper import injury_scraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Combine all data sources into ML-ready features"""
    
    def __init__(self):
        self.output_dir = Path("data/engineered_features")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def build_game_features(self, game_id: str, home_team_id: int, away_team_id: int, 
                           game_date: str, season: str = '2024-25') -> Dict:
        """Build comprehensive feature set for a single game"""
        
        logger.info(f"Engineering features for game {game_id}...")
        features = {}
        
        # 1. Advanced Stats
        try:
            team_advanced = advanced_stats_agent.get_team_advanced_stats(season)
            home_advanced = team_advanced[team_advanced['TEAM_ID'] == home_team_id]
            away_advanced = team_advanced[team_advanced['TEAM_ID'] == away_team_id]
            
            if len(home_advanced) > 0:
                features['home_off_rating'] = home_advanced['OFF_RATING'].values[0]
                features['home_def_rating'] = home_advanced['DEF_RATING'].values[0]
                features['home_pace'] = home_advanced['PACE'].values[0]
                features['home_true_shooting_pct'] = home_advanced['TS_PCT'].values[0]
            
            if len(away_advanced) > 0:
                features['away_off_rating'] = away_advanced['OFF_RATING'].values[0]
                features['away_def_rating'] = away_advanced['DEF_RATING'].values[0]
                features['away_pace'] = away_advanced['PACE'].values[0]
                features['away_true_shooting_pct'] = away_advanced['TS_PCT'].values[0]
                
        except Exception as e:
            logger.warning(f"Advanced stats failed: {e}")
        
        # 2. Rest & Fatigue
        try:
            home_rest = rest_fatigue_agent.calculate_rest_days(home_team_id, game_date, season)
            away_rest = rest_fatigue_agent.calculate_rest_days(away_team_id, game_date, season)
            
            features['home_rest_days'] = home_rest.get('rest_days', 3)
            features['home_is_back_to_back'] = int(home_rest.get('is_back_to_back', False))
            features['away_rest_days'] = away_rest.get('rest_days', 3)
            features['away_is_back_to_back'] = int(away_rest.get('is_back_to_back', False))
            features['rest_advantage'] = features['home_rest_days'] - features['away_rest_days']
            
        except Exception as e:
            logger.warning(f"Rest/fatigue failed: {e}")
        
        # 3. Injuries
        try:
            injuries = injury_scraper.get_cached_injuries()
            # Count injured starters (simplified)
            features['home_injured_count'] = 0
            features['away_injured_count'] = 0
            
        except Exception as e:
            logger.warning(f"Injury data failed: {e}")
        
        # 4. Historical Matchup
        try:
            h2h = matchup_agent.get_h2h_record(home_team_id, away_team_id)
            features['h2h_win_pct'] = h2h.get('h2h_win_pct', 0.5)
            features['h2h_point_diff'] = h2h.get('avg_point_differential', 0)
            
        except Exception as e:
            logger.warning(f"H2H data failed: {e}")
        
        # 5. Home Court Advantage
        features['is_home_game'] = 1
        features['home_court_factor'] = 1.03  # ~3% advantage
        
        return features
    
    def build_training_dataset(self, season: str = '2024-25', max_games: int = 100) -> pd.DataFrame:
        """Build full training dataset with all features"""
        
        logger.info(f"Building training dataset for {season}...")
        
        # Get play-by-play data (has game IDs and outcomes)
        pbp_data = playbyplay_fetcher.get_current_season_data(max_games)
        
        if len(pbp_data) == 0:
            logger.error("No play-by-play data available")
            return pd.DataFrame()
        
        # Get unique games
        games = pbp_data.groupby('gameid').first().reset_index()
        
        all_features = []
        processed_games = set()  # Avoid duplicates
        
        # Use to_dict('records') instead of iterrows() for ~10x faster iteration
        game_records = games.to_dict('records')
        
        for game in game_records:
            game_id = game.get('gameid', '')
            
            # Skip if already processed
            if game_id in processed_games:
                continue
            processed_games.add(game_id)
            
            # Extract team IDs from game_id (format: 002YYSNNNN where YY=year, S=season type, NNNN=game number)
            # For now use placeholder - need actual game metadata
            try:
                home_team_id = int(game.get('home_team_id', 1610612737))
                away_team_id = int(game.get('visitor_team_id', 1610612738))
                game_date = game.get('date', '2024-12-01')
            except Exception:
                game_date = '2024-12-01'   # Placeholder
            
            features = self.build_game_features(
                game_id, home_team_id, away_team_id, game_date, season
            )
            features['game_id'] = game_id
            all_features.append(features)
        
        df = pd.DataFrame(all_features)
        
        # Save
        output_file = self.output_dir / f"training_features_{season}.parquet"
        df.to_parquet(output_file)
        logger.info(f"✅ Built {len(df)} game features, saved to {output_file}")
        
        return df

feature_engineer = FeatureEngineer()
