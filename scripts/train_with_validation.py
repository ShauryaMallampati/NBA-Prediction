"""
Master Training Pipeline with Cross-Validation
Trains all models with proper validation to prevent overfitting
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import logging
from sklearn.model_selection import TimeSeriesSplit, cross_validate
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score
from src.models.ensemble_model import NBAEnsembleModel
from src.pipeline.feature_engineering import feature_engineer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainingPipeline:
    """Train models with proper validation"""
    
    def __init__(self):
        self.results_dir = Path("artifacts/training_results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def train_with_cv(self, X: pd.DataFrame, y: pd.Series, n_splits: int = 5):
        """
        Train with Time Series Cross-Validation to prevent overfitting
        """
        logger.info(f"\n{'='*80}")
        logger.info("🎯 TRAINING WITH CROSS-VALIDATION (PREVENTS OVERFITTING)")
        logger.info(f"{'='*80}\n")
        
        # Time Series Split (respects temporal order)
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        ensemble = NBAEnsembleModel()
        
        cv_scores = []
        fold_results = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
            logger.info(f"\n📊 Fold {fold}/{n_splits}")
            logger.info(f"   Train size: {len(train_idx)}, Val size: {len(val_idx)}")
            
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Train
            ensemble.train(X_train, y_train, use_stacking=True)
            
            # Validate
            predictions, details = ensemble.predict(X_val)
            val_acc = accuracy_score(y_val, predictions)
            
            # Get probabilities for log loss
            proba = details['stacking_ensemble_probability']
            val_logloss = log_loss(y_val, proba)
            
            cv_scores.append(val_acc)
            fold_results.append({
                'fold': fold,
                'train_size': len(train_idx),
                'val_size': len(val_idx),
                'val_accuracy': val_acc,
                'val_logloss': val_logloss
            })
            
            logger.info(f"   ✅ Val Accuracy: {val_acc:.4f}")
            logger.info(f"   📉 Val Log Loss: {val_logloss:.4f}")
        
        # Summary
        logger.info(f"\n{'='*80}")
        logger.info("📈 CROSS-VALIDATION RESULTS")
        logger.info(f"{'='*80}")
        logger.info(f"   Mean CV Accuracy: {np.mean(cv_scores):.4f} (+/- {np.std(cv_scores)*2:.4f})")
        logger.info(f"   Min CV Accuracy: {np.min(cv_scores):.4f}")
        logger.info(f"   Max CV Accuracy: {np.max(cv_scores):.4f}")
        
        # Check for overfitting
        score_variance = np.std(cv_scores)
        if score_variance > 0.05:
            logger.warning(f"⚠️  High variance detected ({score_variance:.4f}) - possible overfitting!")
        else:
            logger.info(f"✅ Low variance ({score_variance:.4f}) - model is stable!")
        
        # Train final model on all data
        logger.info("\n🏁 Training final model on full dataset...")
        ensemble.train(X, y, use_stacking=True)
        
        # Save results
        results_df = pd.DataFrame(fold_results)
        results_df.to_csv(self.results_dir / "cv_results.csv", index=False)
        
        return ensemble, results_df

def main():
    print("\n" + "="*80)
    print("🚀 MASTER TRAINING PIPELINE")
    print("="*80)
    
    pipeline = TrainingPipeline()
    
    # 1. Build features
    print("\n1️⃣  Building feature dataset...")
    features_df = feature_engineer.build_training_dataset(max_games=50)
    
    if len(features_df) < 20:
        print("⚠️  Not enough data. Using demo data...")
        # Create demo data
        from scripts.train_ensemble_model import load_betting_data, create_features_from_odds
        odds_data = load_betting_data()
        features_df = create_features_from_odds(odds_data)
        
        # Simulate outcomes
        features_df['winner'] = np.where(
            features_df['home_implied_prob'] > features_df['away_implied_prob'],
            np.random.choice([1, 0], size=len(features_df), p=[0.7, 0.3]),
            np.random.choice([1, 0], size=len(features_df), p=[0.3, 0.7])
        )
    
    # 2. Prepare features
    print(f"\n2️⃣  Preparing features ({len(features_df)} games)...")
    
    feature_cols = [col for col in features_df.columns 
                   if col not in ['game_id', 'winner', 'home_team', 'away_team', 'commence_time']]
    
    # Fill missing values
    for col in feature_cols:
        if features_df[col].dtype in [np.float64, np.int64]:
            features_df[col] = features_df[col].fillna(features_df[col].median())
    
    X = features_df[feature_cols]
    y = features_df['winner'] if 'winner' in features_df.columns else features_df.iloc[:, -1]
    
    print(f"   Features: {len(feature_cols)}")
    print(f"   Samples: {len(X)}")
    
    # 3. Train with cross-validation
    print("\n3️⃣  Training with cross-validation...")
    model, cv_results = pipeline.train_with_cv(X, y, n_splits=5)
    
    print("\n" + "="*80)
    print("✅ TRAINING COMPLETE!")
    print("="*80)
    print(f"\nCV Results saved to: {pipeline.results_dir / 'cv_results.csv'}")
    print("\n💡 Model is ready for predictions!")

if __name__ == "__main__":
    main()
