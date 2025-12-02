"""
Continuous Training - Automatically collect more games and retrain
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def collect_more_games(current_games=250, target_games=500):
    """Collect more games beyond current dataset"""
    from src.data.live_playbyplay import playbyplay_fetcher
    
    logger.info(f"🎯 Target: Collect {target_games} total games")
    logger.info(f"📊 Current: {current_games} games")
    logger.info(f"➕ Need to collect: {target_games - current_games} more games")
    
    # Check existing games
    pbp_dir = Path("data/playbyplay")
    existing_files = list(pbp_dir.glob("00*.parquet"))
    logger.info(f"✅ Found {len(existing_files)} existing game files")
    
    if len(existing_files) >= target_games:
        logger.info(f"✅ Already have {len(existing_files)} games!")
        return len(existing_files)
    
    # Fetch more games
    logger.info(f"📥 Fetching {target_games} games from NBA...")
    pbp_df = playbyplay_fetcher.get_current_season_data(max_games=target_games)
    
    if len(pbp_df) > 0:
        logger.info(f"✅ Successfully collected play-by-play data")
        return target_games
    else:
        logger.error("❌ Failed to collect additional games")
        return len(existing_files)

def auto_retrain(games_collected):
    """Automatically retrain models when enough new data is available"""
    logger.info(f"\n{'='*80}")
    logger.info("🎓 AUTO-RETRAINING MODELS")
    logger.info(f"{'='*80}")
    
    import subprocess
    
    try:
        # Run the training script
        result = subprocess.run(
            ['python', 'scripts/train_final.py'],
            capture_output=True,
            text=True
        )
        
        logger.info(result.stdout)
        
        if result.returncode == 0:
            logger.info("✅ Models retrained successfully!")
            
            # Save training metadata
            metadata = {
                'training_date': datetime.now().isoformat(),
                'games_used': games_collected,
                'model_version': datetime.now().strftime('%Y%m%d_%H%M%S')
            }
            
            import json
            with open('models/ensemble/training_metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return True
        else:
            logger.error(f"❌ Training failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Auto-retrain failed: {e}")
        return False

def main():
    print("=" * 80)
    print("🔄 CONTINUOUS TRAINING SYSTEM")
    print("=" * 80)
    
    # Step 1: Collect more games
    print("\n📊 STEP 1: Collecting More Games")
    games_collected = collect_more_games(current_games=250, target_games=500)
    
    # Step 2: Retrain if we have enough data
    if games_collected >= 400:
        print("\n🎓 STEP 2: Retraining Models")
        success = auto_retrain(games_collected)
        
        if success:
            print("\n" + "=" * 80)
            print("✅ CONTINUOUS TRAINING COMPLETE!")
            print("=" * 80)
            print(f"📊 Total Games: {games_collected}")
            print("🎓 Models retrained and saved")
            print("=" * 80)
        else:
            print("\n⚠️  Training failed - models not updated")
    else:
        print(f"\n⏳ Need {400 - games_collected} more games before retraining")
        print(f"   Current: {games_collected}, Target: 400")

if __name__ == "__main__":
    main()
