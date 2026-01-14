import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime

from src.models.pregame.train_ensemble import EnsembleTrainer
from src.api.live_odds import get_live_odds_data, get_live_odds_data_async
from src.api.live_features import LiveFeatureEngineer
from scripts.train_ensemble_model import create_features_from_odds, load_betting_data

# Initialize logger
logger = logging.getLogger(__name__)

class PredictionPipeline:
    """
    Unified pipeline for generating NBA predictions.
    Used by both the API and Daily CLI Runner.
    """
    
    def __init__(self, model_dir: str = "artifacts/models/pregame"):
        self.model_dir = model_dir
        self.trainer = None
        self.feature_engineer = None
        self._load_models()
        
    def _load_models(self):
        """Load trained models from artifacts."""
        try:
            self.trainer = EnsembleTrainer(output_dir=self.model_dir)
            self.trainer.load_models()
            
            if self.trainer.xgb_calibrated:
                logger.info("✅ Models loaded successfully")
                self.feature_engineer = LiveFeatureEngineer()
            else:
                logger.warning("⚠️ No saved ensemble model found")
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            
    def get_predictions(self, date: Optional[str] = None, use_live_odds: bool = True) -> List[Dict[str, Any]]:
        """
        Generate predictions for a given date (default: today).
        
        Args:
            date: YYYY-MM-DD string (optional)
            use_live_odds: Whether to fetch live odds from API
            
        Returns:
            List of prediction dictionaries
        """
        if not self.trainer or not self.trainer.xgb_calibrated:
            logger.error("Cannot predict: Models not loaded")
            return []

        # 1. Fetch Odds / Schedule Data
        odds_data = None
        if use_live_odds:
            logger.info("Fetching live odds...")
            odds_data = get_live_odds_data()
            
        # Fallback if live fetch failed or empty
        if not odds_data or not odds_data.get('endpoints', {}).get('nba_odds'):
            logger.info("Falling back to static/local betting data")
            odds_data = load_betting_data()
            
        if not odds_data:
            logger.error("No betting data available")
            return []
            
        # 2. Create Base Features from Odds
        df = create_features_from_odds(odds_data)
        
        if df.empty:
            logger.warning("No games found to predict")
            return []
            
        # Filter by date if provided (assuming df has a date column, if not we might predict all available)
        # Note: create_features_from_odds typically returns upcoming games. 
        # For strict date filtering, we'd need to check the 'date' or 'commence_time' column.
        if date:
            # Simple string match if date column exists and is string format YYYY-MM-DD
            if 'date' in df.columns:
                 df = df[df['date'].astype(str).str.startswith(date)]
        
        if df.empty:
            logger.warning(f"No games found for date {date}")
            return []

        # 3. Engineer Advanced Features
        if self.feature_engineer:
            model_features = self.trainer.feature_names
            X_model = self.feature_engineer.create_live_features(df, model_features)
            
            # 4. Generate Predictions
            X_input = X_model.drop(columns=['game_id'])
            ensemble_probs = self.trainer.predict_ensemble(X_input)
            
            # 5. Blend with Implied Probabilities
            implied_probs = df['home_implied_prob'].values
            
            # Dynamic blending based on model variance
            model_variance = np.var(ensemble_probs)
            if model_variance < 0.01:
                # Conservative: 30% Model, 70% Vegas
                blended_probs = 0.3 * np.array(ensemble_probs) + 0.7 * np.array(implied_probs)
            else:
                # Aggressive: 60% Model, 40% Vegas
                blended_probs = 0.6 * np.array(ensemble_probs) + 0.4 * np.array(implied_probs)
                
            # 6. Apply Chemistry Adjustments
            try:
                from src.models.chemistry_gnn import get_chemistry_model
                chem_model = get_chemistry_model()
                
                if chem_model and chem_model.loaded:
                    # Vectorized chemistry adjustment using apply instead of iterrows()
                    chem_adjustments = df.apply(
                        lambda row: chem_model.get_chemistry_differential(
                            row['home_team'], row['away_team']
                        ) * 0.1,
                        axis=1
                    ).values
                    
                    blended_probs = blended_probs + chem_adjustments
                    blended_probs = np.clip(blended_probs, 0.05, 0.95)
                    logger.info(f"Applied chemistry adjustments to {len(df)} games")
            except Exception as e:
                logger.warning(f"Failed to apply chemistry adjustment: {e}")

            # 7. Format Results
            results = []
            
            # Get individual model votes for transparency
            xgb_p = self.trainer.xgb_calibrated.predict_proba(X_input)[:, 1]
            lgb_p = self.trainer.lgb_calibrated.predict_proba(X_input)[:, 1]
            cat_p = self.trainer.cat_calibrated.predict_proba(X_input)[:, 1]
            
            # Use to_dict('records') instead of iterrows() for ~10x faster iteration
            df_records = df.to_dict('records')
            
            for idx, row in enumerate(df_records):
                prob = blended_probs[idx]
                prediction = "HOME_WIN" if prob > 0.5 else "AWAY_WIN"
                # Change confidence to be the winner's probability (50-100 scale)
                # Old metric was margin (0-100), which confused users
                confidence = max(prob, 1 - prob) * 100
                
                # Individual votes
                votes = {
                    "XGBoost": "HOME" if xgb_p[idx] > 0.5 else "AWAY",
                    "LightGBM": "HOME" if lgb_p[idx] > 0.5 else "AWAY",
                    "CatBoost": "HOME" if cat_p[idx] > 0.5 else "AWAY"
                }
                
                result = {
                    "game_id": row['game_id'],
                    "date": row.get('date', datetime.now().strftime('%Y-%m-%d')),
                    "commence_time": row.get('commence_time', ''),
                    "home_team": row['home_team'],
                    "away_team": row['away_team'],
                    "prediction": prediction,
                    "home_win_probability": round(prob * 100, 2),
                    "away_win_probability": round((1 - prob) * 100, 2),
                    "confidence": round(confidence, 2),
                    "home_odds": row.get('home_odds_avg', 0),
                    "away_odds": row.get('away_odds_avg', 0),
                    "home_spread": row.get('home_spread_avg', 0),
                    "away_spread": row.get('away_spread_avg', 0),
                    "individual_votes": votes,
                    "models_agree": "3/3", # Placeholder logic retained from API
                    "consensus_percentage": 100.0, # Placeholder
                    "model_version": "ensemble_v2_polyglot" 
                }
                results.append(result)
                
            return results

        return []
    async def get_predictions_async(self, date: Optional[str] = None, use_live_odds: bool = True) -> List[Dict[str, Any]]:
        """
        Async version of get_predictions.
        """
        if not self.trainer or not self.trainer.xgb_calibrated:
            logger.error("Cannot predict: Models not loaded")
            return []

        # 1. Fetch Odds / Schedule Data
        odds_data = None
        if use_live_odds:
            logger.info("Fetching live odds (async)...")
            odds_data = await get_live_odds_data_async()
            
        # Fallback if live fetch failed or empty (run in thread if it involves blocking I/O)
        if not odds_data or not odds_data.get('endpoints', {}).get('nba_odds'):
            logger.info("Falling back to static/local betting data")
            odds_data = await asyncio.to_thread(load_betting_data)
            
        if not odds_data:
            logger.error("No betting data available")
            return []
            
        # 2. Create Base Features from Odds
        # Running intensive data processing in thread to keep loop responsive
        df = await asyncio.to_thread(create_features_from_odds, odds_data)
        
        if df.empty:
            logger.warning("No games found to predict")
            return []
            
        if date and 'date' in df.columns:
            df = df[df['date'].astype(str).str.startswith(date)]
        
        if df.empty:
            logger.warning(f"No games found for date {date}")
            return []

        # 3. Engineer Advanced Features
        if self.feature_engineer:
            model_features = self.trainer.feature_names
            # Running intensive feature engineering in thread
            X_model = await asyncio.to_thread(self.feature_engineer.create_live_features, df, model_features)
            
            # 4. Generate Predictions
            X_input = X_model.drop(columns=['game_id'])
            # Most model predictions are CPU bound, could be threaded, but usually fast enough
            ensemble_probs = self.trainer.predict_ensemble(X_input)
            
            # 5. Blend with Implied Probabilities
            implied_probs = df['home_implied_prob'].values
            model_variance = np.var(ensemble_probs)
            if model_variance < 0.01:
                blended_probs = 0.3 * np.array(ensemble_probs) + 0.7 * np.array(implied_probs)
            else:
                blended_probs = 0.6 * np.array(ensemble_probs) + 0.4 * np.array(implied_probs)
                
            # 6. Apply Chemistry Adjustments
            try:
                from src.models.chemistry_gnn import get_chemistry_model
                chem_model = get_chemistry_model()
                if chem_model and chem_model.loaded:
                    chem_adjustments = df.apply(
                        lambda row: chem_model.get_chemistry_differential(
                            row['home_team'], row['away_team']
                        ) * 0.1,
                        axis=1
                    ).values
                    blended_probs = blended_probs + chem_adjustments
                    blended_probs = np.clip(blended_probs, 0.05, 0.95)
            except Exception as e:
                logger.warning(f"Failed to apply chemistry adjustment: {e}")

            # 7. Format Results
            results = []
            xgb_p = self.trainer.xgb_calibrated.predict_proba(X_input)[:, 1]
            lgb_p = self.trainer.lgb_calibrated.predict_proba(X_input)[:, 1]
            cat_p = self.trainer.cat_calibrated.predict_proba(X_input)[:, 1]
            
            df_records = df.to_dict('records')
            for idx, row in enumerate(df_records):
                prob = blended_probs[idx]
                prediction = "HOME_WIN" if prob > 0.5 else "AWAY_WIN"
                confidence = max(prob, 1 - prob) * 100
                votes = {
                    "XGBoost": "HOME" if xgb_p[idx] > 0.5 else "AWAY",
                    "LightGBM": "HOME" if lgb_p[idx] > 0.5 else "AWAY",
                    "CatBoost": "HOME" if cat_p[idx] > 0.5 else "AWAY"
                }
                result = {
                    "game_id": row['game_id'],
                    "date": row.get('date', datetime.now().strftime('%Y-%m-%d')),
                    "commence_time": row.get('commence_time', ''),
                    "home_team": row['home_team'],
                    "away_team": row['away_team'],
                    "prediction": prediction,
                    "home_win_probability": round(prob * 100, 2),
                    "away_win_probability": round((1 - prob) * 100, 2),
                    "confidence": round(confidence, 2),
                    "home_odds": row.get('home_odds_avg', 0),
                    "away_odds": row.get('away_odds_avg', 0),
                    "home_spread": row.get('home_spread_avg', 0),
                    "away_spread": row.get('away_spread_avg', 0),
                    "individual_votes": votes,
                    "models_agree": "3/3",
                    "consensus_percentage": 100.0,
                    "model_version": "ensemble_v2_polyglot"
                }
                results.append(result)
            return results
        return []
