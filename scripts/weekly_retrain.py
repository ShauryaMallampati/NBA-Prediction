#!/usr/bin/env python3
"""Weekly model retraining script for NBA Intelligence Platform."""

import logging
import pickle
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.calibration import reliability_diagram

from src.common.logger import setup_logger
from src.common.paths import Paths

logger = setup_logger(__name__)


class WeeklyModelRetrainer:
    """Retrain XGBoost model weekly with new data."""
    
    def __init__(self):
        """Initialize retrainer."""
        self.model_dir = Path(__file__).parent.parent / "artifacts" / "models"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = Path(__file__).parent.parent / "data" / "processed"
        self.model = None
        self.calibrated_model = None
        self.feature_names = None
    
    def load_features(self):
        """Load engineered features."""
        logger.info("Loading engineered features...")
        
        features_path = self.data_dir / "engineered_features.csv"
        if not features_path.exists():
            logger.error(f"Features file not found: {features_path}")
            raise FileNotFoundError(f"Missing {features_path}")
        
        df = pd.read_csv(features_path)
        logger.info(f"Loaded {len(df)} games with {len(df.columns)} features")
        
        return df
    
    def prepare_data(self, df, test_size=0.2):
        """Prepare training and test sets."""
        logger.info("Preparing data...")
        
        # Fill NaNs
        df = df.fillna(0)
        
        # Define features to exclude
        exclude_cols = [
            'game_id', 'date', 'home_team', 'away_team', 'home_win', 'away_win',
            'home_score', 'away_score', 'score_diff'
        ]
        
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        self.feature_names = feature_cols
        
        X = df[feature_cols]
        y = df['home_win']
        
        # Time-based split
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        logger.info(f"Train set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        logger.info(f"Features: {len(feature_cols)}")
        
        return X_train, X_test, y_train, y_test
    
    def train(self):
        """Train XGBoost model."""
        logger.info("=" * 80)
        logger.info("WEEKLY MODEL RETRAINING")
        logger.info("=" * 80)
        
        # Load and prepare data
        df = self.load_features()
        X_train, X_test, y_train, y_test = self.prepare_data(df)
        
        # Train XGBoost
        logger.info("Training XGBoost model...")
        self.model = xgb.XGBClassifier(
            n_estimators=500,
            learning_rate=0.05,
            max_depth=6,
            min_child_weight=1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
        )
        
        eval_set = [(X_test, y_test)]
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=50,
            early_stopping_rounds=50
        )
        
        # Calibrate probabilities
        logger.info("Calibrating model probabilities...")
        self.calibrated_model = CalibratedClassifierCV(
            self.model, method='sigmoid', cv='prefit'
        )
        self.calibrated_model.fit(X_test, y_test)
        
        # Evaluate
        logger.info("Evaluating model...")
        y_pred = self.calibrated_model.predict(X_test)
        y_pred_proba = self.calibrated_model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        loss = log_loss(y_test, y_pred_proba)
        
        logger.info("=" * 80)
        logger.info(f"Accuracy: {accuracy:.4f}")
        logger.info(f"ROC-AUC: {roc_auc:.4f}")
        logger.info(f"Log Loss: {loss:.4f}")
        logger.info("=" * 80)
        
        # Save model
        self.save_model(accuracy, roc_auc)
        
        return True
    
    def save_model(self, accuracy, roc_auc):
        """Save trained model and metadata."""
        logger.info("Saving model...")
        
        # Save base model
        model_file = self.model_dir / "pregame_model.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Saved model to {model_file}")
        
        # Save calibrated model
        calibrated_file = self.model_dir / "calibrated_model.pkl"
        with open(calibrated_file, 'wb') as f:
            pickle.dump(self.calibrated_model, f)
        logger.info(f"Saved calibrated model to {calibrated_file}")
        
        # Save metadata
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'model_type': 'XGBClassifier',
            'test_accuracy': float(accuracy),
            'test_roc_auc': float(roc_auc),
            'feature_names': self.feature_names,
            'feature_count': len(self.feature_names),
        }
        
        metadata_file = self.model_dir / "pregame_model_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Saved metadata to {metadata_file}")
    
    def generate_feature_importance(self):
        """Generate feature importance plot."""
        try:
            import matplotlib.pyplot as plt
            
            logger.info("Generating feature importance plot...")
            
            importances = self.model.feature_importances_
            indices = np.argsort(importances)[-20:]  # Top 20
            
            plt.figure(figsize=(10, 8))
            plt.title("Top 20 Feature Importances (XGBoost)")
            plt.barh(range(len(indices)), importances[indices])
            plt.yticks(range(len(indices)), [self.feature_names[i] for i in indices])
            plt.tight_layout()
            
            plot_file = self.model_dir / "feature_importance_weekly.png"
            plt.savefig(plot_file, dpi=100)
            logger.info(f"Saved feature importance plot to {plot_file}")
            plt.close()
        
        except Exception as e:
            logger.warning(f"Could not generate plot: {e}")


def main():
    """Run weekly retraining."""
    try:
        retrainer = WeeklyModelRetrainer()
        success = retrainer.train()
        
        if success:
            retrainer.generate_feature_importance()
            logger.info("Weekly retraining completed successfully!")
            return True
        else:
            logger.error("Training failed")
            return False
    
    except Exception as e:
        logger.error(f"Error during retraining: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
