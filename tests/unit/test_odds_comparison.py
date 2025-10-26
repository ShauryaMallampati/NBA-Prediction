"""
Unit tests for Odds Comparison Engine (Task #16)

Tests:
  1. American odds → probability conversion
  2. Edge calculation
  3. Recommendation generation
  4. Confidence classification
  5. Market line parsing
"""

import pytest
import pandas as pd
from datetime import datetime
import sys
import pathlib

src_path = pathlib.Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from services.odds_comparison import (
    OddsComparisonEngine,
    MarketLine,
    BettingRecommendation,
)


@pytest.fixture
def engine():
    """Create engine with test API key."""
    return OddsComparisonEngine(odds_api_key="test_key")


def test_american_to_probability(engine):
    """Test odds conversion."""
    # Favorite odds
    assert engine.american_to_probability(-110) == pytest.approx(0.524, abs=0.001)
    assert engine.american_to_probability(-200) == pytest.approx(0.667, abs=0.001)
    
    # Underdog odds
    assert engine.american_to_probability(+150) == pytest.approx(0.400, abs=0.001)
    assert engine.american_to_probability(+200) == pytest.approx(0.333, abs=0.001)
    
    # Even odds
    assert engine.american_to_probability(+100) == pytest.approx(0.500, abs=0.001)


def test_calculate_edge(engine):
    """Test edge calculation."""
    # Positive edge
    edge = engine.calculate_edge(model_prob=0.55, market_prob=0.50)
    assert edge == pytest.approx(0.05)  # 5% edge
    
    # Negative edge
    edge = engine.calculate_edge(model_prob=0.45, market_prob=0.50)
    assert edge == pytest.approx(-0.05)  # -5% edge
    
    # No edge
    edge = engine.calculate_edge(model_prob=0.52, market_prob=0.52)
    assert edge == pytest.approx(0.0)


def test_classify_confidence(engine):
    """Test confidence classification."""
    assert engine._classify_confidence(0.10) == "HIGH"  # 10% edge
    assert engine._classify_confidence(0.06) == "MEDIUM"  # 6% edge
    assert engine._classify_confidence(0.04) == "LOW"  # 4% edge


def test_map_market_to_stat(engine):
    """Test market key mapping."""
    assert engine._map_market_to_stat("player_points") == "PTS"
    assert engine._map_market_to_stat("player_assists") == "AST"
    assert engine._map_market_to_stat("player_rebounds") == "REB"
    assert engine._map_market_to_stat("player_steals") == "STL"
    assert engine._map_market_to_stat("player_blocks") == "BLK"
    assert engine._map_market_to_stat("unknown_market") is None


def test_generate_recommendations(engine):
    """Test recommendation generation."""
    # Mock model predictions
    predictions = pd.DataFrame([
        {"player_name": "LeBron James", "stat_type": "PTS", "predicted_prob": 0.60},
        {"player_name": "Stephen Curry", "stat_type": "AST", "predicted_prob": 0.55},
    ])
    
    # Mock market lines
    market_lines = [
        MarketLine(
            player_name="LeBron James",
            stat_type="PTS",
            line=25.5,
            over_odds=-110,  # Implies ~52.4%
            under_odds=-110,
            sportsbook="fanduel",
            timestamp=datetime.now(),
        ),
        MarketLine(
            player_name="Stephen Curry",
            stat_type="AST",
            line=6.5,
            over_odds=-120,  # Implies ~54.5%
            under_odds=+100,
            sportsbook="draftkings",
            timestamp=datetime.now(),
        ),
    ]
    
    # Generate recommendations (3% min edge)
    recommendations = engine.generate_recommendations(
        predictions, market_lines, min_edge=0.03
    )
    
    # Should find LeBron OVER (60% vs 52.4% = +7.6% edge)
    assert len(recommendations) >= 1
    
    lebron_rec = [r for r in recommendations if r.player_name == "LeBron James"][0]
    assert lebron_rec.bet_direction == "OVER"
    assert lebron_rec.edge >= 0.05  # At least 5% edge
    assert lebron_rec.confidence in ["HIGH", "MEDIUM", "LOW"]


def test_generate_recommendations_no_edge(engine):
    """Test when no edge exists."""
    # Model and market agree
    predictions = pd.DataFrame([
        {"player_name": "Player A", "stat_type": "PTS", "predicted_prob": 0.52},
    ])
    
    market_lines = [
        MarketLine(
            player_name="Player A",
            stat_type="PTS",
            line=25.5,
            over_odds=-108,  # Implies ~51.9%
            under_odds=-112,
            sportsbook="fanduel",
            timestamp=datetime.now(),
        ),
    ]
    
    # Should find NO recommendations (edge < 3%)
    recommendations = engine.generate_recommendations(
        predictions, market_lines, min_edge=0.03
    )
    
    assert len(recommendations) == 0


def test_recommendation_dataclass():
    """Test BettingRecommendation dataclass."""
    rec = BettingRecommendation(
        player_name="Test Player",
        stat_type="PTS",
        model_prob=0.60,
        market_line=25.5,
        market_prob=0.52,
        edge=0.08,
        bet_direction="OVER",
        odds=-110,
        sportsbook="fanduel",
        confidence="HIGH",
    )
    
    assert rec.player_name == "Test Player"
    assert rec.edge == 0.08
    assert rec.confidence == "HIGH"


def test_market_line_dataclass():
    """Test MarketLine dataclass."""
    line = MarketLine(
        player_name="Test Player",
        stat_type="PTS",
        line=25.5,
        over_odds=-110,
        under_odds=-110,
        sportsbook="fanduel",
        timestamp=datetime.now(),
    )
    
    assert line.player_name == "Test Player"
    assert line.line == 25.5
    assert line.over_odds == -110


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
