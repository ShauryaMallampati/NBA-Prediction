"""Pregame prediction service using trained XGBoost model."""

import pickle
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
from nba_api.live.nba.endpoints import scoreboard

from src.common.logger import setup_logger

logger = setup_logger(__name__)


class PregamePredictionService:
    """Service for pregame predictions using trained XGBoost model."""
    
    def __init__(self):
        """Initialize service and load trained model."""
        self.model_path = Path(__file__).parent.parent.parent / "artifacts" / "models"
        self.model = None
        self.calibrated_model = None
        self.feature_names = None
        self.metadata = None
        self._load_model()
    
    async def load_model_async(self):
        """Async version of model loading"""
        import asyncio
        try:
            model_file = self.model_path / "pregame_model.pkl"
            calibrated_file = self.model_path / "calibrated_model.pkl"
            metadata_file = self.model_path / "pregame_model_metadata.json"
            
            async def read_pickle(path):
                with open(path, 'rb') as f:
                    return pickle.load(f)
            
            async def read_json(path):
                with open(path, 'r') as f:
                    return json.load(f)

            if model_file.exists():
                self.model = await asyncio.to_thread(read_pickle, model_file)
            
            if calibrated_file.exists():
                self.calibrated_model = await asyncio.to_thread(read_pickle, calibrated_file)
            
            if metadata_file.exists():
                self.metadata = await asyncio.to_thread(read_json, metadata_file)
                self.feature_names = self.metadata.get('feature_names', [])
                
        except Exception as e:
            logger.error(f"Error loading model async: {e}")

    def _load_model(self):
        """Load trained XGBoost model and metadata (sync)."""
        try:
            model_file = self.model_path / "pregame_model.pkl"
            calibrated_file = self.model_path / "calibrated_model.pkl"
            metadata_file = self.model_path / "pregame_model_metadata.json"
            
            if model_file.exists():
                with open(model_file, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info(f"Loaded model from {model_file}")
            
            if calibrated_file.exists():
                with open(calibrated_file, 'rb') as f:
                    self.calibrated_model = pickle.load(f)
                logger.info(f"Loaded calibrated model from {calibrated_file}")
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.metadata = json.load(f)
                self.feature_names = self.metadata.get('feature_names', [])
                logger.info(f"Loaded metadata with {len(self.feature_names)} features")
            else:
                logger.warning(f"Metadata file not found: {metadata_file}")
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")
    
    def predict_game(self, home_team: str, away_team: str, game_date: Optional[str] = None) -> Dict:
        """
        Make pregame prediction for a matchup.
        
        Args:
            home_team: Home team abbreviation (e.g., 'GSW')
            away_team: Away team abbreviation (e.g., 'LAL')
            game_date: Optional game date (ISO format)
        
        Returns:
            Dictionary with predictions and feature values
        """
        if self.model is None:
            logger.error("Model not loaded")
            return {
                'error': 'Model not available',
                'home_win_prob': 0.5,
                'away_win_prob': 0.5,
            }
        
        try:
            # Load engineered features
            features_path = Path(__file__).parent.parent.parent / "data" / "processed" / "engineered_features.csv"
            df = pd.read_csv(features_path)
            df['date'] = pd.to_datetime(df['date'])
            
            # Get latest features for each team to use as baseline
            home_features = df[df['home_team'] == home_team].iloc[-1] if len(df[df['home_team'] == home_team]) > 0 else None
            away_features = df[df['away_team'] == away_team].iloc[-1] if len(df[df['away_team'] == away_team]) > 0 else None
            
            if home_features is None or away_features is None:
                logger.warning(f"Features not found for {home_team} vs {away_team}")
                return {
                    'error': 'Team features not available',
                    'home_win_prob': 0.5,
                    'away_win_prob': 0.5,
                }
            
            # Build feature vector
            feature_dict = {}
            
            # Core Elo and differentials
            feature_dict['home_elo'] = home_features.get('home_elo', 1500)
            feature_dict['away_elo'] = away_features.get('away_elo', 1500)
            feature_dict['elo_diff'] = feature_dict['home_elo'] - feature_dict['away_elo']
            feature_dict['elo_win_prob'] = home_features.get('elo_win_prob', 0.5)
            
            # Recent form
            feature_dict['home_last_5_wins'] = home_features.get('home_last_5_wins', 0)
            feature_dict['home_last_5_win_pct'] = home_features.get('home_last_5_win_pct', 0.5)
            feature_dict['home_last_10_wins'] = home_features.get('home_last_10_wins', 0)
            feature_dict['home_last_10_win_pct'] = home_features.get('home_last_10_win_pct', 0.5)
            
            feature_dict['away_last_5_wins'] = away_features.get('away_last_5_wins', 0)
            feature_dict['away_last_5_win_pct'] = away_features.get('away_last_5_win_pct', 0.5)
            feature_dict['away_last_10_wins'] = away_features.get('away_last_10_wins', 0)
            feature_dict['away_last_10_win_pct'] = away_features.get('away_last_10_win_pct', 0.5)
            
            # Head-to-head
            feature_dict['h2h_home_wins'] = home_features.get('h2h_home_wins', 0)
            feature_dict['h2h_away_wins'] = home_features.get('h2h_away_wins', 0)
            
            # Rest and scheduling
            feature_dict['home_rest_days'] = home_features.get('home_rest_days', 1)
            feature_dict['away_rest_days'] = away_features.get('away_rest_days', 1)
            feature_dict['home_back_to_back'] = home_features.get('home_back_to_back', 0)
            feature_dict['away_back_to_back'] = away_features.get('away_back_to_back', 0)
            
            # Home/away splits
            feature_dict['home_home_win_pct'] = home_features.get('home_home_win_pct', 0.5)
            feature_dict['away_away_win_pct'] = away_features.get('away_away_win_pct', 0.5)
            
            # Additional advanced features (fill with reasonable defaults if not available)
            feature_dict['home_court_advantage'] = home_features.get('home_court_advantage', 3.0)
            feature_dict['home_clutch_record'] = home_features.get('home_clutch_record', 0.5)
            feature_dict['home_games_last_5'] = home_features.get('home_games_last_5', 5)
            feature_dict['away_games_last_5'] = away_features.get('away_games_last_5', 5)
            feature_dict['home_recent_pt_diff'] = home_features.get('home_recent_pt_diff', 0)
            feature_dict['away_recent_pt_diff'] = away_features.get('away_recent_pt_diff', 0)
            feature_dict['home_opp_elo_avg'] = away_features.get('away_elo', 1500)  # Opponent Elo
            feature_dict['away_opp_elo_avg'] = home_features.get('home_elo', 1500)
            feature_dict['home_last_3_win_pct'] = home_features.get('home_last_3_win_pct', 0.5)
            feature_dict['away_last_3_win_pct'] = away_features.get('away_last_3_win_pct', 0.5)
            feature_dict['home_last_3_wins'] = home_features.get('home_last_3_wins', 1)
            feature_dict['away_last_3_wins'] = away_features.get('away_last_3_wins', 1)
            
            # Create feature DataFrame in correct order
            X = pd.DataFrame([feature_dict])
            
            # Ensure all required features are present
            for feat in self.feature_names:
                if feat not in X.columns:
                    X[feat] = 0
            
            # Select only the features used in training
            X = X[self.feature_names]
            
            # Make prediction
            home_win_prob = float(self.calibrated_model.predict_proba(X)[0][1]) if self.calibrated_model is not None else float(self.model.predict_proba(X)[0][1])
            
            # Get feature importance info
            top_features = self._get_top_features(X, 5)
            
            return {
                'game_id': f"{game_date or 'today'}_{home_team}_{away_team}",
                'date': game_date or datetime.now().isoformat(),
                'home_team': home_team,
                'away_team': away_team,
                'home_win_prob': home_win_prob,
                'away_win_prob': 1.0 - home_win_prob,
                'confidence': abs(home_win_prob - 0.5) * 2,  # 0-1, higher = more confident
                'top_features': top_features,
                'model_version': 'xgboost_calibrated',
                'accuracy': self.metadata.get('test_accuracy', 0.638) if self.metadata else 0.638,
            }
        
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return {
                'error': str(e),
                'home_win_prob': 0.5,
                'away_win_prob': 0.5,
            }
    
    def _get_top_features(self, X: pd.DataFrame, n: int = 5) -> Dict[str, float]:
        """Get top N most important features."""
        if not hasattr(self.model, 'feature_importances_'):
            return {}
        
        importance = self.model.feature_importances_
        feature_importance = pd.Series(importance, index=self.feature_names)
        top_features = feature_importance.nlargest(n).to_dict()
        
        return {k: float(v) for k, v in top_features.items()}
    
    async def predict_games_for_date_async(self, date_str: Optional[str] = None) -> List[Dict]:
        """Async version of predict_games_for_date"""
        import asyncio
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # ScoreBoard is blocking, run in thread
            nba_response = await asyncio.to_thread(scoreboard.ScoreBoard)
            games = await asyncio.to_thread(nba_response.get_data_frames)
            games = games[0] if games else pd.DataFrame()
            
            predictions = []
            # Use to_dict('records') instead of iterrows()
            game_records = games.to_dict('records')
            
            for game in game_records:
                home_team = game.get('HOME_TEAM_ABBREVIATION')
                away_team = game.get('AWAY_TEAM_ABBREVIATION')
                game_date = game.get('GAME_DATE_EST', date_str)
                
                if home_team and away_team:
                    # predict_game involves pd.read_csv, keep it in thread
                    pred = await asyncio.to_thread(self.predict_game, home_team, away_team, game_date)
                    predictions.append(pred)
            
            return predictions
        except Exception as e:
            logger.error(f"Error async predicting games for {date_str}: {e}")
            return []

    def predict_games_for_date(self, date_str: Optional[str] = None) -> List[Dict]:
        """
        Get predictions for all games on a given date.
        
        Args:
            date_str: Date in format YYYY-MM-DD (defaults to today)
        
        Returns:
            List of prediction dictionaries
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Get today's games from NBA Live API
            nba_response = scoreboard.ScoreBoard()
            games = nba_response.get_data_frames()[0]
            
            predictions = []
            # Use to_dict('records') instead of iterrows()
            game_records = games.to_dict('records')
            
            for game in game_records:
                home_team = game.get('HOME_TEAM_ABBREVIATION')
                away_team = game.get('AWAY_TEAM_ABBREVIATION')
                game_date = game.get('GAME_DATE_EST', date_str)
                
                if home_team and away_team:
                    pred = self.predict_game(home_team, away_team, game_date)
                    predictions.append(pred)
            
            logger.info(f"Generated {len(predictions)} predictions for {date_str}")
            return predictions
        
        except Exception as e:
            logger.error(f"Error getting games for {date_str}: {e}")
            return []
