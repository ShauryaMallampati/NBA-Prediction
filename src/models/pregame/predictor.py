"""
Ensemble predictor for loading and using trained models
"""
import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np


class EnsemblePredictor:
    """Load and use trained ensemble models for prediction"""
    
    def __init__(self, model_dir: str = "artifacts/models/pregame"):
        """
        Initialize predictor by loading models
        
        Args:
            model_dir: Directory containing saved model files
        """
        self.model_dir = Path(model_dir)
        self.xgb_model = None
        self.lgb_model = None
        self.cat_model = None
        self.weights = None
        self.feature_names = None
        self.metadata = None
        
        self._load_models()
    
    async def load_async(self):
        """Async version of model loading"""
        import asyncio
        metadata_path = self.model_dir / "ensemble_metadata.json"
        
        async def read_json():
            with open(metadata_path, 'r') as f:
                return json.load(f)
        
        self.metadata = await asyncio.to_thread(read_json)
        self.weights = self.metadata['weights']
        self.feature_names = self.metadata['feature_names']
        
        async def read_pickle(path):
            with open(path, 'rb') as f:
                return pickle.load(f)
        
        self.xgb_model = await asyncio.to_thread(read_pickle, self.model_dir / "xgb_model.pkl")
        self.lgb_model = await asyncio.to_thread(read_pickle, self.model_dir / "lgb_model.pkl")
        self.cat_model = await asyncio.to_thread(read_pickle, self.model_dir / "cat_model.pkl")

    def _load_models(self):
        """Load all model files (sync version)"""
        # Load metadata
        metadata_path = self.model_dir / "ensemble_metadata.json"
        if not metadata_path.exists():
            return # Silent fail for initialization, caller should check models
        
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
        
        self.weights = self.metadata['weights']
        self.feature_names = self.metadata['feature_names']
        
        # Load models
        with open(self.model_dir / "xgb_model.pkl", 'rb') as f:
            self.xgb_model = pickle.load(f)
        
        with open(self.model_dir / "lgb_model.pkl", 'rb') as f:
            self.lgb_model = pickle.load(f)
        
        with open(self.model_dir / "cat_model.pkl", 'rb') as f:
            self.cat_model = pickle.load(f)
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict win probabilities using ensemble
        
        Args:
            X: Feature DataFrame with shape (n_games, n_features)
        
        Returns:
            Array of home team win probabilities (shape: n_games)
        """
        # Ensure we have the right features in the right order
        if not all(col in X.columns for col in self.feature_names):
            missing = set(self.feature_names) - set(X.columns)
            raise ValueError(f"Missing features: {missing}")
        
        X_ordered = X[self.feature_names].fillna(0)
        
        # Get predictions from each model
        xgb_proba = self.xgb_model.predict_proba(X_ordered)[:, 1]
        lgb_proba = self.lgb_model.predict_proba(X_ordered)[:, 1]
        cat_proba = self.cat_model.predict_proba(X_ordered)[:, 1]
        
        # Weighted ensemble
        ensemble_proba = (
            self.weights['xgb'] * xgb_proba +
            self.weights['lgb'] * lgb_proba +
            self.weights['cat'] * cat_proba
        )
        
        return ensemble_proba
    
    def predict_with_features(
        self, X: pd.DataFrame, top_n: int = 5
    ) -> List[Dict]:
        """
        Predict with feature importance explanation
        
        Args:
            X: Feature DataFrame
            top_n: Number of top features to return
        
        Returns:
            List of predictions with feature importance
        """
        predictions = self.predict(X)
        
        # Get feature importance from LightGBM (usually most interpretable)
        # Handle both calibrated and uncalibrated models
        lgb_base = self.lgb_model
        if hasattr(self.lgb_model, 'calibrated_classifiers_'):
            # If calibrated, get the base estimator
            lgb_base = self.lgb_model.calibrated_classifiers_[0].estimator
        
        feature_importance = lgb_base.feature_importances_
        
        # Sort features by importance
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': feature_importance
        }).sort_values('importance', ascending=False)
        
        results = []
        for i, prob in enumerate(predictions):
            # Get top features for this specific game
            game_features = X.iloc[i][self.feature_names]
            
            # Calculate contribution (feature value * importance)
            contributions = []
            
            # Use to_dict('records') instead of iterrows() for performance
            importance_records = importance_df.head(top_n).to_dict('records')
            
            for row in importance_records:
                feat = row['feature']
                importance = row['importance']
                value = game_features[feat]
                contributions.append({
                    'feature': feat,
                    'importance': float(importance),
                    'value': float(value)
                })
            
            results.append({
                'prediction': float(prob),
                'top_features': contributions
            })
        
        return results
    
    def get_model_info(self) -> Dict:
        """Get metadata about the loaded models"""
        return {
            'feature_count': len(self.feature_names),
            'features': self.feature_names,
            'weights': self.weights,
            'metrics': {
                'xgb': {
                    'accuracy': self.metadata['metrics']['xgb']['accuracy'],
                    'auc': self.metadata['metrics']['xgb']['auc'],
                },
                'lgb': {
                    'accuracy': self.metadata['metrics']['lgb']['accuracy'],
                    'auc': self.metadata['metrics']['lgb']['auc'],
                },
                'cat': {
                    'accuracy': self.metadata['metrics']['cat']['accuracy'],
                    'auc': self.metadata['metrics']['cat']['auc'],
                },
                'ensemble': {
                    'accuracy': self.metadata['metrics']['ensemble']['accuracy'],
                    'auc': self.metadata['metrics']['ensemble']['auc'],
                }
            },
            'timestamp': self.metadata['timestamp']
        }
