import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
import os
import asyncio

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.prediction_pipeline import PredictionPipeline

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
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

async def run_pipeline(target_date):
    pipeline = PredictionPipeline()
    return await pipeline.get_predictions(date=target_date, use_live_odds=True)

def main():
    parser = argparse.ArgumentParser(description="Run daily NBA predictions")
    parser.add_argument("--date", type=str, help="Date to predict for (YYYY-MM-DD)", default=None)
    args = parser.parse_args()
    
    target_date = args.date or datetime.now().strftime("%Y-%m-%d")
    logger.info(f"🚀 Starting prediction job for {target_date}")
    
    try:
        predictions = asyncio.run(run_pipeline(target_date))
        
        if not predictions:
            logger.warning(f"⚠️ No predictions generated for {target_date}")
            # We still might want to save an empty file or log this event, 
            # but for now we just exit safely.
            return
            
        save_predictions(predictions, target_date)
        
        # Also update a 'latest.json' for easy frontend access if needed
        # (Though frontend currently uses API, this is good for static site generators)
        
    except Exception as e:
        logger.error(f"❌ Critical error in prediction job: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
