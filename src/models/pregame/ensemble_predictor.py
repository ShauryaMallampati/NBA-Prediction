"""
"""Use our trained ensemble to predict NBA games.

Loads the three models (XGBoost, LightGBM, CatBoost) and combines
their predictions with optimal weights.
"""

import pickle
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

import pandas as pd
import numpy as np

from .train_ensemble import EnsembleTrainer

logger = logging.getLogger(__name__)


class EnsemblePredictor:
    """Make predictions using the full ensemble."""
    
    def __init__(self, model_dir: str = "artifacts/models/pregame"):
        """Set up the ensemble predictor."""
        self.model_dir = Path(model_dir)
        self.trainer = EnsembleTrainer(output_dir=str(self.model_dir))
        self.loaded = False
        logger.info("🎯 Ensemble predictor initialized")
    
    def load_models(self):
        """Load trained models."""
        if self.loaded:
            return
        
        logger.info("📂 Loading ensemble models...")
        self.trainer.load_models()
        self.loaded = True
        logger.info("✅ Models loaded")
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make ensemble prediction.
        
        Args:
            X: Features dataframe
        
        Returns:
            Predictions (probabilities)
        """
        if not self.loaded:
            self.load_models()
        
        if self.trainer.xgb_calibrated is None:
            raise ValueError("Models not loaded. Train models first.")
        
        # Make ensemble prediction
        predictions = self.trainer.predict_ensemble(X)
        
        return predictions
    
    def predict_game(self, features: Dict) -> Dict:
        """
        Predict a single game.
        
        Args:
            features: Dictionary with feature values
        
        Returns:
            Dictionary with prediction and confidence
        """
        if not self.loaded:
            self.load_models()
        
        # Convert features to dataframe
        if self.trainer.feature_names is None:
            raise ValueError("Feature names not available. Train models first.")
        
        # Create feature vector
        feature_vector = pd.DataFrame([features])
        
        # Ensure all features are present
        for feature in self.trainer.feature_names:
            if feature not in feature_vector.columns:
                feature_vector[feature] = 0  # Default value
        
        # Select only required features
        feature_vector = feature_vector[self.trainer.feature_names]
        
        # Make prediction
        prediction = self.predict(feature_vector)[0]
        
        return {
            'home_win_prob': float(prediction),
            'away_win_prob': float(1 - prediction),
            'confidence': abs(prediction - 0.5) * 2,  # 0-1 scale
        }
    
    def get_feature_importance(self) -> Dict:
        """
        Get feature importance from ensemble.
        
        Returns:
            Dictionary with feature importance for each model
        """
        if not self.loaded:
            self.load_models()
        
        importance = {}
        
        # XGBoost feature importance
        if self.trainer.xgb_model is not None:
            xgb_importance = self.trainer.xgb_model.feature_importances_
            importance['xgb'] = dict(zip(self.trainer.feature_names, xgb_importance))
        
        # LightGBM feature importance
        if self.trainer.lgb_model is not None:
            lgb_importance = self.trainer.lgb_model.feature_importance(importance_type='gain')
            importance['lgb'] = dict(zip(self.trainer.feature_names, lgb_importance))
        
        # CatBoost feature importance
        if self.trainer.cat_model is not None:
            cat_importance = self.trainer.cat_model.get_feature_importance()
            importance['cat'] = dict(zip(self.trainer.feature_names, cat_importance))
        
        # Ensemble feature importance (weighted average)
        if len(importance) > 0:
            ensemble_importance = {}
            for feature in self.trainer.feature_names:
                weighted_importance = (
                    self.trainer.weights['xgb'] * importance['xgb'].get(feature, 0) +
                    self.trainer.weights['lgb'] * importance['lgb'].get(feature, 0) +
                    self.trainer.weights['cat'] * importance['cat'].get(feature, 0)
                )
                ensemble_importance[feature] = weighted_importance
            
            importance['ensemble'] = ensemble_importance
        
        return importance


# Singleton instance
_predictor: Optional[EnsemblePredictor] = None


def get_ensemble_predictor() -> EnsemblePredictor:
    """Get or create ensemble predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = EnsemblePredictor()
        _predictor.load_models()
    return _predictor


if __name__ == "__main__":
    # Example usage
    predictor = get_ensemble_predictor()
    
    # Example features
    features = {
        'elo_home': 1600,
        'elo_away': 1550,
        'home_adv_flag': 1,
        # ... other features
    }
    
    # Make prediction
    prediction = predictor.predict_game(features)
    print(f"Prediction: {prediction}")

