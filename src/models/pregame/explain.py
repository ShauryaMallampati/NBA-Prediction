"""Use SHAP to explain why our model makes each prediction.

Instead of just giving you a prediction, we break down which features
were most important for that specific game.
"""

import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP not available. Install with: pip install shap")

from .ensemble_predictor import get_ensemble_predictor

logger = logging.getLogger(__name__)


class SHAPExplainer:
    """Break down predictions using SHAP values."""
    
    def __init__(self, model_dir: str = "artifacts/models/pregame"):
        """Set up the SHAP explainer."""
        self.model_dir = Path(model_dir)
        self.explainer = None
        self.feature_names = None
        self.loaded = False
        
        if not SHAP_AVAILABLE:
            logger.warning("SHAP not available. Explanations will be limited.")
        
        logger.info("🔍 SHAP explainer initialized")
    
    def load_model(self):
        """Load the trained model so we can explain its predictions."""
        if self.loaded:
            return
        
        if not SHAP_AVAILABLE:
            logger.warning("SHAP not available, skipping model loading")
            return
        
        try:
            # Load ensemble predictor
            predictor = get_ensemble_predictor()
            predictor.load_models()
            
            # Get feature names
            self.feature_names = predictor.trainer.feature_names
            
            # Create SHAP explainer (TreeExplainer for tree-based models)
            if predictor.trainer.xgb_calibrated is not None:
                # Use XGBoost model for SHAP (most interpretable)
                model = predictor.trainer.xgb_model
                if model is not None:
                    self.explainer = shap.TreeExplainer(model)
                    self.loaded = True
                    logger.info("✅ SHAP explainer loaded")
                else:
                    logger.warning("XGBoost model not available for SHAP")
            else:
                logger.warning("No model available for SHAP")
                
        except Exception as e:
            logger.error(f"Error loading SHAP explainer: {e}")
    
    def explain_prediction(self, X: pd.DataFrame, game_id: Optional[str] = None) -> Dict:
        """
        Generate SHAP explanation for a prediction.
        
        Args:
            X: Feature vector (single row)
            game_id: Game ID (optional)
        
        Returns:
            Dictionary with SHAP values and explanation
        """
        if not SHAP_AVAILABLE:
            return {
                'error': 'SHAP not available',
                'shap_values': {},
                'explanation': 'SHAP explanations require shap package',
            }
        
        if not self.loaded:
            self.load_model()
        
        if self.explainer is None:
            return {
                'error': 'SHAP explainer not available',
                'shap_values': {},
                'explanation': 'Model not loaded',
            }
        
        try:
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(X)
            
            # Get feature importance (absolute SHAP values)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Positive class
            
            # Create feature importance dictionary
            feature_importance = {}
            for i, feature in enumerate(self.feature_names):
                if i < len(shap_values[0]):
                    feature_importance[feature] = float(shap_values[0][i])
            
            # Sort by absolute value
            sorted_features = sorted(
                feature_importance.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            
            # Get top 5 features
            top_features = sorted_features[:5]
            
            # Generate explanation text
            explanation_parts = []
            for feature, value in top_features:
                if value > 0:
                    explanation_parts.append(f"{feature}: +{value:.3f}")
                else:
                    explanation_parts.append(f"{feature}: {value:.3f}")
            
            explanation = "Top factors: " + ", ".join(explanation_parts)
            
            return {
                'shap_values': dict(feature_importance),
                'top_features': [{'feature': f, 'value': v} for f, v in top_features],
                'explanation': explanation,
                'game_id': game_id,
            }
            
        except Exception as e:
            logger.error(f"Error generating SHAP explanation: {e}")
            return {
                'error': str(e),
                'shap_values': {},
                'explanation': f'Error: {e}',
            }
    
    def explain_game(self, features: Dict, game_id: Optional[str] = None) -> Dict:
        """
        Explain a game prediction.
        
        Args:
            features: Dictionary with feature values
            game_id: Game ID (optional)
        
        Returns:
            Dictionary with SHAP explanation
        """
        if not SHAP_AVAILABLE:
            return {
                'error': 'SHAP not available',
                'shap_values': {},
                'explanation': 'SHAP explanations require shap package',
            }
        
        if not self.loaded:
            self.load_model()
        
        if self.explainer is None or self.feature_names is None:
            return {
                'error': 'SHAP explainer not available',
                'shap_values': {},
                'explanation': 'Model not loaded',
            }
        
        try:
            # Convert features to dataframe
            feature_vector = pd.DataFrame([features])
            
            # Ensure all features are present
            for feature in self.feature_names:
                if feature not in feature_vector.columns:
                    feature_vector[feature] = 0  # Default value
            
            # Select only required features
            feature_vector = feature_vector[self.feature_names]
            
            # Generate explanation
            explanation = self.explain_prediction(feature_vector, game_id)
            
            return explanation
            
        except Exception as e:
            logger.error(f"Error explaining game: {e}")
            return {
                'error': str(e),
                'shap_values': {},
                'explanation': f'Error: {e}',
            }
    
    def get_global_feature_importance(self, X: pd.DataFrame, n_samples: int = 100) -> Dict:
        """
        Get global feature importance using SHAP.
        
        Args:
            X: Feature matrix
            n_samples: Number of samples to use for SHAP (for speed)
        
        Returns:
            Dictionary with global feature importance
        """
        if not SHAP_AVAILABLE:
            return {'error': 'SHAP not available'}
        
        if not self.loaded:
            self.load_model()
        
        if self.explainer is None:
            return {'error': 'SHAP explainer not available'}
        
        try:
            # Sample data for speed
            if len(X) > n_samples:
                X_sample = X.sample(n=n_samples, random_state=42)
            else:
                X_sample = X
            
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(X_sample)
            
            # Get feature importance (mean absolute SHAP values)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Positive class
            
            # Calculate mean absolute SHAP values
            mean_shap = np.abs(shap_values).mean(axis=0)
            
            # Create feature importance dictionary
            feature_importance = {}
            for i, feature in enumerate(self.feature_names):
                if i < len(mean_shap):
                    feature_importance[feature] = float(mean_shap[i])
            
            # Sort by importance
            sorted_features = sorted(
                feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return {
                'feature_importance': dict(feature_importance),
                'top_features': [{'feature': f, 'importance': v} for f, v in sorted_features[:10]],
            }
            
        except Exception as e:
            logger.error(f"Error calculating global feature importance: {e}")
            return {'error': str(e)}


# Singleton instance
_explainer: Optional[SHAPExplainer] = None


def get_shap_explainer() -> SHAPExplainer:
    """Get or create SHAP explainer instance."""
    global _explainer
    if _explainer is None:
        _explainer = SHAPExplainer()
    return _explainer


if __name__ == "__main__":
    # Example usage
    explainer = get_shap_explainer()
    
    # Example features
    features = {
        'elo_home': 1600,
        'elo_away': 1550,
        'home_adv_flag': 1,
        # ... other features
    }
    
    # Explain prediction
    explanation = explainer.explain_game(features, game_id="test_game")
    print(f"Explanation: {explanation}")

