"""
Tests for ML models
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.pregame.predictor import EnsemblePredictor
from src.common.paths import Paths


class TestEnsemblePredictor:
    """Test suite for EnsemblePredictor"""
    
    @pytest.fixture
    def predictor(self):
        """Load predictor for testing"""
        model_path = Paths.ARTIFACTS / "models" / "pregame"
        if not model_path.exists():
            pytest.skip("Model not found - run training first")
        
        # EnsemblePredictor loads models in __init__
        predictor = EnsemblePredictor(model_dir=str(model_path))
        return predictor
    
    @pytest.fixture
    def sample_features(self):
        """Create sample features for testing"""
        # Load a real feature row from historical data
        pregame_file = Paths.ARTIFACTS / "features" / "pregame.parquet"
        if not pregame_file.exists():
            pytest.skip("Feature file not found")
        
        df = pd.read_parquet(pregame_file)
        # Get a single row, remove outcome columns
        feature_cols = [col for col in df.columns if col not in [
            'game_id', 'date', 'home_team', 'away_team', 'season',
            'home_score', 'away_score', 'home_win', 'away_win', 'score_diff',
            'year', 'month', 'day_of_week'
        ]]
        
        sample = df[feature_cols].iloc[0:1]
        return sample
    
    def test_predictor_loads(self, predictor):
        """Test that predictor loads successfully"""
        assert predictor is not None
        # Check that all three models are loaded
        assert predictor.xgb_model is not None
        assert predictor.lgb_model is not None
        assert predictor.cat_model is not None
    
    def test_prediction_output_format(self, predictor, sample_features):
        """Test that predictions return correct format"""
        predictions = predictor.predict_with_features(sample_features, top_n=5)
        
        assert isinstance(predictions, list)
        assert len(predictions) == 1  # One prediction for one input row
        
        pred = predictions[0]
        assert 'prediction' in pred
        assert 'top_features' in pred
        
        # Check prediction is probability (0-1)
        assert 0 <= pred['prediction'] <= 1
        
        # Check top features format
        assert isinstance(pred['top_features'], list)
        assert len(pred['top_features']) <= 5
        
        if len(pred['top_features']) > 0:
            feature = pred['top_features'][0]
            assert 'feature' in feature
            assert 'importance' in feature
            assert 'value' in feature
    
    def test_prediction_consistency(self, predictor, sample_features):
        """Test that same input produces same output"""
        pred1 = predictor.predict_with_features(sample_features, top_n=3)
        pred2 = predictor.predict_with_features(sample_features, top_n=3)
        
        assert pred1[0]['prediction'] == pred2[0]['prediction']
    
    def test_multiple_predictions(self, predictor):
        """Test predicting on multiple games"""
        pregame_file = Paths.ARTIFACTS / "features" / "pregame.parquet"
        df = pd.read_parquet(pregame_file)
        
        feature_cols = [col for col in df.columns if col not in [
            'game_id', 'date', 'home_team', 'away_team', 'season',
            'home_score', 'away_score', 'home_win', 'away_win', 'score_diff',
            'year', 'month', 'day_of_week'
        ]]
        
        sample = df[feature_cols].head(10)
        predictions = predictor.predict_with_features(sample, top_n=3)
        
        assert len(predictions) == 10
        
        # Check all predictions are valid probabilities
        for pred in predictions:
            assert 0 <= pred['prediction'] <= 1
    
    def test_edge_cases(self, predictor, sample_features):
        """Test edge cases"""
        # Test with all zeros
        zeros = sample_features.copy()
        zeros[:] = 0
        
        try:
            predictions = predictor.predict_with_features(zeros, top_n=3)
            # Should still return valid probability
            assert 0 <= predictions[0]['prediction'] <= 1
        except Exception as e:
            pytest.fail(f"Failed on all-zero input: {e}")
        
        # Test with very large values
        large = sample_features.copy()
        large[:] = 1000
        
        try:
            predictions = predictor.predict_with_features(large, top_n=3)
            assert 0 <= predictions[0]['prediction'] <= 1
        except Exception as e:
            pytest.fail(f"Failed on large values: {e}")


class TestModelPerformance:
    """Test model performance metrics"""
    
    def test_accuracy_threshold(self):
        """Test that model meets minimum accuracy threshold"""
        model_meta_path = Paths.ARTIFACTS / "models" / "pregame" / "metadata.json"
        
        if not model_meta_path.exists():
            pytest.skip("Model metadata not found")
        
        import json
        with open(model_meta_path, 'r') as f:
            metadata = json.load(f)
        
        # Check that at least one model has >60% accuracy
        has_good_model = False
        for model_name, model_info in metadata.get('models', {}).items():
            accuracy = model_info.get('accuracy', 0)
            if accuracy > 0.60:
                has_good_model = True
                break
        
        assert has_good_model, "No model achieves >60% accuracy"
    
    def test_auc_threshold(self):
        """Test that model meets minimum AUC threshold"""
        model_meta_path = Paths.ARTIFACTS / "models" / "pregame" / "metadata.json"
        
        if not model_meta_path.exists():
            pytest.skip("Model metadata not found")
        
        import json
        with open(model_meta_path, 'r') as f:
            metadata = json.load(f)
        
        # Check that at least one model has >0.85 AUC
        has_good_auc = False
        for model_name, model_info in metadata.get('models', {}).items():
            auc = model_info.get('auc', 0)
            if auc > 0.85:
                has_good_auc = True
                break
        
        assert has_good_auc, "No model achieves >0.85 AUC"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
