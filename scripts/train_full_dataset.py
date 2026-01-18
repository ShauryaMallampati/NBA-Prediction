#!/usr/bin/env python3
"""
Generate Features for Full 72k Dataset and Retrain Ensemble

This script:
1. Loads all 72,560 historical games
2. Engineers ELO ratings and other features
3. Retrains the ensemble on the full dataset
4. Evaluates on a true 15% holdout test set
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.common.features import calculate_elo, add_rest_features, add_streak_features, add_schedule_features

# Paths
DATA_PATH = Path("data/nba_games_enhanced.csv")
OUTPUT_FEATURES = Path("artifacts/features/pregame_full.parquet")
OUTPUT_DIR = Path("artifacts/models/pregame")


# Features are now imported from src.common.features


def main():
    print("=" * 70)
    print("🏀 FULL DATASET FEATURE ENGINEERING & RETRAINING")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Load data
    logger.info(f"\n📂 Loading data from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    logger.info(f"✅ Loaded {len(df):,} games")
    logger.info(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Filter to modern era (post-1980 for better relevance)
    df['date'] = pd.to_datetime(df['date'])
    df = df[df['date'] >= '1980-01-01'].reset_index(drop=True)
    logger.info(f"📍 Filtered to modern era: {len(df):,} games (1980+)")
    
    # Calculate ELO
    df = calculate_elo(df)
    
    # Add features
    df = add_rest_features(df)
    df = add_streak_features(df)
    df = add_schedule_features(df)
    
    # Prepare final feature set
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
    
    # Keep identifiers and target
    output_cols = ['game_id', 'date', 'home', 'away', 'home_pts', 'away_pts', 'home_win'] + feature_cols
    df_features = df[output_cols].copy()
    
    # Rename for compatibility
    df_features = df_features.rename(columns={'home': 'home_team', 'away': 'away_team'})
    
    # Save features
    OUTPUT_FEATURES.parent.mkdir(parents=True, exist_ok=True)
    df_features.to_parquet(OUTPUT_FEATURES, index=False)
    logger.info(f"\n💾 Saved features to {OUTPUT_FEATURES}")
    logger.info(f"   Games: {len(df_features):,}")
    logger.info(f"   Features: {len(feature_cols)}")
    
    # Now train the ensemble
    print("\n" + "=" * 70)
    print("🎯 TRAINING ENSEMBLE ON FULL DATASET")
    print("=" * 70)
    
    from src.models.pregame.train_ensemble import EnsembleTrainer
    
    trainer = EnsembleTrainer(output_dir=str(OUTPUT_DIR))
    X, y = trainer.load_data(str(OUTPUT_FEATURES))
    
    # Train
    metrics = trainer.train_all(X, y, cv_folds=5)
    
    # Save
    trainer.save_models()
    
    # Now evaluate on holdout
    print("\n" + "=" * 70)
    print("🧪 HOLDOUT TEST SET EVALUATION")
    print("=" * 70)
    
    # Split: 85% train, 15% test (time-based)
    split_idx = int(len(X) * 0.85)
    X_test = X.iloc[split_idx:]
    y_test = y.iloc[split_idx:]
    
    # Predict
    from sklearn.metrics import accuracy_score, roc_auc_score
    
    ensemble_pred = trainer.predict_ensemble(X_test)
    ensemble_pred_binary = (ensemble_pred > 0.5).astype(int)
    
    holdout_acc = accuracy_score(y_test, ensemble_pred_binary)
    holdout_auc = roc_auc_score(y_test, ensemble_pred)
    
    print(f"\n📊 RESULTS ON {len(y_test):,} UNSEEN GAMES (Last 15%):")
    print(f"   ✅ Holdout Accuracy: {holdout_acc:.2%} ({holdout_acc*100:.2f}%)")
    print(f"   📈 Holdout AUC-ROC:  {holdout_auc:.4f}")
    
    # Save results
    import json
    results = {
        'timestamp': datetime.now().isoformat(),
        'dataset': {
            'total_games': len(X),
            'train_games': split_idx,
            'test_games': len(y_test),
            'date_range': f"{df_features['date'].min()} to {df_features['date'].max()}",
        },
        'cv_metrics': {
            'xgb_cv_accuracy': float(np.mean([s['accuracy'] for s in metrics['xgb']['cv_scores']])),
            'lgb_cv_accuracy': float(np.mean([s['accuracy'] for s in metrics['lgb']['cv_scores']])),
            'cat_cv_accuracy': float(np.mean([s['accuracy'] for s in metrics['cat']['cv_scores']])),
        },
        'holdout_metrics': {
            'accuracy': float(holdout_acc),
            'auc': float(holdout_auc),
            'n_games': len(y_test),
        }
    }
    
    with open(OUTPUT_DIR / "full_dataset_results.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n" + "=" * 70)
    print("✅ TRAINING COMPLETE!")
    print("=" * 70)
    print(f"   Dataset: {len(X):,} games (1980-present)")
    print(f"   Holdout Test: {len(y_test):,} games")
    print(f"   Holdout Accuracy: {holdout_acc:.2%}")
    print(f"   Results saved to: {OUTPUT_DIR / 'full_dataset_results.json'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
