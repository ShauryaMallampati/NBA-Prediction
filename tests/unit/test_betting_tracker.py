"""
Unit tests for betting performance tracker (Task #18)
"""

import pytest
from datetime import date, datetime
from src.services.betting_tracker import BettingTracker, BetRecord


def test_database_initialization():
    """Test database and table creation."""
    tracker = BettingTracker(db_path=":memory:")
    
    # Verify tables exist
    cursor = tracker.conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    assert "bets" in tables, "Bets table should exist"
    
    tracker.close()


def test_log_bet():
    """Test logging a bet to database."""
    tracker = BettingTracker(db_path=":memory:")
    
    bet = BetRecord(
        bet_id=None,
        date=date(2024, 1, 15),
        player_name="LeBron James",
        stat_type="PTS",
        bet_direction="OVER",
        market_line=25.5,
        odds=-110,
        predicted_prob=0.58,
        market_prob=0.524,
        edge=0.056,
        actual_value=None,
        outcome=None,
        profit_loss=None,
        sportsbook="fanduel",
        confidence="MEDIUM",
        created_at=datetime.now(),
    )
    
    bet_id = tracker.log_bet(bet)
    
    assert bet_id is not None, "Bet ID should be returned"
    assert bet_id > 0, "Bet ID should be positive"
    
    # Verify bet is in database
    cursor = tracker.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bets WHERE bet_id = ?", (bet_id,))
    count = cursor.fetchone()[0]
    
    assert count == 1, "Bet should exist in database"
    
    tracker.close()


def test_update_bet_outcome_win():
    """Test updating bet outcome with a win."""
    tracker = BettingTracker(db_path=":memory:")
    
    bet = BetRecord(
        bet_id=None,
        date=date(2024, 1, 15),
        player_name="LeBron James",
        stat_type="PTS",
        bet_direction="OVER",
        market_line=25.5,
        odds=-110,
        predicted_prob=0.58,
        market_prob=0.524,
        edge=0.056,
        actual_value=None,
        outcome=None,
        profit_loss=None,
        sportsbook="fanduel",
        confidence="MEDIUM",
        created_at=datetime.now(),
    )
    
    bet_id = tracker.log_bet(bet)
    
    # Update with win (actual = 28, line = 25.5, OVER)
    tracker.update_bet_outcome(bet_id, actual_value=28, stake=100)
    
    # Check outcome
    cursor = tracker.conn.cursor()
    cursor.execute("SELECT outcome, profit_loss FROM bets WHERE bet_id = ?", (bet_id,))
    outcome, profit = cursor.fetchone()
    
    assert outcome == "WIN", "Outcome should be WIN"
    assert profit > 0, "Profit should be positive"
    assert abs(profit - 90.91) < 1, "Profit should be ~$91 for -110 odds"
    
    tracker.close()


def test_update_bet_outcome_loss():
    """Test updating bet outcome with a loss."""
    tracker = BettingTracker(db_path=":memory:")
    
    bet = BetRecord(
        bet_id=None,
        date=date(2024, 1, 15),
        player_name="LeBron James",
        stat_type="PTS",
        bet_direction="OVER",
        market_line=25.5,
        odds=-110,
        predicted_prob=0.58,
        market_prob=0.524,
        edge=0.056,
        actual_value=None,
        outcome=None,
        profit_loss=None,
        sportsbook="fanduel",
        confidence="MEDIUM",
        created_at=datetime.now(),
    )
    
    bet_id = tracker.log_bet(bet)
    
    # Update with loss (actual = 22, line = 25.5, OVER)
    tracker.update_bet_outcome(bet_id, actual_value=22, stake=100)
    
    # Check outcome
    cursor = tracker.conn.cursor()
    cursor.execute("SELECT outcome, profit_loss FROM bets WHERE bet_id = ?", (bet_id,))
    outcome, profit = cursor.fetchone()
    
    assert outcome == "LOSS", "Outcome should be LOSS"
    assert profit == -100, "Loss should be -$100"
    
    tracker.close()


def test_update_bet_outcome_push():
    """Test updating bet outcome with a push."""
    tracker = BettingTracker(db_path=":memory:")
    
    bet = BetRecord(
        bet_id=None,
        date=date(2024, 1, 15),
        player_name="LeBron James",
        stat_type="PTS",
        bet_direction="OVER",
        market_line=25.5,
        odds=-110,
        predicted_prob=0.58,
        market_prob=0.524,
        edge=0.056,
        actual_value=None,
        outcome=None,
        profit_loss=None,
        sportsbook="fanduel",
        confidence="MEDIUM",
        created_at=datetime.now(),
    )
    
    bet_id = tracker.log_bet(bet)
    
    # Update with push (actual = 25.5, line = 25.5, OVER)
    tracker.update_bet_outcome(bet_id, actual_value=25.5, stake=100)
    
    # Check outcome
    cursor = tracker.conn.cursor()
    cursor.execute("SELECT outcome, profit_loss FROM bets WHERE bet_id = ?", (bet_id,))
    outcome, profit = cursor.fetchone()
    
    assert outcome == "PUSH", "Outcome should be PUSH"
    assert profit == 0, "Push should have $0 profit"
    
    tracker.close()


def test_performance_summary():
    """Test performance summary calculation."""
    tracker = BettingTracker(db_path=":memory:")
    
    # Log 3 bets (2 wins, 1 loss)
    bet1 = BetRecord(
        bet_id=None,
        date=date(2024, 1, 15),
        player_name="LeBron James",
        stat_type="PTS",
        bet_direction="OVER",
        market_line=25.5,
        odds=-110,
        predicted_prob=0.58,
        market_prob=0.524,
        edge=0.056,
        actual_value=None,
        outcome=None,
        profit_loss=None,
        sportsbook="fanduel",
        confidence="MEDIUM",
        created_at=datetime.now(),
    )
    
    bet_id1 = tracker.log_bet(bet1)
    tracker.update_bet_outcome(bet_id1, actual_value=28, stake=100)  # Win
    
    bet2 = BetRecord(
        bet_id=None,
        date=date(2024, 1, 15),
        player_name="Stephen Curry",
        stat_type="AST",
        bet_direction="OVER",
        market_line=6.5,
        odds=-110,
        predicted_prob=0.62,
        market_prob=0.545,
        edge=0.075,
        actual_value=None,
        outcome=None,
        profit_loss=None,
        sportsbook="draftkings",
        confidence="HIGH",
        created_at=datetime.now(),
    )
    
    bet_id2 = tracker.log_bet(bet2)
    tracker.update_bet_outcome(bet_id2, actual_value=7, stake=100)  # Win
    
    bet3 = BetRecord(
        bet_id=None,
        date=date(2024, 1, 15),
        player_name="Kevin Durant",
        stat_type="REB",
        bet_direction="OVER",
        market_line=8.5,
        odds=-110,
        predicted_prob=0.55,
        market_prob=0.524,
        edge=0.026,
        actual_value=None,
        outcome=None,
        profit_loss=None,
        sportsbook="fanduel",
        confidence="LOW",
        created_at=datetime.now(),
    )
    
    bet_id3 = tracker.log_bet(bet3)
    tracker.update_bet_outcome(bet_id3, actual_value=6, stake=100)  # Loss
    
    # Get summary
    summary = tracker.get_performance_summary()
    
    assert summary["total_bets"] == 3
    assert summary["wins"] == 2
    assert summary["losses"] == 1
    assert summary["decided_bets"] == 3
    assert abs(summary["win_rate"] - 66.67) < 0.1, "Win rate should be ~66.7%"
    assert summary["total_profit"] > 0, "Total profit should be positive"
    
    tracker.close()


def test_performance_by_stat():
    """Test performance breakdown by stat type."""
    tracker = BettingTracker(db_path=":memory:")
    
    # Log bets with different stats
    bet1 = BetRecord(
        bet_id=None,
        date=date(2024, 1, 15),
        player_name="LeBron James",
        stat_type="PTS",
        bet_direction="OVER",
        market_line=25.5,
        odds=-110,
        predicted_prob=0.58,
        market_prob=0.524,
        edge=0.056,
        actual_value=None,
        outcome=None,
        profit_loss=None,
        sportsbook="fanduel",
        confidence="MEDIUM",
        created_at=datetime.now(),
    )
    
    bet_id1 = tracker.log_bet(bet1)
    tracker.update_bet_outcome(bet_id1, actual_value=28, stake=100)  # Win
    
    bet2 = BetRecord(
        bet_id=None,
        date=date(2024, 1, 15),
        player_name="Stephen Curry",
        stat_type="AST",
        bet_direction="OVER",
        market_line=6.5,
        odds=-110,
        predicted_prob=0.62,
        market_prob=0.545,
        edge=0.075,
        actual_value=None,
        outcome=None,
        profit_loss=None,
        sportsbook="draftkings",
        confidence="HIGH",
        created_at=datetime.now(),
    )
    
    bet_id2 = tracker.log_bet(bet2)
    tracker.update_bet_outcome(bet_id2, actual_value=5, stake=100)  # Loss
    
    # Get breakdown
    df = tracker.get_performance_by_stat()
    
    assert len(df) == 2, "Should have 2 stat types"
    assert set(df["stat_type"]) == {"PTS", "AST"}, "Should have PTS and AST"
    
    pts_row = df[df["stat_type"] == "PTS"].iloc[0]
    assert pts_row["wins"] == 1
    assert pts_row["losses"] == 0
    assert pts_row["win_rate"] == 100.0
    
    ast_row = df[df["stat_type"] == "AST"].iloc[0]
    assert ast_row["wins"] == 0
    assert ast_row["losses"] == 1
    assert ast_row["win_rate"] == 0.0
    
    tracker.close()


def test_performance_by_confidence():
    """Test performance breakdown by confidence level."""
    tracker = BettingTracker(db_path=":memory:")
    
    # Log bets with different confidence
    bet1 = BetRecord(
        bet_id=None,
        date=date(2024, 1, 15),
        player_name="LeBron James",
        stat_type="PTS",
        bet_direction="OVER",
        market_line=25.5,
        odds=-110,
        predicted_prob=0.58,
        market_prob=0.524,
        edge=0.056,
        actual_value=None,
        outcome=None,
        profit_loss=None,
        sportsbook="fanduel",
        confidence="HIGH",
        created_at=datetime.now(),
    )
    
    bet_id1 = tracker.log_bet(bet1)
    tracker.update_bet_outcome(bet_id1, actual_value=28, stake=100)  # Win
    
    bet2 = BetRecord(
        bet_id=None,
        date=date(2024, 1, 15),
        player_name="Stephen Curry",
        stat_type="AST",
        bet_direction="OVER",
        market_line=6.5,
        odds=-110,
        predicted_prob=0.62,
        market_prob=0.545,
        edge=0.075,
        actual_value=None,
        outcome=None,
        profit_loss=None,
        sportsbook="draftkings",
        confidence="LOW",
        created_at=datetime.now(),
    )
    
    bet_id2 = tracker.log_bet(bet2)
    tracker.update_bet_outcome(bet_id2, actual_value=5, stake=100)  # Loss
    
    # Get breakdown
    df = tracker.get_performance_by_confidence()
    
    assert len(df) == 2, "Should have 2 confidence levels"
    assert set(df["confidence"]) == {"HIGH", "LOW"}, "Should have HIGH and LOW"
    
    high_row = df[df["confidence"] == "HIGH"].iloc[0]
    assert high_row["wins"] == 1
    assert high_row["win_rate"] == 100.0
    
    low_row = df[df["confidence"] == "LOW"].iloc[0]
    assert low_row["wins"] == 0
    assert low_row["win_rate"] == 0.0
    
    tracker.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
