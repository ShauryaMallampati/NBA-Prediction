"""
Retrain Ensemble on Historical Data (Pre-2024-25 Season)
Purpose: create a model that has NOT seen 2024-25 or 2025-26 data, 
allowing for a valid "Time Machine" evaluation of the last 2 seasons.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Reuse feature engineering from train_full_dataset
from src.common.features import calculate_elo, add_rest_features, add_streak_features, add_schedule_features
from src.models.pregame.train_ensemble import EnsembleTrainer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HistoricalRetrain")

DATA_PATH = Path("data/nba_games_enhanced.csv")
# Cutoff: Start of 2024-25 Season is roughly Oct 22, 2024. 
# We train on everything BEFORE this.
CUTOFF_DATE = "2024-10-01" 
OUTPUT_DIR = Path("artifacts/models/historical_2024")
OUTPUT_FEATURES = Path("artifacts/features/historical_2024.parquet")

def main():
    logger.info(f"⏳ Starting Historical Retraining (Data < {CUTOFF_DATE})")
    
    # 1. Load & Filter Data
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    initial_len = len(df)
    
    # FILTER: Only keep games strictly before the 2024-25 season start
    train_df = df[df['date'] < CUTOFF_DATE].copy().reset_index(drop=True)
    
    logger.info(f"   Original Games: {initial_len:,}")
    logger.info(f"   Training Games: {len(train_df):,} (Up to {train_df['date'].max().date()})")
    
    # 2. Feature Engineering (Recalculate ELO just for training set to avoid leakage? 
    # Actually, ELO is progressive. We can run it on the truncated set.)
    
    logger.info("🔧 Re-engineering features for historical set...")
    train_df = calculate_elo(train_df)
    train_df = add_rest_features(train_df)
    train_df = add_streak_features(train_df)
    train_df = add_schedule_features(train_df)
    
    # Prepare Features
    feature_cols = [
        'elo_home', 'elo_away', 'elo_p_home', 'elo_diff', 'elo_win_prob',
        'home_adv_flag', 'home_court_adv',
        'home_injury_count', 'away_injury_count',
        'home_key_player_injured', 'away_key_player_injured',
        'home_rest_days', 'away_rest_days', 'rest_differential',
        'home_rest_advantage', 'away_rest_advantage',
        'home_back_to_back', 'away_back_to_back',
        'is_playoff',
        'home_win_streak', 'away_win_streak',
        'home_loss_streak', 'away_loss_streak',
        'home_games_last_7_days', 'away_games_last_7_days',
        'home_fatigue_score', 'away_fatigue_score',
        'home_game_number', 'away_game_number',
        'home_season_phase', 'away_season_phase',
    ]
    
    output_cols = ['game_id', 'date', 'home', 'away', 'home_pts', 'away_pts', 'home_win'] + feature_cols
    df_features = train_df[output_cols].copy()
    df_features = df_features.rename(columns={'home': 'home_team', 'away': 'away_team'})
    
    OUTPUT_FEATURES.parent.mkdir(parents=True, exist_ok=True)
    df_features.to_parquet(OUTPUT_FEATURES, index=False)
    
    # 3. Train Models
    logger.info(f"🎯 Training Historical Ensemble Models -> {OUTPUT_DIR}")
    
    trainer = EnsembleTrainer(output_dir=str(OUTPUT_DIR))
    X, y = trainer.load_data(str(OUTPUT_FEATURES))
    
    # Train robustly
    metrics = trainer.train_all(X, y, cv_folds=5)
    trainer.save_models()
    
    logger.info(f"✅ Historical Ensemble Models Saved to {OUTPUT_DIR}")
    
    # 4. Train Momentum Transformer (also historical)
    logger.info("\n" + "=" * 50)
    logger.info("⏳ Starting Historical Momentum Training...")
    logger.info("=" * 50)
    
    import subprocess
    momentum_out_dir = OUTPUT_DIR / "momentum"
    momentum_out_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        sys.executable, "scripts/train_momentum_transformer.py",
        "--max_date", CUTOFF_DATE,
        "--output_dir", str(momentum_out_dir)
    ]
    
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"✅ Historical Momentum Model Saved to {momentum_out_dir}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Momentum Training Failed: {e}")
        # Don't exit, we at least have the ensemble
    
    logger.info("\n✅ ALL Historical Retraining Complete!")
    logger.info(f"   Model Directory: {OUTPUT_DIR}")
    logger.info("   You can now run streaming_world_model_eval.py with this directory.")

if __name__ == "__main__":
    main()
