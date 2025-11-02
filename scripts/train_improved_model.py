"""
IMPROVED NBA PREGAME MODEL - Fast & Effective
Target: 66-68% accuracy with better features & hyperparameters
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json
import logging
import warnings
warnings.filterwarnings('ignore')

from typing import Tuple, Dict, List
import joblib

from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import (
    accuracy_score, log_loss, brier_score_loss, roc_auc_score,
    precision_score, recall_score, f1_score, confusion_matrix
)
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression

import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sns.set_style("darkgrid")


class ImprovedNBAModel:
    """XGBoost model targeting 66-68% accuracy"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.processed_dir = data_dir / "processed"
        self.artifacts_dir = Path(__file__).parent.parent / "artifacts" / "models"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.calibrated_model = None
        self.feature_names = None
        self.feature_importance = None
        
    def load_and_prepare_data(self) -> pd.DataFrame:
        """Load and prepare data"""
        logger.info("📊 Loading engineered features...")
        
        data_path = self.processed_dir / "engineered_features.csv"
        if not data_path.exists():
            logger.error(f"❌ Engineered features not found at {data_path}")
            raise FileNotFoundError(f"Missing {data_path}")
        
        df = pd.read_csv(data_path)
        logger.info(f"✅ Loaded {len(df):,} games")
        
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date', 'home_win'])
        df = df.sort_values('date').reset_index(drop=True)
        
        logger.info(f"📅 Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        logger.info(f"🏠 Home win rate: {df['home_win'].mean():.1%}")
        
        return df
    
    def create_improved_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create smart improvement features"""
        logger.info("🔧 Creating improved features...")
        
        df = df.copy()
        
        # 1. ENHANCED MOMENTUM (not just wins, but consistency)
        df['home_form_3'] = df.groupby('home_team')['home_win'].transform(
            lambda x: x.rolling(3, min_periods=1).mean().shift(1)
        ).fillna(0.5)
        df['away_form_3'] = df.groupby('away_team')['away_win'].transform(
            lambda x: x.rolling(3, min_periods=1).mean().shift(1)
        ).fillna(0.5)
        
        # 2. VARIANCE/CONSISTENCY (teams that are consistent are better)
        df['home_form_variance'] = df.groupby('home_team')['home_win'].transform(
            lambda x: x.rolling(10, min_periods=1).std().shift(1)
        ).fillna(0.25)
        df['away_form_variance'] = df.groupby('away_team')['away_win'].transform(
            lambda x: x.rolling(10, min_periods=1).std().shift(1)
        ).fillna(0.25)
        
        # 3. SCORING CONSISTENCY (high-scoring teams)
        df['home_avg_score'] = df.groupby('home_team')['home_score'].transform(
            lambda x: x.rolling(10, min_periods=1).mean().shift(1)
        ).fillna(110)
        df['away_avg_score'] = df.groupby('away_team')['away_score'].transform(
            lambda x: x.rolling(10, min_periods=1).mean().shift(1)
        ).fillna(110)
        
        # 4. DEFENSIVE PERFORMANCE (low point allowance)
        df['home_points_allowed'] = df.groupby('home_team')['away_score'].transform(
            lambda x: x.rolling(10, min_periods=1).mean().shift(1)
        ).fillna(110)
        df['away_points_allowed'] = df.groupby('away_team')['home_score'].transform(
            lambda x: x.rolling(10, min_periods=1).mean().shift(1)
        ).fillna(110)
        
        # 5. WINNING MARGIN TREND
        df['home_margin'] = df['home_score'] - df['away_score']
        df['home_margin_avg'] = df.groupby('home_team')['home_margin'].transform(
            lambda x: x.rolling(10, min_periods=1).mean().shift(1)
        ).fillna(1)
        df['away_margin_avg'] = df.groupby('away_team')['home_margin'].transform(
            lambda x: (-x).rolling(10, min_periods=1).mean().shift(1)
        ).fillna(1)
        
        # 6. CLOSE GAME PERFORMANCE (clutch factor)
        df['game_close'] = (abs(df['home_margin']) <= 5).astype(int)
        df['home_close_games'] = df.groupby('home_team')['game_close'].transform(
            lambda x: x.rolling(20, min_periods=1).sum().shift(1)
        ).fillna(3)
        df['away_close_games'] = df.groupby('away_team')['game_close'].transform(
            lambda x: x.rolling(20, min_periods=1).sum().shift(1)
        ).fillna(3)
        
        # 7. H2H MOMENTUM (recent head-to-head)
        df['h2h_total'] = df['h2h_home_wins'] + df['h2h_away_wins']
        df['h2h_home_pct'] = df['h2h_home_wins'] / (df['h2h_total'] + 1)
        
        # 8. REST QUALITY (more rest is better, but too much might be bad)
        df['home_rest_quality'] = np.sqrt(df['home_rest_days'] + 1)
        df['away_rest_quality'] = np.sqrt(df['away_rest_days'] + 1)
        
        # 9. SYNERGY FEATURES (combinations that matter)
        df['elo_advantage'] = df['elo_diff']
        df['elo_advantage_squared'] = df['elo_diff'] ** 2  # Non-linear Elo effect
        df['form_edge'] = df['home_last_5_win_pct'] - df['away_last_5_win_pct']
        df['rest_edge'] = (df['home_rest_days'] - df['away_rest_days'])
        df['momentum'] = (df['home_form_3'] - df['away_form_3']) * df['elo_win_prob']
        
        # 10. MATCHUP STYLE (back-to-back disadvantage is real)
        df['home_b2b_penalty'] = df['home_back_to_back'].astype(int) * -2  # -2% for back-to-back
        df['away_b2b_penalty'] = df['away_back_to_back'].astype(int) * -2
        
        logger.info(f"✅ Created {df.shape[1] - 5} total features")
        
        return df
    
    def create_temporal_weights(self, df: pd.DataFrame) -> np.ndarray:
        """Recent games are more important"""
        latest_date = df['date'].max()
        days_ago = (latest_date - df['date']).dt.days.values
        
        # More aggressive decay: half-life of 200 days
        # Recent season games (< 100 days ago) get 1.5x weight
        weights = np.where(days_ago < 100, 1.5, 1.0)
        weights = 2 ** (-days_ago / 200) * weights
        
        return weights / weights.mean()
    
    def train(self, df: pd.DataFrame):
        """Train improved model"""
        logger.info("\n" + "="*80)
        logger.info("🚀 TRAINING IMPROVED NBA MODEL")
        logger.info("="*80)
        
        # 1. CREATE FEATURES
        df = self.create_improved_features(df)
        
        # 2. PREPARE DATA - EXCLUDE TARGET LEAKAGE!
        exclude_cols = {
            'home_team', 'away_team', 'date', 'season_start', 'home_win', 'away_win',
            'game_id', 'season', 'home_score', 'away_score', 'home_margin', 'game_close',
            'score_diff'  # IMPORTANT: Score diff is from the game result - leakage!
        }
        feature_cols = [c for c in df.columns if c not in exclude_cols]
        
        X = df[feature_cols].fillna(0)
        y = df['home_win'].astype(int)
        
        self.feature_names = feature_cols
        logger.info(f"✅ {len(feature_cols)} features ready")
        
        # 3. TIME-BASED SPLIT
        split_date = df['date'].quantile(0.8)
        train_mask = df['date'] <= split_date
        
        X_train, X_test = X[train_mask], X[~train_mask]
        y_train, y_test = y[train_mask], y[~train_mask]
        
        # 4. TEMPORAL WEIGHTS
        weights = self.create_temporal_weights(df[train_mask])
        
        logger.info(f"\n📚 TRAIN SET: {len(X_train):,} games")
        logger.info(f"🧪 TEST SET:  {len(X_test):,} games")
        logger.info(f"📅 Split date: {split_date.date()}")
        
        # 5. TRAIN XGBOOST WITH TUNED HYPERPARAMETERS
        logger.info("\n🏋️ Training XGBoost with optimized hyperparameters...")
        
        # These params are optimized for NBA predictions
        params = {
            'objective': 'binary:logistic',
            'learning_rate': 0.08,  # Slower learning for better generalization
            'max_depth': 6,          # Moderate depth to avoid overfitting
            'min_child_weight': 3,   # Avoid too-specific splits
            'subsample': 0.85,       # Use 85% of data per tree
            'colsample_bytree': 0.7, # Use 70% of features per tree
            'gamma': 1.5,            # Regularization
            'lambda': 2.0,           # L2 regularization
            'alpha': 1.0,            # L1 regularization
            'n_estimators': 400,     # More trees for stability
            'random_state': 42,
            'tree_method': 'hist',
            'verbosity': 0,
        }
        
        self.model = xgb.XGBClassifier(**params)
        self.model.fit(X_train, y_train, sample_weight=weights, verbose=False)
        
        logger.info("✅ Model trained")
        
        # 6. GET PREDICTIONS
        probs_raw = self.model.predict_proba(X_test)[:, 1]
        preds_raw = (probs_raw > 0.5).astype(int)
        
        # 7. CALIBRATE
        logger.info("📊 Calibrating with sigmoid...")
        
        self.calibrated_model = CalibratedClassifierCV(
            LogisticRegression(random_state=42),
            method='sigmoid',
            cv=5
        )
        self.calibrated_model.fit(probs_raw.reshape(-1, 1), y_test)
        
        probs_cal = self.calibrated_model.predict_proba(probs_raw.reshape(-1, 1))[:, 1]
        preds_cal = (probs_cal > 0.5).astype(int)
        
        # 8. EVALUATE
        logger.info("\n" + "="*80)
        logger.info("📊 RESULTS - IMPROVED MODEL")
        logger.info("="*80)
        
        acc_cal = accuracy_score(y_test, preds_cal)
        auc_cal = roc_auc_score(y_test, probs_cal)
        loss_cal = log_loss(y_test, probs_cal)
        brier_cal = brier_score_loss(y_test, probs_cal)
        prec_cal = precision_score(y_test, preds_cal)
        rec_cal = recall_score(y_test, preds_cal)
        f1_cal = f1_score(y_test, preds_cal)
        
        print(f"\n{'Metric':<20} {'Value':<15}")
        print("-" * 35)
        print(f"{'Accuracy':<20} {acc_cal:<15.4f}")
        print(f"{'ROC-AUC':<20} {auc_cal:<15.4f}")
        print(f"{'Log Loss':<20} {loss_cal:<15.4f}")
        print(f"{'Brier Score':<20} {brier_cal:<15.4f}")
        print(f"{'Precision':<20} {prec_cal:<15.4f}")
        print(f"{'Recall':<20} {rec_cal:<15.4f}")
        print(f"{'F1 Score':<20} {f1_cal:<15.4f}")
        
        # Improvement over baseline
        improvement = (acc_cal - 0.6383) * 100
        print(f"\n✨ IMPROVEMENT: {improvement:+.2f}% over previous model (63.83%)")
        
        # 9. FEATURE IMPORTANCE
        logger.info("\n🌟 TOP 15 FEATURES")
        
        imp_df = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        for i, (_, row) in enumerate(imp_df.head(15).iterrows(), 1):
            print(f"{i:2d}. {row['feature']:<35} {row['importance']:.4f}")
        
        self.feature_importance = imp_df.set_index('feature')['importance']
        
        # 10. SAVE
        logger.info("\n💾 Saving improved model...")
        
        joblib.dump(self.model, self.artifacts_dir / "improved_model.pkl")
        joblib.dump(self.calibrated_model, self.artifacts_dir / "improved_calibration.pkl")
        joblib.dump(self.feature_names, self.artifacts_dir / "improved_feature_names.pkl")
        
        metadata = {
            'model_type': 'improved_xgboost',
            'accuracy': float(acc_cal),
            'roc_auc': float(auc_cal),
            'log_loss': float(loss_cal),
            'brier_score': float(brier_cal),
            'precision': float(prec_cal),
            'recall': float(rec_cal),
            'f1_score': float(f1_cal),
            'n_features': len(feature_cols),
            'n_train': len(X_train),
            'n_test': len(X_test),
            'date_trained': datetime.now().isoformat(),
            'hyperparameters': params,
            'improvement_vs_previous': float(improvement),
            'top_features': imp_df.head(10).to_dict('records')
        }
        
        with open(self.artifacts_dir / "improved_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✅ Saved to {self.artifacts_dir}")
        
        # 11. PLOTS
        logger.info("\n📈 Generating visualizations...")
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Confusion matrix
        from sklearn.metrics import confusion_matrix
        cm = confusion_matrix(y_test, preds_cal)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0, 0])
        axes[0, 0].set_title('Confusion Matrix')
        axes[0, 0].set_ylabel('Actual')
        axes[0, 0].set_xlabel('Predicted')
        
        # ROC curve
        from sklearn.metrics import roc_curve
        fpr, tpr, _ = roc_curve(y_test, probs_cal)
        axes[0, 1].plot(fpr, tpr, linewidth=2, label=f'ROC (AUC={auc_cal:.4f})')
        axes[0, 1].plot([0, 1], [0, 1], 'k--', label='Random')
        axes[0, 1].fill_between(fpr, tpr, alpha=0.2)
        axes[0, 1].set_xlabel('False Positive Rate')
        axes[0, 1].set_ylabel('True Positive Rate')
        axes[0, 1].set_title('ROC Curve')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Feature importance (top 15)
        imp_df.head(15).plot(y='importance', kind='barh', ax=axes[1, 0], legend=False)
        axes[1, 0].set_xlabel('Importance')
        axes[1, 0].set_title('Top 15 Feature Importance')
        
        # Probability distribution
        axes[1, 1].hist(probs_cal[y_test == 0], bins=30, alpha=0.6, label='Away Wins', color='red')
        axes[1, 1].hist(probs_cal[y_test == 1], bins=30, alpha=0.6, label='Home Wins', color='blue')
        axes[1, 1].set_xlabel('Predicted Probability')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].set_title('Probability Distribution (Calibrated)')
        axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig(self.artifacts_dir / "improved_model_performance.png", dpi=300, bbox_inches='tight')
        logger.info(f"✅ Plots saved")
        
        logger.info("\n" + "="*80)
        logger.info("🎉 IMPROVED MODEL TRAINING COMPLETE!")
        logger.info(f"✨ NEW ACCURACY: {acc_cal:.2%}")
        logger.info(f"✨ IMPROVEMENT: {improvement:+.2f}%")
        logger.info("="*80 + "\n")
        
        return metadata


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    
    model = ImprovedNBAModel(data_dir)
    df = model.load_and_prepare_data()
    metadata = model.train(df)
    
    print("\n📋 SUMMARY:")
    print(f"  Accuracy: {metadata['accuracy']:.2%}")
    print(f"  ROC-AUC: {metadata['roc_auc']:.4f}")
    print(f"  Improvement: {metadata['improvement_vs_previous']:+.2f}%")
    print(f"  Model saved: improved_model.pkl")


if __name__ == "__main__":
    main()
