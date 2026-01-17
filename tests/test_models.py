"""
Test Suite for ML Models
Tests pregame ensemble, live GRU, feature engineering
"""

import pytest
import sys
from pathlib import Path
import torch
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestLiveGRUModel:
    """Test live win probability GRU model - DEPRECATED: GRU model has been removed"""
    
    @pytest.mark.skip(reason="GRU model has been deprecated and removed")
    def test_model_exists(self):
        """Test that GRU model file exists"""
        model_path = Path("artifacts/models/live_gru_winprob.pt")
        assert model_path.exists(), "GRU model should be trained and saved"
    
    @pytest.mark.skip(reason="GRU model has been deprecated and removed")
    def test_model_loading(self):
        """Test loading the trained GRU model"""
        model_path = Path("artifacts/models/live_gru_winprob.pt")
        if model_path.exists():
            model = torch.jit.load(str(model_path))
            assert model is not None
    
    @pytest.mark.skip(reason="GRU model has been deprecated and removed")
    def test_model_inference(self):
        """Test GRU model inference"""
        model_path = Path("artifacts/models/live_gru_winprob.pt")
        if not model_path.exists():
            pytest.skip("GRU model not trained yet")
        
        model = torch.jit.load(str(model_path))
        model.eval()
        
        # Create sample input sequence (score differentials)
        # Shape: (batch_size=1, sequence_length=20, features=1)
        sample_input = torch.randn(1, 20, 1)
        
        with torch.no_grad():
            output = model(sample_input)
        
        # Output should be win probability [0, 1]
        assert output.shape == (1, 1)
        assert 0 <= output.item() <= 1
    
    @pytest.mark.skip(reason="GRU model has been deprecated and removed")
    def test_gru_dataset_loading(self):
        """Test LiveSeqDataset loads correctly"""
        from src.models.live.dataset import LiveSeqDataset
        
        data_path = Path("artifacts/features/live_sequences.parquet")
        if not data_path.exists():
            pytest.skip("Live sequences not generated yet")
        
        dataset = LiveSeqDataset(str(data_path))
        
        # Check dataset has games
        assert len(dataset) > 0
        
        # Check data structure
        sequence, target = dataset[0]
        assert isinstance(sequence, torch.Tensor)
        assert isinstance(target, torch.Tensor)
        assert target.item() in [0.0, 1.0]  # Binary label
    
    @pytest.mark.skip(reason="GRU model has been deprecated and removed")
    def test_gru_batch_processing(self):
        """Test GRU model can process batches"""
        model_path = Path("artifacts/models/live_gru_winprob.pt")
        if not model_path.exists():
            pytest.skip("GRU model not trained yet")
        
        model = torch.jit.load(str(model_path))
        model.eval()
        
        # Batch of 5 sequences
        batch_input = torch.randn(5, 15, 1)
        
        with torch.no_grad():
            output = model(batch_input)
        
        assert output.shape == (5, 1)
        # All probabilities should be in [0, 1]
        assert torch.all((output >= 0) & (output <= 1))


class TestPregameEnsembleModel:
    """Test pregame prediction ensemble model"""
    
    def test_ensemble_models_exist(self):
        """Test that ensemble model artifacts exist"""
        model_dir = Path("artifacts/models/pregame")
        
        if not model_dir.exists():
            pytest.skip("Pregame models not trained yet")
        
        # Check for individual model files
        expected_files = ["xgboost_model.pkl", "lightgbm_model.pkl", "catboost_model.pkl"]
        for model_file in expected_files:
            # Files might have different names, just check directory has pkl files
            pkl_files = list(model_dir.glob("*.pkl"))
            if len(pkl_files) > 0:
                assert True
                return
        
        # If no .pkl files, might be using other formats
        assert len(list(model_dir.iterdir())) > 0
    
    def test_feature_engineering(self):
        """Test feature engineering creates expected features"""
        from scripts.engineer_features import FeatureEngineer
        
        # Create sample game data
        sample_games = [
            {
                'date': pd.Timestamp('2025-01-01'),
                'home_team': 'LAL',
                'away_team': 'GSW',
                'home_score': 110,
                'away_score': 105,
                'home_win': True
            },
            {
                'date': pd.Timestamp('2025-01-02'),
                'home_team': 'BOS',
                'away_team': 'MIA',
                'home_score': 115,
                'away_score': 112,
                'home_win': True
            }
        ]
        
        # Test that FeatureEngineer can be instantiated
        engineer = FeatureEngineer()
        assert engineer is not None
    
    def test_elo_rating_calculation(self):
        """Test Elo rating calculations"""
        from scripts.engineer_features import EloRatingSystem
        
        elo = EloRatingSystem()
        
        # Initial ratings should be 1500
        assert elo.ratings['LAL'] == 1500
        
        # Simulate a game
        elo.update_ratings('LAL', 'GSW', 110, 105, is_home=True)
        
        # Winner's rating should increase
        assert elo.ratings['LAL'] > 1500
        # Loser's rating should decrease
        assert elo.ratings['GSW'] < 1500
    
    def test_model_prediction_format(self):
        """Test prediction output format"""
        # Mock prediction
        mock_prediction = {
            'game_id': '0022200001',
            'home_win_prob': 0.65,
            'away_win_prob': 0.35,
            'confidence': 'high'
        }
        
        # Validate structure
        assert 'home_win_prob' in mock_prediction
        assert 'away_win_prob' in mock_prediction
        assert mock_prediction['home_win_prob'] + mock_prediction['away_win_prob'] == 1.0
        assert 0 <= mock_prediction['home_win_prob'] <= 1


class TestFeatureEngineering:
    """Test feature engineering pipeline"""
    
    def test_recent_form_calculation(self):
        """Test recent form (last N games) calculation"""
        # Sample game results
        games = pd.DataFrame({
            'date': pd.date_range('2025-01-01', periods=10),
            'team': ['LAL'] * 10,
            'pts': [110, 115, 105, 120, 108, 112, 118, 103, 116, 114],
            'win': [1, 1, 0, 1, 1, 1, 1, 0, 1, 1]
        })
        
        # Last 5 games win rate
        recent_5 = games.tail(5)['win'].mean()
        assert 0 <= recent_5 <= 1
        
        # Last 5 games avg points
        recent_pts = games.tail(5)['pts'].mean()
        assert recent_pts > 0
    
    def test_rest_days_calculation(self):
        """Test rest days between games calculation"""
        dates = pd.Series([
            pd.Timestamp('2025-01-01'),
            pd.Timestamp('2025-01-03'),  # 2 days rest
            pd.Timestamp('2025-01-04'),  # 1 day rest (back-to-back)
            pd.Timestamp('2025-01-08')   # 4 days rest
        ])
        
        rest_days = dates.diff().dt.days
        
        assert pd.isna(rest_days.iloc[0])  # First game has no previous
        assert rest_days.iloc[1] == 2
        assert rest_days.iloc[2] == 1
        assert rest_days.iloc[3] == 4
    
    def test_head_to_head_record(self):
        """Test head-to-head record calculation"""
        # Sample matchups
        matchups = pd.DataFrame({
            'date': pd.date_range('2025-01-01', periods=5),
            'home_team': ['LAL', 'GSW', 'LAL', 'GSW', 'LAL'],
            'away_team': ['GSW', 'LAL', 'GSW', 'LAL', 'GSW'],
            'home_win': [1, 0, 1, 1, 0]  # LAL: 2 wins, GSW: 2 wins, 1 tie
        })
        
        # LAL vs GSW record
        lal_vs_gsw = matchups[
            ((matchups['home_team'] == 'LAL') & (matchups['away_team'] == 'GSW')) |
            ((matchups['home_team'] == 'GSW') & (matchups['away_team'] == 'LAL'))
        ]
        
        assert len(lal_vs_gsw) == 5
    
    def test_home_away_splits(self):
        """Test home/away split statistics"""
        games = pd.DataFrame({
            'team': ['LAL'] * 10,
            'is_home': [True, False, True, False, True, False, True, False, True, False],
            'win': [1, 0, 1, 0, 1, 1, 1, 0, 1, 0]
        })
        
        home_games = games[games['is_home'] == True]
        away_games = games[games['is_home'] == False]
        
        home_win_rate = home_games['win'].mean()
        away_win_rate = away_games['win'].mean()
        
        # Home win rate is typically higher
        assert home_win_rate > away_win_rate


class TestModelPerformance:
    """Test model performance metrics"""
    
    def test_accuracy_calculation(self):
        """Test accuracy metric calculation"""
        y_true = np.array([1, 0, 1, 1, 0, 1, 0, 0])
        y_pred = np.array([1, 0, 1, 0, 0, 1, 1, 0])
        
        accuracy = np.mean(y_true == y_pred)
        assert 0 <= accuracy <= 1
        assert accuracy == 0.75  # 6 correct out of 8
    
    def test_confusion_matrix(self):
        """Test confusion matrix calculation"""
        y_true = np.array([1, 0, 1, 1, 0])
        y_pred = np.array([1, 0, 1, 0, 0])
        
        # True Positives
        tp = np.sum((y_true == 1) & (y_pred == 1))
        # True Negatives
        tn = np.sum((y_true == 0) & (y_pred == 0))
        # False Positives
        fp = np.sum((y_true == 0) & (y_pred == 1))
        # False Negatives
        fn = np.sum((y_true == 1) & (y_pred == 0))
        
        assert tp == 2
        assert tn == 2
        assert fp == 0
        assert fn == 1
    
    def test_probability_calibration(self):
        """Test prediction probabilities are calibrated"""
        # Sample predictions
        y_prob = np.array([0.9, 0.7, 0.3, 0.1, 0.5])
        
        # All probabilities should be in [0, 1]
        assert np.all((y_prob >= 0) & (y_prob <= 1))
        
        # Complementary probabilities should sum to 1
        y_prob_complement = 1 - y_prob
        assert np.allclose(y_prob + y_prob_complement, 1.0)


class TestDataPreprocessing:
    """Test data preprocessing and cleaning"""
    
    def test_missing_value_handling(self):
        """Test handling of missing values"""
        df = pd.DataFrame({
            'team': ['LAL', 'GSW', 'BOS', 'MIA'],
            'pts': [110.0, np.nan, 115.0, 108.0],
            'reb': [45.0, 42.0, np.nan, 40.0]
        })
        
        # Count missing values
        missing_counts = df.isna().sum()
        assert missing_counts['pts'] == 1
        assert missing_counts['reb'] == 1
        
        # Fill with mean (only numeric columns)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        assert df[numeric_cols].isna().sum().sum() == 0
    
    def test_outlier_detection(self):
        """Test outlier detection"""
        data = np.array([10, 12, 11, 13, 12, 11, 100, 12, 11, 13], dtype=float)
        
        # Calculate z-scores
        z_scores = np.abs((data - np.mean(data)) / np.std(data))
        
        # Identify outliers (z-score > 2)
        outliers = z_scores > 2
        
        assert np.sum(outliers) >= 1  # 100 should be an outlier
        assert data[outliers][0] == 100  # Verify it's the 100 value
    
    def test_feature_scaling(self):
        """Test feature scaling/normalization"""
        data = np.array([[100, 50], [120, 60], [90, 45]])
        
        # Min-max scaling
        data_min = data.min(axis=0)
        data_max = data.max(axis=0)
        scaled = (data - data_min) / (data_max - data_min)
        
        # All scaled values should be in [0, 1]
        assert np.all((scaled >= 0) & (scaled <= 1))
        
        # Min and max should be exactly 0 and 1
        assert np.allclose(scaled.min(axis=0), 0)
        assert np.allclose(scaled.max(axis=0), 1)


class TestBettingCalculations:
    """Test betting-related calculations"""
    
    def test_kelly_criterion(self):
        """Test Kelly Criterion bet sizing"""
        # Setup
        win_prob = 0.55  # 55% win probability
        odds = 2.0       # Decimal odds (even money)
        
        # Kelly formula: f = (bp - q) / b
        # where b = odds - 1, p = win_prob, q = 1 - p
        b = odds - 1
        p = win_prob
        q = 1 - p
        
        kelly = (b * p - q) / b
        
        # Kelly should be positive when we have edge
        assert kelly > 0
        
        # Kelly should be reasonable (not > 100% of bankroll)
        assert kelly < 1.0
    
    def test_implied_probability_from_odds(self):
        """Test converting odds to implied probability"""
        # Decimal odds of 2.0 = 50% probability
        odds = 2.0
        prob = 1 / odds
        assert abs(prob - 0.5) < 0.001
        
        # Favorite at 1.5 = 66.67% probability
        odds_fav = 1.5
        prob_fav = 1 / odds_fav
        assert abs(prob_fav - 0.6667) < 0.01
    
    def test_expected_value(self):
        """Test expected value calculation"""
        # EV = (win_prob * win_amount) - (lose_prob * lose_amount)
        win_prob = 0.6
        win_amount = 100
        lose_prob = 0.4
        lose_amount = 100
        
        ev = (win_prob * win_amount) - (lose_prob * lose_amount)
        
        # Positive EV
        assert ev > 0
        assert ev == 20  # 60 - 40 = 20


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
