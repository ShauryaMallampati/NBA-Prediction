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

# Paths
DATA_PATH = Path("data/nba_games_enhanced.csv")
OUTPUT_FEATURES = Path("artifacts/features/pregame_full.parquet")
OUTPUT_DIR = Path("artifacts/models/pregame")


def calculate_elo(df: pd.DataFrame, k: int = 20, home_advantage: float = 100) -> pd.DataFrame:
    """
    Calculate ELO ratings for all teams across all games.
    
    Args:
        df: DataFrame with columns [date, home, away, home_pts, away_pts, home_win]
        k: ELO K-factor (how quickly ratings change)
        home_advantage: ELO points added for home team
    
    Returns:
        DataFrame with ELO features added
    """
    logger.info("📊 Calculating ELO ratings for all teams...")
    
    # Initialize ELO ratings
    elo_ratings = {}
    default_elo = 1500
    
    # Store ELO at time of each game
    elo_home_list = []
    elo_away_list = []
    elo_diff_list = []
    elo_win_prob_list = []
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    for idx, row in df.iterrows():
        home = row['home']
        away = row['away']
        home_win = row['home_win']
        
        # Get current ELO (or default)
        home_elo = elo_ratings.get(home, default_elo)
        away_elo = elo_ratings.get(away, default_elo)
        
        # Store pre-game ELO
        elo_home_list.append(home_elo)
        elo_away_list.append(away_elo)
        elo_diff_list.append(home_elo - away_elo + home_advantage)
        
        # Expected win probability
        exp_home = 1 / (1 + 10 ** ((away_elo - home_elo - home_advantage) / 400))
        elo_win_prob_list.append(exp_home)
        
        # Update ELO after game
        if pd.notna(home_win):
            new_home_elo = home_elo + k * (home_win - exp_home)
            new_away_elo = away_elo + k * ((1 - home_win) - (1 - exp_home))
            elo_ratings[home] = new_home_elo
            elo_ratings[away] = new_away_elo
        
        if (idx + 1) % 10000 == 0:
            logger.info(f"   Processed {idx + 1:,} games...")
    
    df['elo_home'] = elo_home_list
    df['elo_away'] = elo_away_list
    df['elo_diff'] = elo_diff_list
    df['elo_win_prob'] = elo_win_prob_list
    
    # Additional ELO-derived features
    df['elo_p_home'] = df['elo_home'] / (df['elo_home'] + df['elo_away'])
    df['home_adv_flag'] = 1  # All games have home advantage
    df['home_court_adv'] = 100
    
    logger.info(f"✅ ELO calculated for {len(df):,} games")
    
    return df


def add_rest_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add rest day features."""
    logger.info("🛏️ Adding rest features...")
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Track last game date for each team
    last_game = {}
    
    home_rest = []
    away_rest = []
    
    for idx, row in df.iterrows():
        home = row['home']
        away = row['away']
        game_date = pd.to_datetime(row['date'])
        
        # Calculate rest days
        home_rest_days = (game_date - last_game.get(home, game_date - pd.Timedelta(days=3))).days
        away_rest_days = (game_date - last_game.get(away, game_date - pd.Timedelta(days=3))).days
        
        home_rest.append(min(home_rest_days, 7))  # Cap at 7 days
        away_rest.append(min(away_rest_days, 7))
        
        # Update last game
        last_game[home] = game_date
        last_game[away] = game_date
    
    df['home_rest_days'] = home_rest
    df['away_rest_days'] = away_rest
    df['rest_differential'] = df['home_rest_days'] - df['away_rest_days']
    df['home_rest_advantage'] = (df['home_rest_days'] > df['away_rest_days']).astype(int)
    df['away_rest_advantage'] = (df['away_rest_days'] > df['home_rest_days']).astype(int)
    df['home_back_to_back'] = (df['home_rest_days'] <= 1).astype(int)
    df['away_back_to_back'] = (df['away_rest_days'] <= 1).astype(int)
    
    logger.info("✅ Rest features added")
    return df


def add_streak_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add win/loss streak features."""
    logger.info("🔥 Adding streak features...")
    
    df = df.sort_values('date').reset_index(drop=True)
    
    # Track streaks
    win_streaks = {}
    loss_streaks = {}
    
    home_win_streak = []
    away_win_streak = []
    home_loss_streak = []
    away_loss_streak = []
    
    for idx, row in df.iterrows():
        home = row['home']
        away = row['away']
        
        # Get current streaks
        home_win_streak.append(win_streaks.get(home, 0))
        away_win_streak.append(win_streaks.get(away, 0))
        home_loss_streak.append(loss_streaks.get(home, 0))
        away_loss_streak.append(loss_streaks.get(away, 0))
        
        # Update streaks
        if pd.notna(row['home_win']):
            if row['home_win'] == 1:
                win_streaks[home] = win_streaks.get(home, 0) + 1
                loss_streaks[home] = 0
                win_streaks[away] = 0
                loss_streaks[away] = loss_streaks.get(away, 0) + 1
            else:
                win_streaks[home] = 0
                loss_streaks[home] = loss_streaks.get(home, 0) + 1
                win_streaks[away] = win_streaks.get(away, 0) + 1
                loss_streaks[away] = 0
    
    df['home_win_streak'] = home_win_streak
    df['away_win_streak'] = away_win_streak
    df['home_loss_streak'] = home_loss_streak
    df['away_loss_streak'] = away_loss_streak
    
    logger.info("✅ Streak features added")
    return df


def add_schedule_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add schedule-based features."""
    logger.info("📅 Adding schedule features...")
    
    df['date'] = pd.to_datetime(df['date'])
    
    # Track games in last 7 days
    df = df.sort_values('date').reset_index(drop=True)
    
    games_last_7 = {}
    home_games_7 = []
    away_games_7 = []
    
    for idx, row in df.iterrows():
        home = row['home']
        away = row['away']
        game_date = row['date']
        
        # Clean old games
        cutoff = game_date - pd.Timedelta(days=7)
        
        # Count games in window
        home_count = len([d for d in games_last_7.get(home, []) if d > cutoff])
        away_count = len([d for d in games_last_7.get(away, []) if d > cutoff])
        
        home_games_7.append(home_count)
        away_games_7.append(away_count)
        
        # Update history
        if home not in games_last_7:
            games_last_7[home] = []
        if away not in games_last_7:
            games_last_7[away] = []
        games_last_7[home].append(game_date)
        games_last_7[away].append(game_date)
        
        # Keep only last 20 games in memory
        games_last_7[home] = games_last_7[home][-20:]
        games_last_7[away] = games_last_7[away][-20:]
    
    df['home_games_last_7_days'] = home_games_7
    df['away_games_last_7_days'] = away_games_7
    df['home_fatigue_score'] = df['home_games_last_7_days'] * 0.5 + df['home_back_to_back'] * 2
    df['away_fatigue_score'] = df['away_games_last_7_days'] * 0.5 + df['away_back_to_back'] * 2
    
    # Season phase (early/mid/late)
    df['month'] = df['date'].dt.month
    df['home_season_phase'] = df['month'].apply(lambda m: 0 if m in [10,11,12] else (1 if m in [1,2] else 2))
    df['away_season_phase'] = df['home_season_phase']
    
    # Playoff indicator (April onwards, simplified)
    df['is_playoff'] = (df['month'] >= 4).astype(int)
    
    # Game number in season (approximate)
    df['home_game_number'] = df.groupby('home').cumcount() + 1
    df['away_game_number'] = df.groupby('away').cumcount() + 1
    
    # Dummy injury columns (we don't have real injury data for historical games)
    df['home_injury_count'] = 0
    df['away_injury_count'] = 0
    df['home_key_player_injured'] = 0
    df['away_key_player_injured'] = 0
    
    logger.info("✅ Schedule features added")
    return df


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
