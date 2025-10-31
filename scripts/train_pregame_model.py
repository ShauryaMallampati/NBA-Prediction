#!/usr/bin/env python3
"""
XGBoost Pre-Game Prediction Model Training

Trains a gradient boosting model to predict NBA game outcomes
using engineered features (Elo, recent form, H2H, rest days, etc.)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from typing import Tuple, Dict

# ML libraries
import xgboost as xgb
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, log_loss, roc_auc_score, 
    confusion_matrix, classification_report, brier_score_loss
)
from sklearn.calibration import CalibratedClassifierCV
import matplotlib.pyplot as plt
import seaborn as sns

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


class PregameModelTrainer:
    """Train XGBoost model for pre-game predictions"""
    
    def __init__(self, artifacts_dir: str = "artifacts/models"):
        """
        Initialize trainer
        
        Args:
            artifacts_dir: Directory to save trained models
        """
        self.artifacts_dir = Path(artifacts_dir)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        # Feature columns to use
        self.feature_columns = [
            # Elo ratings
            'home_elo', 'away_elo', 'elo_diff', 'elo_win_prob',
            
            # Recent form
            'home_last_5_win_pct', 'away_last_5_win_pct',
            'home_last_10_win_pct', 'away_last_10_win_pct',
            
            # Head-to-head
            'h2h_home_wins', 'h2h_away_wins',
            
            # Rest and fatigue
            'home_rest_days', 'away_rest_days',
            'home_back_to_back', 'away_back_to_back',
            
            # Home/away splits
            'home_home_win_pct', 'away_away_win_pct',
        ]
        
        self.target_column = 'home_win'
        self.model = None
        self.calibrated_model = None
    
    def load_data(self, features_file: Path) -> pd.DataFrame:
        """
        Load engineered features from CSV
        
        Args:
            features_file: Path to features CSV
        
        Returns:
            DataFrame with features
        """
        print(f"\n📂 Loading features from {features_file}...")
        df = pd.read_csv(features_file)
        print(f"  ✅ Loaded {len(df)} games")
        
        return df
    
    def prepare_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Prepare train/test split
        
        Args:
            df: DataFrame with features and target
        
        Returns:
            X_train, X_test, y_train, y_test
        """
        print(f"\n⚙️  Preparing data...")
        
        # Filter to only completed games (with results)
        df_complete = df[df[self.target_column].notna()].copy()
        print(f"  Games with results: {len(df_complete)}")
        
        # Handle missing features (fill with median)
        for col in self.feature_columns:
            if col in df_complete.columns:
                df_complete[col] = df_complete[col].fillna(df_complete[col].median())
        
        # Split features and target
        X = df_complete[self.feature_columns]
        y = df_complete[self.target_column]
        
        # Train/test split (80/20)
        # Use chronological split for time series data
        split_idx = int(len(df_complete) * 0.8)
        X_train = X.iloc[:split_idx]
        X_test = X.iloc[split_idx:]
        y_train = y.iloc[:split_idx]
        y_test = y.iloc[split_idx:]
        
        print(f"  Training set: {len(X_train)} games")
        print(f"  Test set: {len(X_test)} games")
        print(f"  Features: {len(self.feature_columns)}")
        
        return X_train, X_test, y_train, y_test
    
    def train_model(self, X_train: pd.DataFrame, y_train: pd.Series) -> xgb.XGBClassifier:
        """
        Train XGBoost model
        
        Args:
            X_train: Training features
            y_train: Training labels
        
        Returns:
            Trained XGBoost model
        """
        print(f"\n🤖 Training XGBoost model...")
        
        # XGBoost parameters
        params = {
            'n_estimators': 500,          # Number of boosting rounds
            'max_depth': 6,               # Maximum tree depth
            'learning_rate': 0.05,        # Step size shrinkage
            'subsample': 0.8,             # Fraction of samples per tree
            'colsample_bytree': 0.8,      # Fraction of features per tree
            'min_child_weight': 3,        # Minimum sum of weights in a child
            'gamma': 0.1,                 # Minimum loss reduction
            'reg_alpha': 0.1,             # L1 regularization
            'reg_lambda': 1.0,            # L2 regularization
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'random_state': 42,
            'n_jobs': -1                  # Use all CPU cores
        }
        
        # Create model
        model = xgb.XGBClassifier(**params)
        
        # Train with early stopping
        eval_set = [(X_train, y_train)]
        
        model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=False
        )
        
        print(f"  ✅ Model trained!")
        print(f"  Best iteration: {model.best_iteration}")
        print(f"  Training log loss: {model.best_score:.4f}")
        
        self.model = model
        return model
    
    def calibrate_model(self, X_train: pd.DataFrame, y_train: pd.Series):
        """
        Calibrate model probabilities
        
        Ensures that when model predicts 70%, those predictions actually win 70% of the time
        
        Args:
            X_train: Training features
            y_train: Training labels
        """
        print(f"\n📊 Calibrating model probabilities...")
        
        self.calibrated_model = CalibratedClassifierCV(
            self.model,
            method='sigmoid',  # Platt scaling
            cv=5
        )
        
        self.calibrated_model.fit(X_train, y_train)
        print(f"  ✅ Model calibrated!")
    
    def evaluate_model(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """
        Evaluate model performance
        
        Args:
            X_test: Test features
            y_test: Test labels
        
        Returns:
            Dictionary of metrics
        """
        print(f"\n📈 Evaluating model...")
        
        # Predictions
        y_pred_proba = self.calibrated_model.predict_proba(X_test)[:, 1]
        y_pred = (y_pred_proba >= 0.5).astype(int)
        
        # Calculate metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'log_loss': log_loss(y_test, y_pred_proba),
            'brier_score': brier_score_loss(y_test, y_pred_proba),
            'roc_auc': roc_auc_score(y_test, y_pred_proba)
        }
        
        print(f"\n  ✅ Test Set Results:")
        print(f"     Accuracy:     {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
        print(f"     Log Loss:     {metrics['log_loss']:.4f}")
        print(f"     Brier Score:  {metrics['brier_score']:.4f}")
        print(f"     ROC-AUC:      {metrics['roc_auc']:.4f}")
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        print(f"\n  Confusion Matrix:")
        print(f"                 Predicted")
        print(f"                Away   Home")
        print(f"  Actual Away  {cm[0,0]:5d}  {cm[0,1]:5d}")
        print(f"         Home  {cm[1,0]:5d}  {cm[1,1]:5d}")
        
        # Classification report
        print(f"\n  Classification Report:")
        print(classification_report(y_test, y_pred, target_names=['Away Win', 'Home Win']))
        
        return metrics
    
    def feature_importance(self):
        """Display feature importance"""
        print(f"\n🎯 Feature Importance:")
        
        # Get importance scores
        importance = self.model.feature_importances_
        features_df = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        print(features_df.to_string(index=False))
        
        # Plot
        plt.figure(figsize=(10, 8))
        plt.barh(features_df['feature'][:15], features_df['importance'][:15])
        plt.xlabel('Importance')
        plt.title('Top 15 Most Important Features')
        plt.tight_layout()
        
        importance_plot = self.artifacts_dir / 'feature_importance.png'
        plt.savefig(importance_plot)
        print(f"\n  💾 Saved plot to {importance_plot}")
    
    def save_model(self, name: str = "pregame_xgboost"):
        """
        Save trained model
        
        Args:
            name: Model name
        """
        print(f"\n💾 Saving model...")
        
        # Save calibrated model (this is what we'll use in production)
        model_path = self.artifacts_dir / f"{name}.pkl"
        joblib.dump(self.calibrated_model, model_path)
        print(f"  ✅ Saved calibrated model to {model_path}")
        
        # Save base model (for feature importance analysis)
        base_model_path = self.artifacts_dir / f"{name}_base.pkl"
        joblib.dump(self.model, base_model_path)
        print(f"  ✅ Saved base model to {base_model_path}")
        
        # Save feature columns
        features_path = self.artifacts_dir / f"{name}_features.txt"
        with open(features_path, 'w') as f:
            f.write('\n'.join(self.feature_columns))
        print(f"  ✅ Saved feature list to {features_path}")
    
    def cross_validate(self, X: pd.DataFrame, y: pd.Series, cv: int = 5):
        """
        Perform cross-validation
        
        Args:
            X: Features
            y: Labels
            cv: Number of folds
        """
        print(f"\n🔄 Performing {cv}-fold cross-validation...")
        
        scores = cross_val_score(
            self.model, X, y,
            cv=cv,
            scoring='accuracy',
            n_jobs=-1
        )
        
        print(f"  Cross-validation scores: {scores}")
        print(f"  Mean accuracy: {scores.mean():.4f} (+/- {scores.std() * 2:.4f})")


def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train XGBoost pre-game prediction model')
    parser.add_argument('--features', type=str, required=True,
                       help='Path to engineered features CSV')
    parser.add_argument('--output-dir', type=str, default='artifacts/models',
                       help='Directory to save trained model')
    parser.add_argument('--model-name', type=str, default='pregame_xgboost',
                       help='Name for saved model')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🏀 NBA PRE-GAME PREDICTION MODEL TRAINING (XGBoost)")
    print("=" * 80)
    
    # Initialize trainer
    trainer = PregameModelTrainer(artifacts_dir=args.output_dir)
    
    # Load data
    df = trainer.load_data(Path(args.features))
    
    # Prepare train/test split
    X_train, X_test, y_train, y_test = trainer.prepare_data(df)
    
    # Train model
    model = trainer.train_model(X_train, y_train)
    
    # Calibrate probabilities
    trainer.calibrate_model(X_train, y_train)
    
    # Evaluate
    metrics = trainer.evaluate_model(X_test, y_test)
    
    # Feature importance
    trainer.feature_importance()
    
    # Cross-validation
    X_full = df[trainer.feature_columns].fillna(df[trainer.feature_columns].median())
    y_full = df[trainer.target_column].dropna()
    X_full = X_full.loc[y_full.index]
    trainer.cross_validate(X_full, y_full, cv=5)
    
    # Save model
    trainer.save_model(name=args.model_name)
    
    print("\n" + "=" * 80)
    print("✅ TRAINING COMPLETE!")
    print(f"   Model saved to: {trainer.artifacts_dir}")
    print(f"   Test Accuracy: {metrics['accuracy']*100:.2f}%")
    print(f"   ROC-AUC: {metrics['roc_auc']:.4f}")
    print("=" * 80)


if __name__ == "__main__":
    main()
