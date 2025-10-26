"""
Test suite for LightGBM Player Props Model (Task #15)

Tests:
  1. Model training with synthetic data
  2. Calibration verification
  3. SHAP value generation
  4. Prediction accuracy on test set
  5. Model serialization/deserialization
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import pathlib
from datetime import datetime, timedelta
import sys

# Add src to path
src_path = pathlib.Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from models.pregame.train_props_model import PlayerPropsLightGBMTrainer


@pytest.fixture
def synthetic_features():
    """Generate synthetic player props features for testing."""
    np.random.seed(42)
    n_samples = 1000
    
    dates = [datetime(2019, 10, 1) + timedelta(days=i) for i in range(n_samples)]
    
    data = {
        'date': dates,
        'player_name': np.random.choice(['LeBron', 'Luka', 'Giannis', 'Jokic', 'Durant'], n_samples),
        'team': np.random.choice(['LAL', 'DAL', 'MIL', 'DEN', 'PHX'], n_samples),
        'opponent': np.random.choice(['BOS', 'GSW', 'LAC', 'MIA', 'NYK'], n_samples),
        
        # Player performance features (20 total)
        'pts_avg_season': np.random.normal(20, 5, n_samples),
        'pts_avg_recent': np.random.normal(19, 6, n_samples),
        'pts_trend': np.random.normal(0, 3, n_samples),
        'pts_consistency': np.random.uniform(0.5, 1.0, n_samples),
        
        'ast_avg_season': np.random.normal(5, 2, n_samples),
        'ast_avg_recent': np.random.normal(5.5, 2.5, n_samples),
        'ast_trend': np.random.normal(0, 1, n_samples),
        'ast_consistency': np.random.uniform(0.5, 1.0, n_samples),
        
        'reb_avg_season': np.random.normal(7, 2, n_samples),
        'reb_avg_recent': np.random.normal(7.2, 2.5, n_samples),
        'reb_trend': np.random.normal(0, 1.5, n_samples),
        'reb_consistency': np.random.uniform(0.5, 1.0, n_samples),
        
        'stl_avg_season': np.random.normal(1.2, 0.5, n_samples),
        'stl_avg_recent': np.random.normal(1.3, 0.6, n_samples),
        'stl_trend': np.random.normal(0, 0.3, n_samples),
        'stl_consistency': np.random.uniform(0.5, 1.0, n_samples),
        
        'blk_avg_season': np.random.normal(1.0, 0.5, n_samples),
        'blk_avg_recent': np.random.normal(1.1, 0.6, n_samples),
        'blk_trend': np.random.normal(0, 0.3, n_samples),
        'blk_consistency': np.random.uniform(0.5, 1.0, n_samples),
        
        # Load management (8 features)
        'on_games': np.random.randint(0, 10, n_samples),
        'off_games': np.random.randint(0, 5, n_samples),
        'rest_risk': np.random.uniform(0, 1, n_samples),
        'recent_ppg': np.random.normal(19, 7, n_samples),
        'back_to_back': np.random.choice([0, 1], n_samples),
        'load_consistency': np.random.uniform(0.5, 1.0, n_samples),
        'rest_pattern': np.random.uniform(0, 1, n_samples),
        'load_trend': np.random.normal(0, 0.5, n_samples),
        
        # Travel & Fatigue (8 features)
        'distance_miles': np.random.uniform(0, 2500, n_samples),
        'timezone_diff': np.random.choice([-3, -2, -1, 0, 1, 2, 3], n_samples),
        'fatigue_score': np.random.uniform(0, 100, n_samples),
        'minutes_yesterday': np.random.uniform(0, 40, n_samples),
        'arena_change': np.random.choice([0, 1], n_samples),
        'travel_risk': np.random.uniform(0, 1, n_samples),
        'travel_fatigue': np.random.normal(0, 0.3, n_samples),
        'altitude_change': np.random.uniform(0, 1, n_samples),
        
        # Actual targets (will be binarized)
        'PTS_actual': np.random.normal(20, 6, n_samples),
        'AST_actual': np.random.normal(5, 2.5, n_samples),
        'REB_actual': np.random.normal(7, 2.5, n_samples),
        'STL_actual': np.random.normal(1.2, 0.8, n_samples),
        'BLK_actual': np.random.normal(1.0, 0.7, n_samples),
    }
    
    df = pd.DataFrame(data)
    return df


def test_model_initialization():
    """Test trainer initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trainer = PlayerPropsLightGBMTrainer(output_dir=tmpdir)
        
        assert trainer.output_dir == pathlib.Path(tmpdir)
        assert len(trainer.stats_to_predict) == 5
        assert "PTS" in trainer.stats_to_predict


def test_train_all_models(synthetic_features):
    """Test training all 5 models."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trainer = PlayerPropsLightGBMTrainer(output_dir=tmpdir)
        
        # Train models (data spans 2019-2022)
        results = trainer.train_all_models(
            synthetic_features,
            test_year=2022,
            val_year=2021,
        )
        
        # Verify all stats trained
        assert len(results) > 0
        for stat in ["PTS", "AST", "REB", "STL", "BLK"]:
            if stat in results:
                assert "auc_calibrated" in results[stat]
                assert "accuracy_calibrated" in results[stat]
                assert results[stat]["auc_calibrated"] > 0.5  # Better than random


def test_calibration(synthetic_features):
    """Test that calibration improves Brier score."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trainer = PlayerPropsLightGBMTrainer(output_dir=tmpdir)
        
        results = trainer.train_all_models(synthetic_features, test_year=2022, val_year=2021)
        
        # For any stat, calibrated Brier score should be lower (better)
        for stat, metrics in results.items():
            brier_uncal = metrics["brier_uncalibrated"]
            brier_cal = metrics["brier_calibrated"]
            
            # Calibration should improve (lower Brier score)
            assert brier_cal <= brier_uncal + 0.01  # Allow small tolerance


def test_predictions(synthetic_features):
    """Test that predictions work."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trainer = PlayerPropsLightGBMTrainer(output_dir=tmpdir)
        
        # Train
        trainer.train_all_models(synthetic_features, test_year=2022, val_year=2021)
        
        # Get feature columns
        feature_cols = [col for col in synthetic_features.columns 
                       if not col.startswith(('date', 'year', '_actual', 'player_name', 'team', 'opponent'))]
        X_test = synthetic_features[feature_cols].iloc[:100]
        
        # Make predictions
        for stat in ["PTS", "AST", "REB", "STL", "BLK"]:
            preds = trainer.predict(X_test, stat=stat, calibrated=True)
            
            assert len(preds) == 100
            assert np.all(preds >= 0) and np.all(preds <= 1)  # Probabilities


def test_model_serialization(synthetic_features):
    """Test that models are saved and loadable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trainer = PlayerPropsLightGBMTrainer(output_dir=tmpdir)
        
        # Train
        trainer.train_all_models(synthetic_features, test_year=2022, val_year=2021)
        
        # Verify files exist
        output_dir = pathlib.Path(tmpdir)
        for stat in ["PTS", "AST", "REB", "STL", "BLK"]:
            model_file = output_dir / f"{stat.lower()}_model.pkl"
            calibrator_file = output_dir / f"{stat.lower()}_calibrator.pkl"
            
            assert model_file.exists() or (output_dir / f"{stat.lower()}_model.txt").exists()
            assert calibrator_file.exists()


def test_shap_values(synthetic_features):
    """Test SHAP value generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trainer = PlayerPropsLightGBMTrainer(output_dir=tmpdir)
        
        # Train
        trainer.train_all_models(synthetic_features, test_year=2022, val_year=2021)
        
        # Get feature columns and sample
        feature_cols = [col for col in synthetic_features.columns 
                       if not col.startswith(('date', 'year', '_actual', 'player_name', 'team', 'opponent'))]
        X_sample = synthetic_features[feature_cols].iloc[:10]
        
        # Generate SHAP values
        for stat in ["PTS", "AST", "REB"]:
            shap_vals = trainer.generate_shap_values(stat, X_sample)
            
            if shap_vals is not None:
                assert shap_vals.shape[0] == 10
                assert shap_vals.shape[1] == len(feature_cols)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
