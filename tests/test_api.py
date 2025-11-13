"""
Test Suite for API Endpoints
Tests all FastAPI routes for predictions, schedule, analytics
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pandas as pd
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.api.main import app

client = TestClient(app)


class TestPredictionsAPI:
    """Test predictions API endpoints"""
    
    def test_get_today_predictions(self):
        """Test GET /api/predictions/today"""
        response = client.get("/api/predictions/today")
        assert response.status_code == 200
        
        data = response.json()
        assert "predictions" in data
        assert "date" in data
        assert isinstance(data["predictions"], list)
    
    def test_get_predictions_by_date(self):
        """Test GET /api/predictions/{date}"""
        test_date = "2025-11-12"
        response = client.get(f"/api/predictions/{test_date}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["date"] == test_date
        assert "predictions" in data
    
    def test_get_prediction_by_game_id(self):
        """Test GET /api/predictions/game/{game_id}"""
        # This requires actual game data
        response = client.get("/api/predictions/game/0022200001")
        assert response.status_code in [200, 404]  # 404 if game doesn't exist
    
    def test_predictions_validation(self):
        """Test that predictions have required fields"""
        response = client.get("/api/predictions/today")
        assert response.status_code == 200
        
        predictions = response.json()["predictions"]
        
        if len(predictions) > 0:
            pred = predictions[0]
            required_fields = ["game_id", "home_team", "away_team", "home_win_prob", "confidence"]
            for field in required_fields:
                assert field in pred
            
            # Validate probability range
            assert 0 <= pred["home_win_prob"] <= 1
            assert pred["confidence"] in ["high", "medium", "low"]


class TestScheduleAPI:
    """Test schedule API endpoints"""
    
    def test_get_today_schedule(self):
        """Test GET /api/schedule/today"""
        response = client.get("/api/schedule/today")
        assert response.status_code == 200
        
        data = response.json()
        assert "games" in data
        assert "date" in data
    
    def test_get_schedule_by_month(self):
        """Test GET /api/schedule/{year}/{month}"""
        response = client.get("/api/schedule/2024/11")
        assert response.status_code == 200
        
        data = response.json()
        assert "games" in data
        assert isinstance(data["games"], list)
    
    def test_get_team_schedule(self):
        """Test GET /api/schedule/team/{team}"""
        response = client.get("/api/schedule/team/LAL")
        assert response.status_code == 200
        
        data = response.json()
        assert "team" in data
        assert data["team"] == "LAL"


class TestAnalyticsAPI:
    """Test analytics API endpoints"""
    
    def test_get_model_performance(self):
        """Test GET /api/analytics/performance"""
        response = client.get("/api/analytics/performance")
        assert response.status_code == 200
        
        data = response.json()
        metrics = ["accuracy", "precision", "recall", "f1_score", "auc_roc"]
        for metric in metrics:
            assert metric in data
            assert isinstance(data[metric], (int, float))
    
    def test_get_feature_importance(self):
        """Test GET /api/analytics/features"""
        response = client.get("/api/analytics/features")
        assert response.status_code == 200
        
        data = response.json()
        assert "features" in data
        assert isinstance(data["features"], list)
        
        if len(data["features"]) > 0:
            feature = data["features"][0]
            assert "name" in feature
            assert "importance" in feature
    
    def test_get_team_stats(self):
        """Test GET /api/analytics/teams"""
        response = client.get("/api/analytics/teams")
        assert response.status_code == 200
        
        data = response.json()
        assert "teams" in data
        assert isinstance(data["teams"], list)


class TestLiveAPI:
    """Test live games API endpoints"""
    
    def test_get_live_games(self):
        """Test GET /api/live/games"""
        response = client.get("/api/live/games")
        assert response.status_code == 200
        
        data = response.json()
        assert "games" in data
        assert isinstance(data["games"], list)
    
    def test_get_live_win_probability(self):
        """Test GET /api/live/{game_id}/probability"""
        # This requires a live game
        response = client.get("/api/live/0022200001/probability")
        assert response.status_code in [200, 404]
    
    def test_live_updates_websocket(self):
        """Test WebSocket connection for live updates"""
        # This would require WebSocket testing
        # Placeholder for now
        pass


class TestBettingAPI:
    """Test betting odds API endpoints"""
    
    def test_get_today_odds(self):
        """Test GET /api/odds/today"""
        response = client.get("/api/odds/today")
        assert response.status_code == 200
        
        data = response.json()
        assert "odds" in data
    
    def test_get_best_bets(self):
        """Test GET /api/betting/best-bets"""
        response = client.get("/api/betting/best-bets")
        assert response.status_code == 200
        
        data = response.json()
        assert "bets" in data
        assert isinstance(data["bets"], list)
    
    def test_kelly_calculator(self):
        """Test POST /api/betting/kelly"""
        payload = {
            "probability": 0.65,
            "odds": 150,  # American odds
            "bankroll": 1000
        }
        
        response = client.post("/api/betting/kelly", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "bet_size" in data
        assert "full_kelly" in data
        assert "half_kelly" in data
        assert "quarter_kelly" in data


class TestHealthCheck:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test GET /"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_endpoint(self):
        """Test GET /health"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "model_loaded" in data
        assert "data_available" in data


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_date_format(self):
        """Test invalid date format"""
        response = client.get("/api/predictions/invalid-date")
        assert response.status_code in [400, 422]
    
    def test_future_date_predictions(self):
        """Test predictions for future dates (should work)"""
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        response = client.get(f"/api/predictions/{future_date}")
        assert response.status_code == 200
    
    def test_invalid_team_code(self):
        """Test invalid team code"""
        response = client.get("/api/schedule/team/INVALID")
        assert response.status_code in [400, 404]
    
    def test_nonexistent_game_id(self):
        """Test nonexistent game ID"""
        response = client.get("/api/predictions/game/9999999999")
        assert response.status_code == 404


@pytest.fixture
def sample_prediction_data():
    """Fixture for sample prediction data"""
    return {
        "game_id": "0022200001",
        "date": "2025-11-12",
        "home_team": "LAL",
        "away_team": "GSW",
        "home_win_prob": 0.65,
        "away_win_prob": 0.35,
        "confidence": "high",
        "predicted_spread": -5.5,
        "predicted_total": 225.5
    }


@pytest.fixture
def sample_odds_data():
    """Fixture for sample odds data"""
    return {
        "game_id": "0022200001",
        "home_ml": -200,
        "away_ml": +170,
        "home_spread": -5.5,
        "total": 225.5,
        "sportsbook": "DraftKings"
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
