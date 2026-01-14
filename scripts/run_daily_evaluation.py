import argparse
import pandas as pd
import json
import logging
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from nba_api.stats.endpoints import ScoreboardV2

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DailyEvaluation")

METRICS_FILE = Path("data/metrics/daily_accuracy.csv")

def ensure_metrics_file():
    """Ensure the metrics CSV exists with headers."""
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not METRICS_FILE.exists():
        with open(METRICS_FILE, 'w') as f:
            f.write("date,evaluated_at,total_games,correct,accuracy,avg_confidence,model_version,notes\n")

def load_predictions(date_str):
    """Load predictions from JSONL file."""
    file_path = Path(f"data/predictions/{date_str}.jsonl")
    if not file_path.exists():
        logger.warning(f"No prediction file found for {date_str} at {file_path}")
        return []
    
    preds = []
    with open(file_path, 'r') as f:
        for line in f:
            preds.append(json.loads(line))
    return preds

def fetch_actual_scores(date_str):
    """Fetch actual scores using NBA API."""
    logger.info(f"Fetching actual scores for {date_str}...")
    
    # NBA API expects MM/DD/YYYY
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    nba_date = dt.strftime("%m/%d/%Y")
    
    try:
        # Retry logic for NBA API
        attempts = 0
        while attempts < 3:
            try:
                scoreboard = ScoreboardV2(game_date=nba_date)
                games = scoreboard.game_header.get_data_frame()
                line_scores = scoreboard.line_score.get_data_frame()
                break
            except Exception as e:
                attempts += 1
                logger.warning(f"NBA API attempt {attempts} failed: {e}")
                time.sleep(2)
        else:
            logger.error("Failed to fetch scores after 3 attempts")
            return []

        results = {}
        if games is None or games.empty:
            logger.warning("No games found in ScoreboardV2")
            return []

        # Use to_dict('records') for performance
        game_records = games.to_dict('records')
        for game in game_records:
            game_id = game['GAME_ID']
            home_team_id = game['HOME_TEAM_ID']
            visitor_team_id = game['VISITOR_TEAM_ID']
            
            # Find scores
            home_row = line_scores[line_scores['TEAM_ID'] == home_team_id]
            visitor_row = line_scores[line_scores['TEAM_ID'] == visitor_team_id]
            
            if not home_row.empty and not visitor_row.empty:
                h_pts = home_row['PTS'].values[0]
                v_pts = visitor_row['PTS'].values[0]
                
                # Only count finished games (rough check, or check STATUS_ID)
                # STATUS_ID 3 = Final
                if game['GAME_STATUS_ID'] == 3:
                     winner = "HOME" if h_pts > v_pts else "AWAY"
                     # Store by team identifiers to help matching
                     # Ideally use game_id if we have it in predictions
                     results[game_id] = {
                         "winner": winner, 
                         "home_pts": h_pts, 
                         "away_pts": v_pts
                     }
        
        logger.info(f"Fetched {len(results)} final scores")
        return results

    except Exception as e:
        logger.error(f"Error processing scores: {e}")
        return []

def evaluate(predictions, actuals):
    """Compare predictions against actuals."""
    total = 0
    correct = 0
    conf_sum = 0
    
    # Mapping needed? 
    # Predictions usually have string ID "00224000..."
    # Actuals keys are also IDs.
    
    for p in predictions:
        game_id = p.get('game_id')
        
        # Some providers use different ID formats, fallback to team strings if needed
        # But our pipeline uses NBA API IDs hopefully
        
        actual = actuals.get(game_id)
        
        # If not found by ID, could try soft matching by teams (skipped for MVP reliability)
        
        if actual:
            total += 1
            predicted_winner = "HOME" if "HOME" in p['prediction'] else "AWAY"
            
            is_correct = (predicted_winner == actual['winner'])
            if is_correct:
                correct += 1
            
            conf_sum += p.get('confidence', 0)
            
            match_icon = "✅" if is_correct else "❌"
            logger.info(f"{match_icon} {p['home_team']} vs {p['away_team']} | Pred: {predicted_winner} | Act: {actual['winner']}")
            
    return total, correct, conf_sum

def log_metrics(date_str, total, correct, conf_sum, model_version="v2"):
    ensure_metrics_file()
    
    accuracy = round((correct / total * 100), 2) if total > 0 else 0
    avg_conf = round((conf_sum / total), 2) if total > 0 else 0
    
    with open(METRICS_FILE, 'a') as f:
        f.write(f"{date_str},{datetime.now().isoformat()},{total},{correct},{accuracy},{avg_conf},{model_version},\n")
    
    logger.info(f"📈 Logged metrics for {date_str}: {accuracy}% ({correct}/{total})")

def main():
    parser = argparse.ArgumentParser(description="Run daily evaluation")
    parser.add_argument("--date", type=str, help="Date to evaluate (YYYY-MM-DD)", default=None)
    args = parser.parse_args()
    
    # Default to yesterday if no date provided
    target_date = args.date or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    logger.info(f"🧐 Starting evaluation for {target_date}")
    
    predictions = load_predictions(target_date)
    if not predictions:
        logger.warning("No predictions to evaluate.")
        return

    actuals = fetch_actual_scores(target_date)
    if not actuals:
        # Warning already logged
        return

    total, correct, conf_sum = evaluate(predictions, actuals)
    
    if total > 0:
        log_metrics(target_date, total, correct, conf_sum)
    else:
        logger.warning("No matched games found between predictions and actuals.")

if __name__ == "__main__":
    main()
