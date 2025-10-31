"""
Train XGBoost model on 73 YEARS of NBA data (1953-2026)
Enhanced with better features and ensemble techniques
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import logging
from typing import Tuple, Dict
import joblib

from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.metrics import (
    accuracy_score, log_loss, brier_score_loss, roc_auc_score,
    confusion_matrix, classification_report
)
from sklearn.calibration import CalibratedClassifierCV
import xgboost as xgb
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedNBAPregameModel:
    """Enhanced XGBoost model with 73 years of data"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.processed_dir = data_dir / "processed"
        self.artifacts_dir = Path(__file__).parent.parent / "artifacts" / "models"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.calibrated_model = None
        self.feature_names = None
        self.feature_importance = None
        
    def load_data(self) -> pd.DataFrame:
        """Load processed historical data"""
        logger.info("Loading processed data...")
        
        data_path = self.processed_dir / "engineered_features.csv"
        
        if not data_path.exists():
            logger.error(f"Engineered features not found at {data_path}")
            logger.info("Please run: poetry run python scripts/engineer_features.py")
            raise FileNotFoundError(f"Missing {data_path}")
        
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} games with engineered features")
        
        return df
    
    def create_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add advanced features for better accuracy"""
        logger.info("Creating advanced features...")
        
        # 1. Momentum features (last 3, 5, 10 games)
        for n in [3, 5, 10]:
            df[f'home_last_{n}_win_pct'] = df.groupby('home_team')['home_win'].transform(
                lambda x: x.rolling(n, min_periods=1).mean().shift(1)
            )
            df[f'away_last_{n}_win_pct'] = df.groupby('away_team')['away_win'].transform(
                lambda x: (1 - x).rolling(n, min_periods=1).mean().shift(1)
            )
        
        # 2. Strength of schedule (opponent quality)
        df['home_opp_elo_avg'] = df.groupby('home_team')['away_elo'].transform(
            lambda x: x.rolling(10, min_periods=1).mean().shift(1)
        )
        df['away_opp_elo_avg'] = df.groupby('away_team')['home_elo'].transform(
            lambda x: x.rolling(10, min_periods=1).mean().shift(1)
        )
        
        # 3. Home court advantage (team-specific)
        home_advantage = df.groupby('home_team').apply(
            lambda x: (x['home_win'].mean() - 0.5) * 100  # Deviation from 50%
        ).to_dict()
        df['home_court_advantage'] = df['home_team'].map(home_advantage)
        
        # 4. Clutch performance (close games)
        df['home_clutch_record'] = df.groupby('home_team').apply(
            lambda x: x[abs(x['point_diff']) <= 5]['home_win'].mean()
        ).to_dict()
        df['home_clutch_record'] = df['home_team'].map(df['home_clutch_record'])
        
        # 5. Fatigue factor (games in last 7 days)
        df['date'] = pd.to_datetime(df['date'])
        df['home_games_last_7d'] = df.groupby('home_team')['date'].transform(
            lambda x: x.rolling('7D').count() - 1
        )
        df['away_games_last_7d'] = df.groupby('away_team')['date'].transform(
            lambda x: x.rolling('7D').count() - 1
        )
        
        # 6. Playoff experience (if available)
        df['home_playoff_exp'] = df.groupby('home_team')['season'].transform(
            lambda x: x.value_counts().max() if len(x) > 0 else 0
        )
        df['away_playoff_exp'] = df.groupby('away_team')['season'].transform(
            lambda x: x.value_counts().max() if len(x) > 0 else 0
        )
        
        # 7. Recent point differential trend
        df['home_recent_pt_diff'] = df.groupby('home_team')['point_diff'].transform(
            lambda x: x.rolling(5, min_periods=1).mean().shift(1)
        )
        df['away_recent_pt_diff'] = df.groupby('away_team')['point_diff'].transform(
            lambda x: -x.rolling(5, min_periods=1).mean().shift(1)
        )
        
        logger.info(f"Created advanced features. Total columns: {len(df.columns)}")
        return df
    
    def prepare_data(self, df: pd.DataFrame, test_size: float = 0.2) -> Tuple:
        """Prepare training and test sets with time-based split"""
        logger.info("Preparing data for training...")
        
        # Add advanced features
        df = self.create_advanced_features(df)
        
        # Remove rows with missing values
        df = df.dropna()
        logger.info(f"Data shape after dropna: {df.shape}")
        
        # Define features (exclude target and metadata)
        exclude_cols = [
            'game_id', 'date', 'home_team', 'away_team', 'home_win',
            'home_pts', 'away_pts', 'point_diff', 'season'
        ]
        
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        X = df[feature_cols]
        y = df['home_win']
        
        self.feature_names = feature_cols
        logger.info(f"Features: {len(feature_cols)}")
        logger.info(f"Samples: {len(X)}")
        
        # Time-based split (last 20% for testing)
        split_idx = int(len(X) * (1 - test_size))
        
        X_train = X[:split_idx]
        X_test = X[split_idx:]
        y_train = y[:split_idx]
        y_test = y[split_idx:]
        
        logger.info(f"Train set: {len(X_train)} games")
        logger.info(f"Test set: {len(X_test)} games")
        logger.info(f"Date split: {df.iloc[split_idx]['date']}")
        
        return X_train, X_test, y_train, y_test
    
    def train_model(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Train XGBoost model with optimal hyperparameters"""
        logger.info("Training XGBoost model...")
        
        # XGBoost parameters (tuned for 73 years of data)
        params = {
            'n_estimators': 500,      # More trees for complex patterns
            'max_depth': 6,            # Prevent overfitting
            'learning_rate': 0.05,     # Slower learning = better generalization
            'subsample': 0.8,          # Use 80% of data per tree
            'colsample_bytree': 0.8,   # Use 80% of features per tree
            'min_child_weight': 3,     # Minimum samples per leaf
            'gamma': 0.1,              # Minimum loss reduction
            'reg_alpha': 0.1,          # L1 regularization
            'reg_lambda': 1.0,         # L2 regularization
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'random_state': 42,
            'n_jobs': -1
        }
        
        self.model = xgb.XGBClassifier(**params)
        
        # Train with early stopping
        eval_set = [(X_train, y_train)]
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            verbose=50
        )
        
        logger.info("Training complete!")
        
    def calibrate_model(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Calibrate model for accurate probability estimates"""
        logger.info("Calibrating model probabilities...")
        
        # Use isotonic regression (better than Platt scaling for large datasets)
        self.calibrated_model = CalibratedClassifierCV(
            self.model,
            method='isotonic',
            cv=5
        )
        
        self.calibrated_model.fit(X_train, y_train)
        logger.info("Calibration complete!")
    
    def evaluate_model(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict:
        """Comprehensive model evaluation"""
        logger.info("Evaluating model...")
        
        # Predictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        # Calibrated predictions
        y_pred_cal = self.calibrated_model.predict(X_test)
        y_pred_proba_cal = self.calibrated_model.predict_proba(X_test)[:, 1]
        
        # Metrics
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'accuracy_calibrated': accuracy_score(y_test, y_pred_cal),
            'log_loss': log_loss(y_test, y_pred_proba),
            'log_loss_calibrated': log_loss(y_test, y_pred_proba_cal),
            'brier_score': brier_score_loss(y_test, y_pred_proba),
            'brier_score_calibrated': brier_score_loss(y_test, y_pred_proba_cal),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'roc_auc_calibrated': roc_auc_score(y_test, y_pred_proba_cal)
        }
        
        logger.info("=" * 80)
        logger.info("MODEL EVALUATION RESULTS")
        logger.info("=" * 80)
        logger.info(f"Accuracy (Raw):        {metrics['accuracy']:.4f}")
        logger.info(f"Accuracy (Calibrated): {metrics['accuracy_calibrated']:.4f}")
        logger.info(f"Log Loss (Raw):        {metrics['log_loss']:.4f}")
        logger.info(f"Log Loss (Calibrated): {metrics['log_loss_calibrated']:.4f}")
        logger.info(f"Brier Score (Raw):     {metrics['brier_score']:.4f}")
        logger.info(f"Brier Score (Cal):     {metrics['brier_score_calibrated']:.4f}")
        logger.info(f"ROC-AUC (Raw):         {metrics['roc_auc']:.4f}")
        logger.info(f"ROC-AUC (Calibrated):  {metrics['roc_auc_calibrated']:.4f}")
        logger.info("=" * 80)
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred_cal)
        logger.info("\nConfusion Matrix:")
        logger.info(cm)
        
        # Classification report
        logger.info("\nClassification Report:")
        logger.info(classification_report(y_test, y_pred_cal))
        
        return metrics
    
    def feature_importance_analysis(self):
        """Analyze and plot feature importance"""
        logger.info("Analyzing feature importance...")
        
        importance = self.model.feature_importances_
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        self.feature_importance = feature_importance
        
        # Plot top 20 features
        plt.figure(figsize=(12, 8))
        top_features = feature_importance.head(20)
        plt.barh(top_features['feature'], top_features['importance'])
        plt.xlabel('Importance')
        plt.title('Top 20 Most Important Features')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        
        plot_path = self.artifacts_dir / 'feature_importance.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        logger.info(f"Feature importance plot saved to {plot_path}")
        
        # Log top features
        logger.info("\nTop 10 Most Important Features:")
        for idx, row in feature_importance.head(10).iterrows():
            logger.info(f"  {row['feature']:30s} {row['importance']:.4f}")
    
    def cross_validate(self, X: pd.DataFrame, y: pd.Series, cv: int = 5):
        """Perform time-series cross-validation"""
        logger.info(f"Performing {cv}-fold time-series cross-validation...")
        
        tscv = TimeSeriesSplit(n_splits=cv)
        
        scores = cross_val_score(
            self.model,
            X, y,
            cv=tscv,
            scoring='accuracy',
            n_jobs=-1
        )
        
        logger.info(f"CV Scores: {scores}")
        logger.info(f"Mean CV Accuracy: {scores.mean():.4f} (+/- {scores.std() * 2:.4f})")
    
    def save_model(self, metrics: Dict):
        """Save trained model and metadata"""
        logger.info("Saving model...")
        
        # Save models
        model_path = self.artifacts_dir / 'pregame_xgboost.pkl'
        calibrated_path = self.artifacts_dir / 'pregame_xgboost_calibrated.pkl'
        
        joblib.dump(self.model, model_path)
        joblib.dump(self.calibrated_model, calibrated_path)
        
        logger.info(f"Models saved to {self.artifacts_dir}")
        
        # Save metadata
        metadata = {
            'model_type': 'XGBoost',
            'training_date': datetime.now().isoformat(),
            'features': self.feature_names,
            'num_features': len(self.feature_names),
            'metrics': metrics,
            'feature_importance': self.feature_importance.to_dict('records')
        }
        
        metadata_path = self.artifacts_dir / 'pregame_model_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved to {metadata_path}")
    
    def run(self):
        """Main training pipeline"""
        logger.info("=" * 80)
        logger.info("NBA PREGAME MODEL TRAINING (73 YEARS OF DATA)")
        logger.info("=" * 80)
        
        # Load data
        df = self.load_data()
        
        # Prepare data
        X_train, X_test, y_train, y_test = self.prepare_data(df)
        
        # Train model
        self.train_model(X_train, y_train)
        
        # Calibrate model
        self.calibrate_model(X_train, y_train)
        
        # Evaluate model
        metrics = self.evaluate_model(X_test, y_test)
        
        # Feature importance
        self.feature_importance_analysis()
        
        # Cross-validate
        # self.cross_validate(X_train, y_train, cv=5)  # Uncomment if you want CV
        
        # Save model
        self.save_model(metrics)
        
        logger.info("=" * 80)
        logger.info("TRAINING COMPLETE!")
        logger.info(f"Final Accuracy: {metrics['accuracy_calibrated']:.2%}")
        logger.info(f"Model saved to: {self.artifacts_dir}")
        logger.info("=" * 80)


def main():
    """Main entry point"""
    data_dir = Path(__file__).parent.parent / "data"
    
    trainer = EnhancedNBAPregameModel(data_dir)
    trainer.run()


if __name__ == "__main__":
    main()
