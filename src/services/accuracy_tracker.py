"""
"""Track how well our predictions actually do.

We save every prediction, record the actual outcomes, then calculate
accuracy stats so we know if we're improving or not.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)


class AccuracyTracker:
    """Keep a running log of predictions vs. reality."""
    
    def __init__(self, db_path: str = "betting_performance.db"):
        """Set up the accuracy tracking database."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"📊 Accuracy tracker initialized: {db_path}")
    
    def _init_database(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                date TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_win_prob REAL NOT NULL,
                away_win_prob REAL NOT NULL,
                predicted_winner TEXT,
                confidence REAL,
                features TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(game_id, date)
            )
        """)
        
        # Create outcomes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                date TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_score INTEGER,
                away_score INTEGER,
                actual_winner TEXT,
                home_win INTEGER,
                updated_at TEXT NOT NULL,
                UNIQUE(game_id, date)
            )
        """)
        
        # Create accuracy_metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accuracy_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                team TEXT,
                confidence_level TEXT,
                total_predictions INTEGER,
                correct_predictions INTEGER,
                accuracy REAL,
                calculated_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")
    
    def log_prediction(
        self,
        game_id: str,
        date: str,
        home_team: str,
        away_team: str,
        home_win_prob: float,
        away_win_prob: float,
        confidence: Optional[float] = None,
        features: Optional[Dict] = None
    ) -> int:
        """
        Log a prediction.
        
        Args:
            game_id: Game ID
            date: Game date (YYYY-MM-DD)
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            home_win_prob: Home team win probability
            away_win_prob: Away team win probability
            confidence: Prediction confidence (0-1)
            features: Feature values (optional)
        
        Returns:
            Prediction ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Determine predicted winner
        predicted_winner = home_team if home_win_prob > 0.5 else away_team
        
        # Calculate confidence if not provided
        if confidence is None:
            confidence = abs(home_win_prob - 0.5) * 2  # 0-1 scale
        
        # Insert prediction
        cursor.execute("""
            INSERT OR REPLACE INTO predictions
            (game_id, date, home_team, away_team, home_win_prob, away_win_prob,
             predicted_winner, confidence, features, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id, date, home_team, away_team, home_win_prob, away_win_prob,
            predicted_winner, confidence, json.dumps(features) if features else None,
            datetime.now().isoformat()
        ))
        
        prediction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.debug(f"📊 Logged prediction: {game_id} ({predicted_winner} {home_win_prob:.1%})")
        
        return prediction_id
    
    def log_outcome(
        self,
        game_id: str,
        date: str,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int
    ):
        """
        Log game outcome.
        
        Args:
            game_id: Game ID
            date: Game date (YYYY-MM-DD)
            home_team: Home team abbreviation
            away_team: Away team abbreviation
            home_score: Home team score
            away_score: Away team score
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Determine actual winner
        actual_winner = home_team if home_score > away_score else away_team
        home_win = 1 if home_score > away_score else 0
        
        # Insert outcome
        cursor.execute("""
            INSERT OR REPLACE INTO outcomes
            (game_id, date, home_team, away_team, home_score, away_score,
             actual_winner, home_win, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id, date, home_team, away_team, home_score, away_score,
            actual_winner, home_win, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        logger.debug(f"📊 Logged outcome: {game_id} ({actual_winner} wins)")
    
    def calculate_accuracy(
        self,
        team: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        confidence_level: Optional[str] = None
    ) -> Dict:
        """
        Calculate prediction accuracy.
        
        Args:
            team: Team abbreviation (optional)
            start_date: Start date (YYYY-MM-DD) (optional)
            end_date: End date (YYYY-MM-DD) (optional)
            confidence_level: Confidence level (HIGH, MEDIUM, LOW) (optional)
        
        Returns:
            Dictionary with accuracy metrics
        """
        logger.info(f"📊 Calculating accuracy (team={team}, start_date={start_date}, end_date={end_date})")
        
        conn = sqlite3.connect(self.db_path)
        
        # Build query
        query = """
            SELECT p.game_id, p.date, p.home_team, p.away_team,
                   p.predicted_winner, p.confidence, p.home_win_prob,
                   o.actual_winner, o.home_win
            FROM predictions p
            INNER JOIN outcomes o ON p.game_id = o.game_id AND p.date = o.date
            WHERE 1=1
        """
        
        params = []
        
        if team:
            query += " AND (p.home_team = ? OR p.away_team = ?)"
            params.extend([team, team])
        
        if start_date:
            query += " AND p.date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND p.date <= ?"
            params.append(end_date)
        
        if confidence_level:
            if confidence_level == "HIGH":
                query += " AND p.confidence >= 0.6"
            elif confidence_level == "MEDIUM":
                query += " AND p.confidence >= 0.4 AND p.confidence < 0.6"
            elif confidence_level == "LOW":
                query += " AND p.confidence < 0.4"
        
        # Execute query
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if len(df) == 0:
            logger.warning("No predictions found for accuracy calculation")
            return {
                'total_predictions': 0,
                'correct_predictions': 0,
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
            }
        
        # Calculate accuracy
        df['correct'] = (df['predicted_winner'] == df['actual_winner']).astype(int)
        
        total = len(df)
        correct = df['correct'].sum()
        accuracy = correct / total if total > 0 else 0.0
        
        # Calculate precision, recall, F1
        true_positives = df[df['correct'] == 1].shape[0]
        false_positives = df[(df['correct'] == 0) & (df['predicted_winner'] == df['home_team'])].shape[0]
        false_negatives = df[(df['correct'] == 0) & (df['predicted_winner'] == df['away_team'])].shape[0]
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        metrics = {
            'total_predictions': total,
            'correct_predictions': correct,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
        }
        
        logger.info(f"✅ Accuracy: {accuracy:.1%} ({correct}/{total})")
        
        return metrics
    
    def get_accuracy_by_team(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get accuracy by team.
        
        Args:
            start_date: Start date (YYYY-MM-DD) (optional)
            end_date: End date (YYYY-MM-DD) (optional)
        
        Returns:
            DataFrame with accuracy by team
        """
        logger.info("📊 Calculating accuracy by team...")
        
        conn = sqlite3.connect(self.db_path)
        
        # Get all teams
        teams = pd.read_sql_query("SELECT DISTINCT home_team FROM predictions", conn)['home_team'].tolist()
        
        # Calculate accuracy for each team
        team_accuracy = []
        for team in teams:
            metrics = self.calculate_accuracy(team=team, start_date=start_date, end_date=end_date)
            team_accuracy.append({
                'team': team,
                'total_predictions': metrics['total_predictions'],
                'correct_predictions': metrics['correct_predictions'],
                'accuracy': metrics['accuracy'],
            })
        
        conn.close()
        
        df = pd.DataFrame(team_accuracy)
        df = df.sort_values('accuracy', ascending=False)
        
        logger.info(f"✅ Calculated accuracy for {len(df)} teams")
        
        return df
    
    def get_accuracy_by_confidence(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get accuracy by confidence level.
        
        Args:
            start_date: Start date (YYYY-MM-DD) (optional)
            end_date: End date (YYYY-MM-DD) (optional)
        
        Returns:
            DataFrame with accuracy by confidence level
        """
        logger.info("📊 Calculating accuracy by confidence level...")
        
        confidence_levels = ["HIGH", "MEDIUM", "LOW"]
        
        confidence_accuracy = []
        for level in confidence_levels:
            metrics = self.calculate_accuracy(
                start_date=start_date,
                end_date=end_date,
                confidence_level=level
            )
            confidence_accuracy.append({
                'confidence_level': level,
                'total_predictions': metrics['total_predictions'],
                'correct_predictions': metrics['correct_predictions'],
                'accuracy': metrics['accuracy'],
            })
        
        df = pd.DataFrame(confidence_accuracy)
        
        logger.info(f"✅ Calculated accuracy for {len(df)} confidence levels")
        
        return df
    
    def get_recent_accuracy(self, days: int = 30) -> Dict:
        """
        Get accuracy for recent predictions.
        
        Args:
            days: Number of days to look back
        
        Returns:
            Dictionary with accuracy metrics
        """
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
        
        return self.calculate_accuracy(start_date=start_date, end_date=end_date)


# Singleton instance
_tracker: Optional[AccuracyTracker] = None


def get_accuracy_tracker() -> AccuracyTracker:
    """Get or create accuracy tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = AccuracyTracker()
    return _tracker


if __name__ == "__main__":
    # Example usage
    tracker = get_accuracy_tracker()
    
    # Calculate overall accuracy
    metrics = tracker.calculate_accuracy()
    print(f"Overall accuracy: {metrics['accuracy']:.1%}")
    
    # Calculate accuracy by team
    team_accuracy = tracker.get_accuracy_by_team()
    print(f"\nAccuracy by team:")
    print(team_accuracy.head(10))
    
    # Calculate accuracy by confidence
    confidence_accuracy = tracker.get_accuracy_by_confidence()
    print(f"\nAccuracy by confidence:")
    print(confidence_accuracy)

