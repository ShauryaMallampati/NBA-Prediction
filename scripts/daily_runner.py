"""
Daily Prediction Runner with Accuracy Tracking

This script:
1. Runs predictions every morning
2. Fetches actual game results from previous day
3. Compares predictions vs actuals
4. Logs accuracy metrics to a database
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import sqlite3
from datetime import datetime, timedelta
import logging
import pandas as pd
from nba_api.stats.endpoints import ScoreboardV2, LeagueGameFinder
from nba_api.stats.static import teams

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database for tracking predictions and results
DB_PATH = Path("artifacts/predictions_tracker.db")


def init_database():
    """Initialize SQLite database for tracking predictions."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT UNIQUE,
            game_date TEXT,
            home_team TEXT,
            away_team TEXT,
            predicted_winner TEXT,
            home_win_prob REAL,
            confidence REAL,
            created_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT UNIQUE,
            game_date TEXT,
            home_team TEXT,
            away_team TEXT,
            home_score INTEGER,
            away_score INTEGER,
            actual_winner TEXT,
            created_at TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accuracy_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            total_games INTEGER,
            correct_predictions INTEGER,
            accuracy REAL,
            avg_confidence REAL,
            created_at TEXT
        )
    """)
    
    conn.commit()
    return conn


def get_yesterdays_results():
    """Fetch actual game results from yesterday."""
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")
    
    logger.info(f"Fetching results for {date_str}...")
    
    try:
        # Use NBA API to get yesterday's scoreboard
        scoreboard = ScoreboardV2(game_date=yesterday.strftime("%m/%d/%Y"))
        games = scoreboard.game_header.get_data_frame()
        line_scores = scoreboard.line_score.get_data_frame()
        
        results = []
        for _, game in games.iterrows():
            game_id = game['GAME_ID']
            home_team_id = game['HOME_TEAM_ID']
            away_team_id = game['VISITOR_TEAM_ID']
            
            # Get team names
            all_teams = teams.get_teams()
            home_team = next((t['abbreviation'] for t in all_teams if t['id'] == home_team_id), 'UNK')
            away_team = next((t['abbreviation'] for t in all_teams if t['id'] == away_team_id), 'UNK')
            
            # Get scores from line scores
            home_scores = line_scores[line_scores['TEAM_ID'] == home_team_id]
            away_scores = line_scores[line_scores['TEAM_ID'] == away_team_id]
            
            if not home_scores.empty and not away_scores.empty:
                home_score = int(home_scores['PTS'].values[0]) if pd.notna(home_scores['PTS'].values[0]) else 0
                away_score = int(away_scores['PTS'].values[0]) if pd.notna(away_scores['PTS'].values[0]) else 0
                actual_winner = "HOME_WIN" if home_score > away_score else "AWAY_WIN"
                
                results.append({
                    'game_id': game_id,
                    'game_date': date_str,
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_score': home_score,
                    'away_score': away_score,
                    'actual_winner': actual_winner
                })
        
        logger.info(f"Found {len(results)} completed games")
        return results
        
    except Exception as e:
        logger.error(f"Error fetching results: {e}")
        return []


def save_results(conn, results):
    """Save actual results to database."""
    cursor = conn.cursor()
    for r in results:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO results 
                (game_id, game_date, home_team, away_team, home_score, away_score, actual_winner, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r['game_id'], r['game_date'], r['home_team'], r['away_team'],
                r['home_score'], r['away_score'], r['actual_winner'],
                datetime.now().isoformat()
            ))
        except Exception as e:
            logger.warning(f"Could not save result: {e}")
    conn.commit()


def save_predictions(conn, predictions):
    """Save today's predictions to database."""
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    
    for p in predictions:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO predictions 
                (game_id, game_date, home_team, away_team, predicted_winner, home_win_prob, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                p.get('game_id', ''),
                today,
                p.get('home_team', ''),
                p.get('away_team', ''),
                p.get('prediction', ''),
                p.get('home_win_probability', 0),
                p.get('confidence', 0),
                datetime.now().isoformat()
            ))
        except Exception as e:
            logger.warning(f"Could not save prediction: {e}")
    conn.commit()
    logger.info(f"Saved {len(predictions)} predictions")


def calculate_accuracy(conn, date=None):
    """Calculate accuracy for a specific date."""
    if date is None:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    cursor = conn.cursor()
    
    # Join predictions with results
    cursor.execute("""
        SELECT 
            p.game_id,
            p.home_team,
            p.away_team,
            p.predicted_winner,
            p.confidence,
            r.actual_winner,
            CASE WHEN p.predicted_winner = r.actual_winner THEN 1 ELSE 0 END as correct
        FROM predictions p
        JOIN results r ON p.game_id = r.game_id
        WHERE p.game_date = ?
    """, (date,))
    
    rows = cursor.fetchall()
    
    if not rows:
        logger.info(f"No matched predictions/results for {date}")
        return None
    
    total = len(rows)
    correct = sum(r[6] for r in rows)
    accuracy = correct / total * 100 if total > 0 else 0
    avg_conf = sum(r[4] for r in rows) / total if total > 0 else 0
    
    # Log to accuracy table
    cursor.execute("""
        INSERT INTO accuracy_log (date, total_games, correct_predictions, accuracy, avg_confidence, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (date, total, correct, accuracy, avg_conf, datetime.now().isoformat()))
    conn.commit()
    
    logger.info(f"📊 Accuracy for {date}: {correct}/{total} = {accuracy:.1f}%")
    
    # Print detailed results
    print("\n" + "="*60)
    print(f"ACCURACY REPORT FOR {date}")
    print("="*60)
    for row in rows:
        result = "✅" if row[6] else "❌"
        print(f"{result} {row[1]} vs {row[2]}: Predicted {row[3]}, Actual {row[5]}")
    print(f"\nTOTAL: {correct}/{total} correct ({accuracy:.1f}%)")
    print("="*60)
    
    return {
        'date': date,
        'total': total,
        'correct': correct,
        'accuracy': accuracy,
        'avg_confidence': avg_conf
    }


def get_historical_accuracy(conn, days=30):
    """Get accuracy over the last N days."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT date, total_games, correct_predictions, accuracy 
        FROM accuracy_log 
        ORDER BY date DESC 
        LIMIT ?
    """, (days,))
    
    rows = cursor.fetchall()
    if rows:
        total_games = sum(r[1] for r in rows)
        total_correct = sum(r[2] for r in rows)
        overall = total_correct / total_games * 100 if total_games > 0 else 0
        
        print(f"\n📈 LAST {len(rows)} DAYS ACCURACY:")
        print(f"   {total_correct}/{total_games} = {overall:.1f}%")
    
    return rows


def run_todays_predictions():
    """Run predictions for today's games using the API."""
    import requests
    
    try:
        # Start the API if not running (async approach would be better)
        response = requests.get("http://localhost:8000/predictions", timeout=5)
        if response.ok:
            data = response.json()
            return data.get('predictions', [])
    except Exception as e:
        logger.warning(f"API not available: {e}")
        logger.info("Please start the API: poetry run python src/api/ensemble_predictions.py")
    
    return []


def main():
    """Main daily runner."""
    print("="*60)
    print("🏀 NBA PREDICTION DAILY RUNNER")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Initialize database
    conn = init_database()
    
    # Step 1: Fetch yesterday's actual results
    print("\n📥 Fetching yesterday's results...")
    results = get_yesterdays_results()
    if results:
        save_results(conn, results)
    
    # Step 2: Calculate accuracy for yesterday
    print("\n📊 Calculating accuracy...")
    calculate_accuracy(conn)
    
    # Step 3: Show historical accuracy
    get_historical_accuracy(conn)
    
    # Step 4: Run today's predictions
    print("\n🔮 Running today's predictions...")
    predictions = run_todays_predictions()
    if predictions:
        save_predictions(conn, predictions)
        print(f"   Saved {len(predictions)} predictions for today")
    else:
        print("   No predictions generated (API may not be running)")
    
    conn.close()
    print("\n✅ Daily run complete!")


if __name__ == "__main__":
    main()
