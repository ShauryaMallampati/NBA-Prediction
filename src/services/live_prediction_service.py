"""
Live Prediction Service - Integrates models, features, odds, and risk assessment
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.data.ingest.live_feature_extractor import LiveFeatureExtractor


class LivePredictionService:
    """Real-time prediction service for NBA player props."""
    
    def __init__(self):
        """Initialize with trained models and feature extractor."""
        self.feature_extractor = LiveFeatureExtractor()
        self.models = {}
        self.calibrators = {}
        self._load_models()
        
    def _load_models(self):
        """Load trained LightGBM models and calibrators."""
        model_dir = Path('artifacts/models/pregame')
        
        for stat in ['PTS', 'AST', 'REB', 'STL', 'BLK']:
            model_path = model_dir / f'{stat.lower()}_model.pkl'
            calib_path = model_dir / f'{stat.lower()}_calibrator.pkl'
            
            if model_path.exists():
                with open(model_path, 'rb') as f:
                    self.models[stat] = pickle.load(f)
                logger.info(f"  ✅ Loaded {stat} model")
            
            if calib_path.exists():
                with open(calib_path, 'rb') as f:
                    self.calibrators[stat] = pickle.load(f)
        
        if self.models:
            logger.info(f"✅ Loaded {len(self.models)} models ready for inference")
    
    def predict_player_prop(self, player_data: Dict) -> Dict:
        """
        Make real-time prediction for a player prop.
        
        Returns:
            {
                'player_name': str,
                'predictions': {
                    'PTS': {'raw': float, 'calibrated': float, 'over': bool, 'confidence': float},
                    'AST': {...},
                    ...
                },
                'ready_for_production': bool
            }
        """
        try:
            # Extract features
            features_df = self.feature_extractor.extract_features(player_data)
            features_array = features_df.values.astype(np.float32)
            
            predictions = {}
            
            # Get predictions for each stat
            for stat in ['PTS', 'AST', 'REB', 'STL', 'BLK']:
                if stat not in self.models:
                    logger.warning(f"Model for {stat} not found")
                    continue
                
                model = self.models[stat]
                calibrator = self.calibrators[stat]
                
                # Get raw prediction
                try:
                    pred_raw = model.predict(features_array, num_iteration=model.best_iteration)[0]
                except:
                    pred_raw = 0.5  # Fallback
                
                # Calibrate - IsotonicRegression.predict expects 1D array or 2D array (n_samples, 1)
                try:
                    pred_calib = float(calibrator.predict(np.array([pred_raw]))[0])
                except:
                    # Fallback if calibrator fails
                    pred_calib = pred_raw
                
                predictions[stat] = {
                    'raw': float(pred_raw),
                    'calibrated': float(pred_calib),
                    'over': pred_calib > 0.5,
                    'confidence': abs(pred_calib - 0.5) * 2,  # 0-1 scale
                }
            
            return {
                'player_name': player_data.get('player_name', 'Unknown'),
                'predictions': predictions,
                'ready_for_production': len(predictions) == 5,
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return {
                'player_name': player_data.get('player_name', 'Unknown'),
                'predictions': {},
                'ready_for_production': False,
                'error': str(e),
            }


if __name__ == "__main__":
    print("\n" + "="*80)
    print("LIVE PREDICTION SERVICE TEST")
    print("="*80)
    
    service = LivePredictionService()
    
    if not service.models:
        print("❌ No models loaded!")
    else:
        print(f"✅ Service initialized with {len(service.models)} models\n")
        
        # Test prediction
        sample_player = {
            'player_name': 'LeBron James',
            'is_home': True,
            'rest_days': 2,
            'is_back_to_back': False,
            'FG_pct': 0.50,
            'FG3_pct': 0.38,
            'FT_pct': 0.73,
            'usage_pct': 0.28,
            'games_played': 15,
            'consistency_score': 0.85,
            'recent_stats': {
                'PTS_3game': 25.3, 'PTS_7game': 24.8, 'PTS_7game_std': 2.1,
                'AST_3game': 7.2, 'AST_7game': 7.0, 'AST_7game_std': 0.9,
                'REB_3game': 7.8, 'REB_7game': 7.5, 'REB_7game_std': 1.2,
                'STL_3game': 1.3, 'STL_7game': 1.2, 'STL_7game_std': 0.3,
                'BLK_3game': 0.7, 'BLK_7game': 0.65, 'BLK_7game_std': 0.2,
                'PTS_trend': 0.5, 'AST_trend': 0.3, 'REB_trend': -0.2,
            },
            'season_stats': {
                'PTS_avg': 24.5, 'AST_avg': 6.8, 'REB_avg': 7.2,
                'STL_avg': 1.1, 'BLK_avg': 0.6,
            },
            'opponent_defense': {
                'def_PTS_allowed': 108, 'def_AST_allowed': 26, 'def_REB_allowed': 44,
                'def_STL_allowed': 7.5, 'def_BLK_allowed': 4.8,
            }
        }
        
        result = service.predict_player_prop(sample_player)
        
        print(f"🎯 Predictions for {result['player_name']}:")
        for stat, pred in result['predictions'].items():
            direction = "OVER" if pred['over'] else "UNDER"
            conf = pred['confidence']
            print(f"   {stat}: {direction} @ {pred['calibrated']:.1%} (conf: {conf:.0%})")
        
        print(f"\n✅ Service ready: {result['ready_for_production']}")
