"""
Train Models with Full Features on 200+ Games
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import joblib
import logging
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_processed_data():
    """Load the processed dataset with 200+ games"""
    logger.info("📂 Loading processed dataset...")
    
    data_file = Path("data/processed/games_200plus_full_features.parquet")
    if not data_file.exists():
        logger.error("Data file not found! Run scripts/collect_200_games.py first.")
        return None
    
    df = pd.read_parquet(data_file)
    logger.info(f"✅ Loaded {len(df)} games with {len(df.columns)} features")
    
    return df

def prepare_features(df):
    """Prepare feature matrix and target vector"""
    logger.info("🔧 Preparing features and targets...")
    
    # Drop non-feature columns
    drop_cols = ['gameid', 'home_win', 'scoreHome', 'scoreAway', 'teamId', 'score_diff']
    feature_cols = [col for col in df.columns if col not in drop_cols]
    
    X = df[feature_cols].fillna(0)
    y = df['home_win']
    
    logger.info(f"📊 Feature shape: {X.shape}")
    logger.info(f"🎯 Target distribution: Home wins: {y.mean():.2%}, Away wins: {1-y.mean():.2%}")
    logger.info(f"📋 Features used: {feature_cols}")
    
    return X, y, feature_cols

def train_with_cv(X, y, n_splits=5):
    """Train models with time series cross-validation"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🎯 TRAINING WITH {n_splits}-FOLD TIME SERIES CROSS-VALIDATION")
    logger.info(f"{'='*80}")
    
    # Initialize models
    models = {
        'RandomForest': RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        ),
        'GradientBoosting': GradientBoostingClassifier(
            n_estimators=150,
            max_depth=7,
            learning_rate=0.05,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42
        ),
        'LogisticRegression': LogisticRegression(
            max_iter=2000,
            C=0.1,
            random_state=42
        )
    }
    
    # Time series cross-validation
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    results = {name: {'train_scores': [], 'val_scores': []} for name in models}
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
        logger.info(f"\n{'─'*80}")
        logger.info(f"FOLD {fold}/{n_splits}")
        logger.info(f"{'─'*80}")
        logger.info(f"Train size: {len(train_idx)}, Val size: {len(val_idx)}")
        
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_val_scaled = scaler.transform(X_val)
        
        # Train each model
        for name, model in models.items():
            model.fit(X_train_scaled, y_train)
            
            train_score = model.score(X_train_scaled, y_train)
            val_score = model.score(X_val_scaled, y_val)
            
            results[name]['train_scores'].append(train_score)
            results[name]['val_scores'].append(val_score)
            
            logger.info(f"{name:20s} - Train: {train_score:.4f}, Val: {val_score:.4f}")
    
    # Print summary
    logger.info(f"\n{'='*80}")
    logger.info("CROSS-VALIDATION SUMMARY")
    logger.info(f"{'='*80}")
    
    for name in models:
        train_scores = results[name]['train_scores']
        val_scores = results[name]['val_scores']
        
        train_mean, train_std = np.mean(train_scores), np.std(train_scores)
        val_mean, val_std = np.mean(val_scores), np.std(val_scores)
        
        logger.info(f"\n{name}:")
        logger.info(f"  Train: {train_mean:.4f} ± {train_std:.4f}")
        logger.info(f"  Val:   {val_mean:.4f} ± {val_std:.4f}")
        logger.info(f"  Gap:   {train_mean - val_mean:.4f}")
        
        # Check overfitting
        if val_std > 0.08:
            logger.warning(f"  ⚠️  High variance (std={val_std:.4f}) - possible instability")
        elif train_mean - val_mean > 0.10:
            logger.warning(f"  ⚠️  Train-val gap = {train_mean - val_mean:.4f} - possible overfitting")
        else:
            logger.info(f"  ✅ Good generalization!")
    
    return models, results

def train_final_models(X, y, feature_cols):
    """Train final models on all data"""
    logger.info(f"\n{'='*80}")
    logger.info("🎓 TRAINING FINAL MODELS ON FULL DATASET")
    logger.info(f"{'='*80}")
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train models with optimized hyperparameters
    final_models = {
        'rf': RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        ),
        'gb': GradientBoostingClassifier(
            n_estimators=150,
            max_depth=7,
            learning_rate=0.05,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42
        ),
        'lr': LogisticRegression(
            max_iter=2000,
            C=0.1,
            random_state=42
        )
    }
    
    for name, model in final_models.items():
        logger.info(f"Training {name.upper()}...")
        model.fit(X_scaled, y)
        train_acc = model.score(X_scaled, y)
        logger.info(f"  {name.upper()} training accuracy: {train_acc:.4f}")
    
    # Save models
    models_dir = Path("models/ensemble")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    joblib.dump(final_models, models_dir / "full_features_ensemble.pkl")
    joblib.dump(scaler, models_dir / "full_features_scaler.pkl")
    
    # Save feature names
    import json
    with open(models_dir / "feature_names.json", "w") as f:
        json.dump(feature_cols, f, indent=2)
    
    logger.info(f"💾 Models saved to {models_dir}/")
    
    return final_models, scaler

def analyze_feature_importance(models, feature_cols):
    """Analyze and display feature importance"""
    logger.info(f"\n{'='*80}")
    logger.info("🔍 FEATURE IMPORTANCE ANALYSIS")
    logger.info(f"{'='*80}")
    
    # Random Forest feature importance
    rf_importance = models['rf'].feature_importances_
    rf_features = sorted(zip(feature_cols, rf_importance), key=lambda x: x[1], reverse=True)
    
    logger.info("\nTop 10 Most Important Features (Random Forest):")
    for i, (feat, imp) in enumerate(rf_features[:10], 1):
        logger.info(f"  {i:2d}. {feat:30s} {imp:.4f}")
    
    # Gradient Boosting feature importance
    gb_importance = models['gb'].feature_importances_
    gb_features = sorted(zip(feature_cols, gb_importance), key=lambda x: x[1], reverse=True)
    
    logger.info("\nTop 10 Most Important Features (Gradient Boosting):")
    for i, (feat, imp) in enumerate(gb_features[:10], 1):
        logger.info(f"  {i:2d}. {feat:30s} {imp:.4f}")

def main():
    print("=" * 80)
    print("🏀 TRAINING MODELS WITH FULL FEATURES ON 200+ GAMES")
    print("=" * 80)
    
    # Load data
    df = load_processed_data()
    if df is None:
        return
    
    # Prepare features
    X, y, feature_cols = prepare_features(df)
    
    # Cross-validation
    models, cv_results = train_with_cv(X, y, n_splits=5)
    
    # Train final models
    final_models, scaler = train_final_models(X, y, feature_cols)
    
    # Feature importance
    analyze_feature_importance(final_models, feature_cols)
    
    # Print final summary
    print("\n" + "=" * 80)
    print("✅ TRAINING COMPLETE!")
    print("=" * 80)
    print(f"📊 Dataset: {len(df)} games")
    print(f"🎯 Features: {len(feature_cols)}")
    print(f"💾 Models saved: models/ensemble/full_features_ensemble.pkl")
    print("=" * 80)
    
    # Show best model
    best_model = None
    best_score = 0
    for name, results in cv_results.items():
        val_mean = np.mean(results['val_scores'])
        if val_mean > best_score:
            best_score = val_mean
            best_model = name
    
    print(f"🏆 Best Model: {best_model} ({best_score:.2%} validation accuracy)")
    print("=" * 80)

if __name__ == "__main__":
    main()
