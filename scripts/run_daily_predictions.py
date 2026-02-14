import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.pregame.predictor import EnsemblePredictor

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("DailyPredictions")

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def save_predictions(predictions, date_str):
    """Save predictions to data/predictions/YYYY-MM-DD.jsonl"""
    output_dir = Path("data/predictions")
    ensure_dir(output_dir)
    
    filename = output_dir / f"{date_str}.jsonl"
    
    logger.info(f"Saving {len(predictions)} predictions to {filename}")
    
    with open(filename, 'w') as f:
        for pred in predictions:
            # Enrich with created_at timestamp
            pred['created_at'] = datetime.now().isoformat()
            f.write(json.dumps(pred) + "\n")
            
    logger.info("✅ Save complete")

def main():
    parser = argparse.ArgumentParser(description="Run daily NBA pregame predictions")
    parser.add_argument("--date", type=str, help="Date to predict for (YYYY-MM-DD)", default=None)
    args = parser.parse_args()

    target_date = args.date or datetime.now().strftime("%Y-%m-%d")
    logger.info(f"🚀 Starting pregame prediction job for {target_date}")

    features_path = Path("artifacts/features/pregame.parquet")
    if not features_path.exists():
        logger.error("Missing features. Run `make data` first.")
        sys.exit(1)

    try:
        df = pd.read_parquet(features_path)
        if "date" in df.columns:
            df["date_str"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        if "date_str" in df.columns:
            df = df[df["date_str"] == target_date]

        if df.empty:
            logger.warning(f"⚠️ No games found for {target_date}")
            return

        predictor = EnsemblePredictor("artifacts/models/pregame")
        predictions = predictor.predict_with_features(df, top_n=5)

        output = []
        for i, row in enumerate(df.to_dict("records")):
            pred_data = predictions[i]
            output.append({
                "game_id": row.get("game_id", f"game_{i}"),
                "date": row.get("date", target_date),
                "home_team": row.get("home_team", row.get("home", "Unknown")),
                "away_team": row.get("away_team", row.get("away", "Unknown")),
                "home_win_prob": float(pred_data["prediction"]),
                "away_win_prob": float(1 - pred_data["prediction"]),
                "top_features": pred_data["top_features"],
            })

        save_predictions(output, target_date)

    except Exception as e:
        logger.error(f"❌ Critical error in prediction job: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
