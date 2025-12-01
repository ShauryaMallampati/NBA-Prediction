"""
Simplified Training Script - Train models with existing data (no live API calls)
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
import joblib
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_existing_data():
    """Load pre-fetched data from data directory"""
    logger.info("📂 Loading existing data...")
    
    # Load play-by-play data (combine all game files)
    pbp_dir = Path("data/playbyplay")
    if pbp_dir.exists():
        pbp_files = list(pbp_dir.glob("00*.parquet"))  # Game files
        if pbp_files:
            pbp_dfs = [pd.read_parquet(f) for f in pbp_files]
            pbp_df = pd.concat(pbp_dfs, ignore_index=True)
            logger.info(f"✅ Loaded {len(pbp_df)} play-by-play actions from {len(pbp_files)} games")
        else:
            # Try the combined file
            combined_file = pbp_dir / "enhanced_pbp.parquet"
            if combined_file.exists():
                pbp_df = pd.read_parquet(combined_file)
                logger.info(f"✅ Loaded {len(pbp_df)} play-by-play actions from combined file")
            else:
                logger.error("❌ No play-by-play data found!")
                return None
    else:
        logger.error("❌ No play-by-play data found!")
        return None
    
    # Load player stats
    stats_file = Path("data/player_stats/season_stats_2024-25.parquet")
    if stats_file.exists():
        stats_df = pd.read_parquet(stats_file)
        logger.info(f"✅ Loaded {len(stats_df)} player stat records")
    else:
        logger.warning("⚠️  No player stats found")
        stats_df = None
    
    # Load injuries
    injury_file = Path("data/injuries/nba_injuries.json")
    if injury_file.exists():
        import json
        with open(injury_file) as f:
            injuries = json.load(f)
        logger.info(f"✅ Loaded {len(injuries)} injury reports")
    else:
        logger.warning("⚠️  No injury data found")
        injuries = []
    
    return pbp_df, stats_df, injuries

def engineer_simple_features(pbp_df):
    """Engineer simple features from play-by-play data"""
    logger.info("🔧 Engineering features from play-by-play data...")
    
    # Convert score columns to numeric
    pbp_df['scoreHome'] = pd.to_numeric(pbp_df['scoreHome'], errors='coerce').fillna(0)
    pbp_df['scoreAway'] = pd.to_numeric(pbp_df['scoreAway'], errors='coerce').fillna(0)
    
    # Group by game
    games = pbp_df.groupby('gameid').agg({
        'scoreHome': 'last',
        'scoreAway': 'last',
        'period': 'max',
        'actionNumber': 'count'  # Total number of events
    }).reset_index()
    
    games.rename(columns={'actionNumber': 'total_events'}, inplace=True)
    
    # Create features
    games['score_diff'] = games['scoreHome'] - games['scoreAway']
    games['total_score'] = games['scoreHome'] + games['scoreAway']
    games['home_win'] = (games['scoreHome'] > games['scoreAway']).astype(int)
    
    # Calculate scoring pace
    games['pace'] = games['total_score'] / games['period']
    
    # Calculate momentum indicators from event sequences
    momentum_features = calculate_momentum(pbp_df)
    games = games.merge(momentum_features, on='gameid', how='left')
    
    logger.info(f"✅ Engineered features for {len(games)} games")
    return games

def calculate_momentum(pbp_df):
    """Calculate momentum shifts from play-by-play"""
    momentum = []
    
    for game_id in pbp_df['gameid'].unique():
        game_pbp = pbp_df[pbp_df['gameid'] == game_id].sort_values('actionNumber')
        
        # Calculate scoring runs
        game_pbp['score_change'] = game_pbp['scoreHome'].diff()
        
        # Momentum: standard deviation of score changes (volatility)
        momentum_vol = game_pbp['score_change'].std() if len(game_pbp) > 1 else 0
        
        # Lead changes
        game_pbp['leader'] = np.sign(game_pbp['scoreHome'] - game_pbp['scoreAway'])
        lead_changes = (game_pbp['leader'].diff() != 0).sum()
        
        momentum.append({
            'gameid': game_id,
            'momentum_volatility': momentum_vol,
            'lead_changes': lead_changes
        })
    
    return pd.DataFrame(momentum)

def train_simple_model(X, y):
    """Train a simple ensemble model with time series cross-validation"""
    logger.info("🎯 Training model with time series cross-validation...")
    
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    
    # Time series split (5 folds)
    tscv = TimeSeriesSplit(n_splits=5)
    
    # Models to ensemble
    models = {
        'rf': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
        'gb': GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42),
        'lr': LogisticRegression(max_iter=1000, random_state=42)
    }
    
    cv_scores = {name: [] for name in models}
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"FOLD {fold}/5")
        logger.info(f"{'='*60}")
        
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        # Standardize features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        for name, model in models.items():
            model.fit(X_train_scaled, y_train)
            score = model.score(X_val_scaled, y_val)
            cv_scores[name].append(score)
            logger.info(f"  {name.upper()}: {score:.4f}")
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("CROSS-VALIDATION SUMMARY")
    logger.info(f"{'='*60}")
    
    for name in models:
        scores = cv_scores[name]
        logger.info(f"{name.upper()}:")
        logger.info(f"  Mean: {np.mean(scores):.4f}")
        logger.info(f"  Std:  {np.std(scores):.4f}")
        logger.info(f"  Scores: {[f'{s:.4f}' for s in scores]}")
    
    # Check for overfitting (high variance)
    for name in models:
        std = np.std(cv_scores[name])
        if std > 0.05:
            logger.warning(f"⚠️  {name.upper()} shows high variance (std={std:.4f}) - possible overfitting!")
        else:
            logger.info(f"✅ {name.upper()} shows low variance (std={std:.4f}) - good generalization!")
    
    # Train final models on all data
    logger.info("\n🎓 Training final models on full dataset...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    final_models = {}
    for name, model in models.items():
        model.fit(X_scaled, y)
        final_models[name] = model
        logger.info(f"✅ Trained final {name.upper()} model")
    
    # Save models
    models_dir = Path("models/ensemble")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(final_models, models_dir / "simple_ensemble.pkl")
    joblib.dump(scaler, models_dir / "scaler.pkl")
    logger.info(f"💾 Saved models to {models_dir}")
    
    return final_models, cv_scores

def main():
    print("=" * 80)
    print("🏀 SIMPLIFIED TRAINING PIPELINE (Using Existing Data)")
    print("=" * 80)
    
    # Load data
    data = load_existing_data()
    if data is None:
        logger.error("Failed to load data. Run scripts/fetch_enhanced_data.py first!")
        return
    
    pbp_df, stats_df, injuries = data
    
    # Engineer features
    games_df = engineer_simple_features(pbp_df)
    
    # Prepare training data
    feature_cols = ['total_score', 'total_events', 'pace', 'momentum_volatility', 'lead_changes']
    X = games_df[feature_cols].fillna(0)
    y = games_df['home_win']
    
    logger.info(f"\n📊 Training Data:")
    logger.info(f"  Games: {len(X)}")
    logger.info(f"  Features: {len(feature_cols)}")
    logger.info(f"  Home Win Rate: {y.mean():.2%}")
    
    # Train model
    models, cv_scores = train_simple_model(X, y)
    
    print("\n" + "=" * 80)
    print("✅ TRAINING COMPLETE!")
    print("=" * 80)
    print(f"📁 Models saved to: models/ensemble/")
    print(f"🎯 Best Model: {max(cv_scores.items(), key=lambda x: np.mean(x[1]))[0].upper()}")
    print("=" * 80)

if __name__ == "__main__":
    main()
