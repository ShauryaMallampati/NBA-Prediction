"""
Betting Performance Tracking & ROI Dashboard (Task #18)

CRITICAL METRICS:
  • Daily: date, player, stat, prediction, market line, actual outcome, edge, win/loss
  • Monthly: Cumulative ROI, win rate by stat, win rate by odds tier
  • Target: 53%+ win rate

Purpose: Track every bet to prove profitability
  Example: "Your model is currently +$2,400 on 200 bets (55% win rate)"

Uses SQL database (PostgreSQL), NOT ML model
"""

from __future__ import annotations
from datetime import datetime, date
from typing import Dict, List, Optional
from dataclasses import dataclass
import sqlite3
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BetRecord:
    """Individual bet tracking record."""
    bet_id: Optional[int]  # Auto-generated
    date: date
    player_name: str
    stat_type: str  # PTS, AST, REB, STL, BLK
    bet_direction: str  # OVER or UNDER
    market_line: float  # e.g., 25.5
    odds: int  # American odds
    predicted_prob: float  # Model's probability
    market_prob: float  # Implied probability
    edge: float  # Predicted edge
    actual_value: Optional[float]  # Actual stat value
    outcome: Optional[str]  # WIN, LOSS, PUSH, PENDING
    profit_loss: Optional[float]  # $ profit/loss
    sportsbook: str
    confidence: str  # HIGH, MEDIUM, LOW
    created_at: datetime


class BettingTracker:
    """
    Track betting performance and calculate ROI.
    Uses SQLite for simplicity (can swap to PostgreSQL in production).
    """
    
    def __init__(self, db_path: str = "betting_performance.db"):
        """
        Initialize tracker with database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
        logger.info(f"✅ Connected to database: {db_path}")
    
    def _create_tables(self):
        """Create bet tracking tables if they don't exist."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                bet_id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                player_name TEXT NOT NULL,
                stat_type TEXT NOT NULL,
                bet_direction TEXT NOT NULL,
                market_line REAL NOT NULL,
                odds INTEGER NOT NULL,
                predicted_prob REAL NOT NULL,
                market_prob REAL NOT NULL,
                edge REAL NOT NULL,
                actual_value REAL,
                outcome TEXT,
                profit_loss REAL,
                sportsbook TEXT NOT NULL,
                confidence TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_date ON bets(date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_outcome ON bets(outcome)
        """)
        
        self.conn.commit()
        logger.info("✅ Tables created/verified")
    
    def log_bet(self, bet: BetRecord) -> int:
        """
        Log a new bet to database.
        
        Args:
            bet: BetRecord object
        
        Returns:
            bet_id: Generated bet ID
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO bets (
                date, player_name, stat_type, bet_direction, market_line,
                odds, predicted_prob, market_prob, edge, actual_value,
                outcome, profit_loss, sportsbook, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bet.date,
            bet.player_name,
            bet.stat_type,
            bet.bet_direction,
            bet.market_line,
            bet.odds,
            bet.predicted_prob,
            bet.market_prob,
            bet.edge,
            bet.actual_value,
            bet.outcome,
            bet.profit_loss,
            bet.sportsbook,
            bet.confidence,
        ))
        
        self.conn.commit()
        bet_id = cursor.lastrowid
        
        logger.info(f"✅ Logged bet #{bet_id}: {bet.player_name} {bet.stat_type} {bet.bet_direction}")
        return bet_id
    
    def update_bet_outcome(
        self,
        bet_id: int,
        actual_value: float,
        stake: float = 100,
    ) -> None:
        """
        Update bet with actual outcome and calculate P&L.
        
        Args:
            bet_id: Bet ID to update
            actual_value: Actual stat value (e.g., 27 points)
            stake: Bet amount in dollars (default $100)
        """
        cursor = self.conn.cursor()
        
        # Get bet details
        cursor.execute("""
            SELECT bet_direction, market_line, odds
            FROM bets WHERE bet_id = ?
        """, (bet_id,))
        
        row = cursor.fetchone()
        if not row:
            logger.error(f"❌ Bet #{bet_id} not found")
            return
        
        direction, line, odds = row
        
        # Determine outcome
        if direction == "OVER":
            if actual_value > line:
                outcome = "WIN"
            elif actual_value < line:
                outcome = "LOSS"
            else:
                outcome = "PUSH"
        else:  # UNDER
            if actual_value < line:
                outcome = "WIN"
            elif actual_value > line:
                outcome = "LOSS"
            else:
                outcome = "PUSH"
        
        # Calculate profit/loss
        if outcome == "WIN":
            if odds < 0:
                profit = stake * (100 / abs(odds))
            else:
                profit = stake * (odds / 100)
        elif outcome == "LOSS":
            profit = -stake
        else:  # PUSH
            profit = 0
        
        # Update database
        cursor.execute("""
            UPDATE bets
            SET actual_value = ?, outcome = ?, profit_loss = ?
            WHERE bet_id = ?
        """, (actual_value, outcome, profit, bet_id))
        
        self.conn.commit()
        
        logger.info(f"✅ Updated bet #{bet_id}: {outcome} ({profit:+.2f})")
    
    def get_performance_summary(self, start_date: Optional[date] = None) -> Dict:
        """
        Get overall performance summary.
        
        Args:
            start_date: Filter bets from this date onward
        
        Returns:
            Dict with metrics: total_bets, wins, losses, pushes, win_rate, roi, etc.
        """
        cursor = self.conn.cursor()
        
        where_clause = ""
        params = []
        if start_date:
            where_clause = "WHERE date >= ?"
            params.append(start_date)
        
        # Overall stats
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_bets,
                SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
                SUM(CASE WHEN outcome = 'PUSH' THEN 1 ELSE 0 END) as pushes,
                SUM(CASE WHEN outcome IS NULL THEN 1 ELSE 0 END) as pending,
                SUM(COALESCE(profit_loss, 0)) as total_profit
            FROM bets
            {where_clause}
        """, params)
        
        row = cursor.fetchone()
        total_bets, wins, losses, pushes, pending, total_profit = row
        
        # Win rate (excluding pushes and pending)
        decided_bets = wins + losses
        win_rate = (wins / decided_bets * 100) if decided_bets > 0 else 0
        
        # ROI (assuming $100 stake per bet)
        total_wagered = decided_bets * 100
        roi = (total_profit / total_wagered * 100) if total_wagered > 0 else 0
        
        return {
            "total_bets": total_bets,
            "wins": wins,
            "losses": losses,
            "pushes": pushes,
            "pending": pending,
            "decided_bets": decided_bets,
            "win_rate": win_rate,
            "total_profit": total_profit,
            "total_wagered": total_wagered,
            "roi": roi,
        }
    
    def get_performance_by_stat(self) -> pd.DataFrame:
        """Get performance breakdown by stat type."""
        query = """
            SELECT 
                stat_type,
                COUNT(*) as total_bets,
                SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
                ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 
                    CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END 
                END) * 100, 1) as win_rate,
                SUM(COALESCE(profit_loss, 0)) as profit
            FROM bets
            WHERE outcome IS NOT NULL
            GROUP BY stat_type
            ORDER BY profit DESC
        """
        return pd.read_sql_query(query, self.conn)
    
    def get_performance_by_confidence(self) -> pd.DataFrame:
        """Get performance breakdown by confidence level."""
        query = """
            SELECT 
                confidence,
                COUNT(*) as total_bets,
                SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                ROUND(AVG(CASE WHEN outcome IN ('WIN', 'LOSS') THEN 
                    CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END 
                END) * 100, 1) as win_rate,
                SUM(COALESCE(profit_loss, 0)) as profit
            FROM bets
            WHERE outcome IS NOT NULL
            GROUP BY confidence
            ORDER BY 
                CASE confidence 
                    WHEN 'HIGH' THEN 1 
                    WHEN 'MEDIUM' THEN 2 
                    WHEN 'LOW' THEN 3 
                END
        """
        return pd.read_sql_query(query, self.conn)
    
    def print_dashboard(self):
        """Print performance dashboard to console."""
        summary = self.get_performance_summary()
        
        print("\n" + "="*80)
        print("🎯 BETTING PERFORMANCE DASHBOARD")
        print("="*80)
        
        print(f"\nOverall Performance:")
        print(f"  Total Bets:    {summary['total_bets']}")
        print(f"  Decided:       {summary['decided_bets']} (W: {summary['wins']}, L: {summary['losses']}, P: {summary['pushes']})")
        print(f"  Pending:       {summary['pending']}")
        print(f"  Win Rate:      {summary['win_rate']:.1f}%")
        print(f"  Total Profit:  ${summary['total_profit']:,.2f}")
        print(f"  Total Wagered: ${summary['total_wagered']:,.2f}")
        print(f"  ROI:           {summary['roi']:+.1f}%")
        
        # By stat type
        print(f"\nPerformance by Stat:")
        stat_df = self.get_performance_by_stat()
        if not stat_df.empty:
            print(stat_df.to_string(index=False))
        
        # By confidence
        print(f"\nPerformance by Confidence:")
        conf_df = self.get_performance_by_confidence()
        if not conf_df.empty:
            print(conf_df.to_string(index=False))
        
        print("\n" + "="*80)
    
    def close(self):
        """Close database connection."""
        self.conn.close()
        logger.info("✅ Database connection closed")


def main():
    """Example usage."""
    tracker = BettingTracker(db_path=":memory:")  # In-memory for demo
    
    # Example: Log some bets
    print("\n📝 Logging sample bets...")
    
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
    
    bet2 = BetRecord(
        bet_id=None,
        date=date(2024, 1, 15),
        player_name="Stephen Curry",
        stat_type="AST",
        bet_direction="OVER",
        market_line=6.5,
        odds=-120,
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
    
    # Update outcomes
    print("\n✅ Updating bet outcomes...")
    tracker.update_bet_outcome(bet_id1, actual_value=28, stake=100)  # LeBron scored 28
    tracker.update_bet_outcome(bet_id2, actual_value=7, stake=100)   # Curry had 7 assists
    
    # Display dashboard
    tracker.print_dashboard()
    
    tracker.close()


if __name__ == "__main__":
    main()
