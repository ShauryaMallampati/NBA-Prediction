"""
Sync predictions and evaluations to Supabase.

This script is designed to run in GitHub Actions after daily predictions.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.supabase_client import get_supabase_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SyncToSupabase")


def load_predictions_for_date(date_str: str) -> list:
    """Load predictions from JSONL file."""
    file_path = Path(f"data/predictions/{date_str}.jsonl")
    if not file_path.exists():
        logger.warning(f"No prediction file for {date_str}")
        return []
    
    predictions = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.strip():
                predictions.append(json.loads(line))
    return predictions


def load_evaluation_for_date(date_str: str) -> dict:
    """Load evaluation from metrics CSV."""
    import pandas as pd
    
    csv_path = Path("data/metrics/daily_accuracy.csv")
    if not csv_path.exists():
        return {}
    
    df = pd.read_csv(csv_path)
    row = df[df['date'] == date_str]
    
    if row.empty:
        return {}
    
    row = row.iloc[0]
    return {
        "date": date_str,
        "total_games": int(row.get("total_games", 0)),
        "correct": int(row.get("correct", 0)),
        "accuracy": float(row.get("accuracy", 0)),
        "avg_confidence": float(row.get("avg_confidence", 0)),
        "model_version": row.get("model_version", "ensemble_v2"),
    }


def sync_today_predictions():
    """Sync today's predictions to Supabase."""
    today = datetime.now().strftime("%Y-%m-%d")
    predictions = load_predictions_for_date(today)
    
    if not predictions:
        logger.info(f"No predictions for {today} to sync")
        return 0
    
    client = get_supabase_client()
    count = client.insert_predictions_batch(predictions)
    logger.info(f"✅ Synced {count} predictions for {today}")
    return count


def sync_yesterday_evaluation():
    """Sync yesterday's evaluation to Supabase."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    evaluation = load_evaluation_for_date(yesterday)
    
    if not evaluation:
        logger.info(f"No evaluation for {yesterday} to sync")
        return False
    
    client = get_supabase_client()
    success = client.insert_evaluation(evaluation)
    if success:
        logger.info(f"✅ Synced evaluation for {yesterday}")
    return success


def sync_all_historical():
    """Sync all historical predictions and evaluations."""
    client = get_supabase_client()
    
    # Sync all predictions
    predictions_dir = Path("data/predictions")
    if predictions_dir.exists():
        for jsonl_file in predictions_dir.glob("*.jsonl"):
            date_str = jsonl_file.stem
            predictions = load_predictions_for_date(date_str)
            if predictions:
                count = client.insert_predictions_batch(predictions)
                logger.info(f"Synced {count} predictions for {date_str}")
    
    # Sync all evaluations
    import pandas as pd
    csv_path = Path("data/metrics/daily_accuracy.csv")
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            evaluation = {
                "date": row["date"],
                "total_games": int(row.get("total_games", 0)),
                "correct": int(row.get("correct", 0)),
                "accuracy": float(row.get("accuracy", 0)),
                "avg_confidence": float(row.get("avg_confidence", 0)),
                "model_version": row.get("model_version", "ensemble_v2"),
            }
            client.insert_evaluation(evaluation)
        logger.info(f"Synced {len(df)} evaluations")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Sync data to Supabase")
    parser.add_argument("--all", action="store_true", help="Sync all historical data")
    args = parser.parse_args()
    
    if args.all:
        logger.info("📦 Syncing all historical data to Supabase...")
        sync_all_historical()
    else:
        logger.info("📦 Syncing today's predictions and yesterday's evaluation...")
        sync_today_predictions()
        sync_yesterday_evaluation()
    
    logger.info("✅ Sync complete!")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
