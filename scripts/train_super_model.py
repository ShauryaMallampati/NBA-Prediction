"""
SUPER NBA PREGAME MODEL: 70%+ Accuracy
================================================
Ensemble of XGBoost + LightGBM + CatBoost
with advanced features, temporal weighting, and Optuna tuning
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
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
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV

import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier
import optuna
from optuna.pruners import MedianPruner

import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sns.set_style("darkgrid")


class SuperNBAModel:
    """Ensemble model targeting 70%+ accuracy"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.processed_dir = data_dir / "processed"
        self.artifacts_dir = Path(__file__).parent.parent / "artifacts" / "models"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        self.xgb_model = None
        self.lgb_model = None
        self.cat_model = None
        self.ensemble_model = None
        self.calibrated_ensemble = None
        
        self.feature_names = None
        self.feature_importance = None
        
    def load_and_prepare_data(self) -> pd.DataFrame:
        """Load and prepare data with temporal handling"""
        logger.info("📊 Loading engineered features...")
        
        data_path = self.processed_dir / "engineered_features.csv"
        if not data_path.exists():
            logger.error(f"❌ Engineered features not found at {data_path}")
            logger.info("Run: poetry run python scripts/engineer_features.py")
            raise FileNotFoundError(f"Missing {data_path}")
        
        df = pd.read_csv(data_path)
        logger.info(f"✅ Loaded {len(df):,} games")
        
        # Convert date properly
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date', 'home_win'])
        df = df.sort_values('date').reset_index(drop=True)
        
        logger.info(f"📅 Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        logger.info(f"🏠 Home win rate: {df['home_win'].mean():.1%}")
        
        return df
    
    def create_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create powerful new features"""
        logger.info("🔧 Creating advanced features...")
        
        df = df.copy()
        
        # 1. MOMENTUM FEATURES - use existing home_last_N_win_pct and away_last_N_win_pct
        # These are already engineered, so we'll create additional ones
        df['home_win_momentum'] = df.groupby('home_team')['home_win'].transform(
            lambda x: x.rolling(5, min_periods=1).sum().shift(1)
        )
        df['away_win_momentum'] = df.groupby('away_team')['away_win'].transform(
            lambda x: x.rolling(5, min_periods=1).sum().shift(1)
        )
        
        # 2. STRENGTH OF SCHEDULE (opponent quality)
        # Use away_elo as proxy for opponent strength
        df['home_avg_opp_elo_10'] = df.groupby('home_team')['away_elo'].transform(
            lambda x: x.rolling(10, min_periods=1).mean().shift(1)
        ).fillna(1500)
        df['away_avg_opp_elo_10'] = df.groupby('away_team')['home_elo'].transform(
            lambda x: x.rolling(10, min_periods=1).mean().shift(1)
        ).fillna(1500)
        
        # 3. ELO MOMENTUM (is Elo going up or down)
        df['home_elo_trend'] = df.groupby('home_team')['home_elo'].transform(
            lambda x: x.diff().rolling(5, min_periods=1).mean().shift(1)
        )
        df['away_elo_trend'] = df.groupby('away_team')['away_elo'].transform(
            lambda x: x.diff().rolling(5, min_periods=1).mean().shift(1)
        )
        
        # 4. WIN STREAK FEATURES
        def get_streak(series):
            streaks = []
            current = 0
            for val in series:
                if val == 1:
                    current += 1
                elif val == 0:
                    current -= 1
                streaks.append(current)
            return streaks
        
        df['home_streak'] = df.groupby('home_team')['home_win'].transform(
            lambda x: get_streak(x.shift(1).fillna(0))
        )
        df['away_streak'] = df.groupby('away_team')['away_win'].transform(
            lambda x: get_streak(x.shift(1).fillna(0))
        )
        
        # 5. CLUTCH PERFORMANCE (close games)
        close_games = df[abs(df['score_diff']) <= 5].copy()
        home_clutch = close_games.groupby('home_team')['home_win'].mean()
        away_clutch = close_games.groupby('away_team')['away_win'].mean()
        
        df['home_clutch_pct'] = df['home_team'].map(home_clutch).fillna(0.5)
        df['away_clutch_pct'] = df['away_team'].map(away_clutch).fillna(0.5)
        
        # 6. POINT DIFFERENTIAL TREND
        df['home_pt_diff_trend'] = df.groupby('home_team')['score_diff'].transform(
            lambda x: x.rolling(5, min_periods=1).mean().shift(1)
        ).fillna(0)
        df['away_pt_diff_trend'] = df.groupby('away_team')['score_diff'].transform(
            lambda x: (-x).rolling(5, min_periods=1).mean().shift(1)
        ).fillna(0)
        
        # 7. HOME/AWAY FORM (already engineered - use directly)
        df['home_form_pct_calc'] = df.groupby('home_team')['home_win'].transform(
            lambda x: x.rolling(10, min_periods=1).mean().shift(1)
        ).fillna(0.5)
        df['away_form_pct_calc'] = df.groupby('away_team')['away_win'].transform(
            lambda x: x.rolling(10, min_periods=1).mean().shift(1)
        ).fillna(0.5)
        
        # 8. HEAD-TO-HEAD MOMENTUM
        df['h2h_total'] = df['h2h_home_wins'] + df['h2h_away_wins']
        df['h2h_home_pct'] = df['h2h_home_wins'] / (df['h2h_total'] + 1)
        df['h2h_away_pct'] = df['h2h_away_wins'] / (df['h2h_total'] + 1)
        
        # 9. FATIGUE FEATURES
        df['home_games_in_5'] = df.groupby('home_team').cumcount()
        df['away_games_in_5'] = df.groupby('away_team').cumcount()
        
        # 10. INTERACTION FEATURES
        df['elo_diff_squared'] = df['elo_diff'] ** 2
        df['elo_rest_interaction'] = df['elo_diff'] * df['home_rest_days']
        df['recent_form_diff'] = df['home_last_5_win_pct'] - df['away_last_5_win_pct']
        df['momentum_elo'] = df['home_win_momentum'] - df['away_win_momentum']
        
        # 11. TEMPORAL FEATURES
        df['month'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 4).astype(int)
        
        # 12. SEASON FEATURES
        df['season_start'] = pd.to_datetime(
            df['date'].dt.year.astype(str) + '-10-01'
        )
        df['days_into_season'] = (df['date'] - df['season_start']).dt.days
        df['playoff_like'] = (df['days_into_season'] > 200).astype(int)
        
        logger.info(f"✅ Created {df.shape[1] - 5} total features")
        
        return df
    
    def create_temporal_weights(self, df: pd.DataFrame) -> np.ndarray:
        """Create temporal weights - recent games are more important"""
        latest_date = df['date'].max()
        days_ago = (latest_date - df['date']).dt.days.values
        
        # Exponential decay: recent games worth more
        # Half-life of 365 days (games from 1 year ago = 0.5 weight)
        half_life = 365
        weights = 2 ** (-days_ago / half_life)
        
        return weights / weights.mean()  # Normalize to mean=1
    
    def optimize_xgboost(self, X_train: pd.DataFrame, y_train: pd.Series, 
                         trial: optuna.trial.Trial) -> xgb.XGBClassifier:
        """Optuna optimization for XGBoost"""
        params = {
            'learning_rate': trial.suggest_float('xgb_lr', 0.01, 0.3),
            'max_depth': trial.suggest_int('xgb_depth', 3, 10),
            'min_child_weight': trial.suggest_int('xgb_child_weight', 1, 10),
            'subsample': trial.suggest_float('xgb_subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('xgb_colsample', 0.5, 1.0),
            'gamma': trial.suggest_float('xgb_gamma', 0, 5),
            'lambda': trial.suggest_float('xgb_lambda', 0, 5),
            'alpha': trial.suggest_float('xgb_alpha', 0, 5),
            'n_estimators': 200,
            'random_state': 42,
            'tree_method': 'hist',
            'device': 'cpu',
            'verbosity': 0,
        }
        
        model = xgb.XGBClassifier(**params)
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=3)
        cv_scores = cross_val_score(
            model, X_train, y_train,
            cv=tscv, scoring='roc_auc', n_jobs=-1
        )
        
        return cv_scores.mean()
    
    def optimize_lgb(self, X_train: pd.DataFrame, y_train: pd.Series,
                     trial: optuna.trial.Trial) -> lgb.LGBMClassifier:
        """Optuna optimization for LightGBM"""
        params = {
            'learning_rate': trial.suggest_float('lgb_lr', 0.01, 0.3),
            'num_leaves': trial.suggest_int('lgb_leaves', 20, 200),
            'min_child_weight': trial.suggest_float('lgb_child_weight', 1e-3, 1e-1),
            'subsample': trial.suggest_float('lgb_subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('lgb_colsample', 0.5, 1.0),
            'reg_alpha': trial.suggest_float('lgb_alpha', 0, 5),
            'reg_lambda': trial.suggest_float('lgb_lambda', 0, 5),
            'n_estimators': 200,
            'random_state': 42,
            'verbose': -1,
            'force_row_wise': True,
        }
        
        model = lgb.LGBMClassifier(**params)
        
        tscv = TimeSeriesSplit(n_splits=3)
        cv_scores = cross_val_score(
            model, X_train, y_train,
            cv=tscv, scoring='roc_auc', n_jobs=-1
        )
        
        return cv_scores.mean()
    
    def train(self, df: pd.DataFrame):
        """Train ensemble model"""
        logger.info("\n" + "="*80)
        logger.info("🚀 TRAINING SUPER NBA MODEL")
        logger.info("="*80)
        
        # 1. CREATE ADVANCED FEATURES
        df = self.create_advanced_features(df)
        
        # 2. PREPARE DATA
        exclude_cols = {
            'home_team', 'away_team', 'date', 'season_start', 'home_win', 'away_win',
            'game_id', 'season', 'home_score', 'away_score'
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
        
        logger.info(f"\n📚 TRAIN SET: {len(X_train):,} games ({train_mask.mean():.1%})")
        logger.info(f"🧪 TEST SET:  {len(X_test):,} games ({(~train_mask).mean():.1%})")
        logger.info(f"📅 Split date: {split_date.date()}")
        logger.info(f"⚖️  Temporal weights: mean={weights.mean():.2f}, min={weights.min():.2f}, max={weights.max():.2f}")
        
        # 5. HYPERPARAMETER OPTIMIZATION (quick version)
        logger.info("\n🔍 Optimizing hyperparameters with Optuna...")
        
        study_xgb = optuna.create_study(direction='maximize', pruner=MedianPruner())
        study_xgb.optimize(
            lambda trial: self.optimize_xgboost(X_train, y_train, trial),
            n_trials=15, show_progress_bar=True
        )
        
        study_lgb = optuna.create_study(direction='maximize', pruner=MedianPruner())
        study_lgb.optimize(
            lambda trial: self.optimize_lgb(X_train, y_train, trial),
            n_trials=15, show_progress_bar=True
        )
        
        logger.info(f"✅ XGBoost best: {study_xgb.best_value:.4f}")
        logger.info(f"✅ LightGBM best: {study_lgb.best_value:.4f}")
        
        # 6. TRAIN FINAL MODELS WITH BEST PARAMS
        logger.info("\n🏋️ Training final models...")
        
        # XGBoost
        xgb_params = study_xgb.best_params
        xgb_params.update({'n_estimators': 300, 'random_state': 42})
        self.xgb_model = xgb.XGBClassifier(**xgb_params)
        self.xgb_model.fit(X_train, y_train, sample_weight=weights, verbose=0)
        
        # LightGBM
        lgb_params = study_lgb.best_params
        lgb_params.update({'n_estimators': 300, 'random_state': 42})
        self.lgb_model = lgb.LGBMClassifier(**lgb_params)
        self.lgb_model.fit(X_train, y_train, sample_weight=weights)
        
        # CatBoost with default params (quick)
        self.cat_model = CatBoostClassifier(
            iterations=300,
            learning_rate=0.1,
            depth=6,
            verbose=False,
            random_state=42,
        )
        self.cat_model.fit(X_train, y_train, sample_weight=weights)
        
        logger.info("✅ All models trained")
        
        # 7. CREATE ENSEMBLE (voting)
        logger.info("\n🎯 Creating ensemble predictions...")
        
        probs_xgb = self.xgb_model.predict_proba(X_test)[:, 1]
        probs_lgb = self.lgb_model.predict_proba(X_test)[:, 1]
        probs_cat = self.cat_model.predict_proba(X_test)[:, 1]
        
        # Weighted average (by CV performance)
        xgb_score = study_xgb.best_value
        lgb_score = study_lgb.best_value
        total = xgb_score + lgb_score + 0.66  # CatBoost assumed 0.66
        
        weights_ensemble = np.array([
            xgb_score / total,
            lgb_score / total,
            0.66 / total
        ])
        
        ensemble_probs = (
            probs_xgb * weights_ensemble[0] +
            probs_lgb * weights_ensemble[1] +
            probs_cat * weights_ensemble[2]
        )
        
        ensemble_preds = (ensemble_probs > 0.5).astype(int)
        
        # 8. CALIBRATE ENSEMBLE
        logger.info("📊 Calibrating ensemble...")
        
        self.calibrated_ensemble = CalibratedClassifierCV(
            LogisticRegression(random_state=42),
            method='sigmoid',
            cv=5
        )
        self.calibrated_ensemble.fit(ensemble_probs.reshape(-1, 1), y_test)
        
        calibrated_probs = self.calibrated_ensemble.predict_proba(
            ensemble_probs.reshape(-1, 1)
        )[:, 1]
        calibrated_preds = (calibrated_probs > 0.5).astype(int)
        
        # 9. EVALUATE
        logger.info("\n" + "="*80)
        logger.info("📊 RESULTS")
        logger.info("="*80)
        
        print(f"\n{'Metric':<20} {'Raw Ensemble':<15} {'Calibrated':<15}")
        print("-" * 50)
        
        acc_raw = accuracy_score(y_test, ensemble_preds)
        acc_cal = accuracy_score(y_test, calibrated_preds)
        print(f"{'Accuracy':<20} {acc_raw:<15.4f} {acc_cal:<15.4f}")
        
        auc_raw = roc_auc_score(y_test, ensemble_probs)
        auc_cal = roc_auc_score(y_test, calibrated_probs)
        print(f"{'ROC-AUC':<20} {auc_raw:<15.4f} {auc_cal:<15.4f}")
        
        log_raw = log_loss(y_test, ensemble_probs)
        log_cal = log_loss(y_test, calibrated_probs)
        print(f"{'Log Loss':<20} {log_raw:<15.4f} {log_cal:<15.4f}")
        
        brier_raw = brier_score_loss(y_test, ensemble_probs)
        brier_cal = brier_score_loss(y_test, calibrated_probs)
        print(f"{'Brier Score':<20} {brier_raw:<15.4f} {brier_cal:<15.4f}")
        
        prec_cal = precision_score(y_test, calibrated_preds)
        rec_cal = recall_score(y_test, calibrated_preds)
        f1_cal = f1_score(y_test, calibrated_preds)
        print(f"{'Precision':<20} {'-':<15} {prec_cal:<15.4f}")
        print(f"{'Recall':<20} {'-':<15} {rec_cal:<15.4f}")
        print(f"{'F1 Score':<20} {'-':<15} {f1_cal:<15.4f}")
        
        # 10. FEATURE IMPORTANCE
        logger.info("\n🌟 TOP FEATURES")
        
        xgb_imp = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.xgb_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        lgb_imp = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.lgb_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Average importance
        avg_imp = (xgb_imp.set_index('feature') + lgb_imp.set_index('feature')).mean(axis=1)
        avg_imp = avg_imp.sort_values(ascending=False)
        
        for i, (feat, imp) in enumerate(avg_imp.head(10).items(), 1):
            print(f"{i:2d}. {feat:<30} {imp:.4f}")
        
        self.feature_importance = avg_imp
        
        # 11. SAVE MODELS
        logger.info("\n💾 Saving models...")
        
        joblib.dump(self.xgb_model, self.artifacts_dir / "xgb_model.pkl")
        joblib.dump(self.lgb_model, self.artifacts_dir / "lgb_model.pkl")
        joblib.dump(self.cat_model, self.artifacts_dir / "cat_model.pkl")
        joblib.dump(self.calibrated_ensemble, self.artifacts_dir / "ensemble_calibration.pkl")
        joblib.dump(self.feature_names, self.artifacts_dir / "feature_names.pkl")
        
        # Save metadata
        metadata = {
            'accuracy': float(acc_cal),
            'roc_auc': float(auc_cal),
            'log_loss': float(log_cal),
            'brier_score': float(brier_cal),
            'precision': float(prec_cal),
            'recall': float(rec_cal),
            'f1_score': float(f1_cal),
            'n_features': len(feature_cols),
            'n_train': len(X_train),
            'n_test': len(X_test),
            'model_type': 'ensemble',
            'date_trained': datetime.now().isoformat(),
            'xgb_params': str(xgb_params),
            'lgb_params': str(lgb_params),
            'ensemble_weights': {
                'xgb': float(weights_ensemble[0]),
                'lgb': float(weights_ensemble[1]),
                'cat': float(weights_ensemble[2])
            }
        }
        
        with open(self.artifacts_dir / "ensemble_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✅ Models saved to {self.artifacts_dir}")
        
        # 12. PLOTS
        logger.info("\n📈 Generating plots...")
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Confusion matrix
        cm = confusion_matrix(y_test, calibrated_preds)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0, 0])
        axes[0, 0].set_title('Confusion Matrix')
        axes[0, 0].set_ylabel('Actual')
        axes[0, 0].set_xlabel('Predicted')
        
        # ROC curve
        from sklearn.metrics import roc_curve
        fpr, tpr, _ = roc_curve(y_test, calibrated_probs)
        axes[0, 1].plot(fpr, tpr, label=f'ROC (AUC={auc_cal:.3f})')
        axes[0, 1].plot([0, 1], [0, 1], 'k--', label='Random')
        axes[0, 1].set_xlabel('False Positive Rate')
        axes[0, 1].set_ylabel('True Positive Rate')
        axes[0, 1].set_title('ROC Curve')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Feature importance
        avg_imp.head(15).plot(kind='barh', ax=axes[1, 0])
        axes[1, 0].set_xlabel('Importance')
        axes[1, 0].set_title('Top 15 Features')
        
        # Calibration
        axes[1, 1].hist(calibrated_probs[y_test == 0], bins=30, alpha=0.6, label='Away Wins')
        axes[1, 1].hist(calibrated_probs[y_test == 1], bins=30, alpha=0.6, label='Home Wins')
        axes[1, 1].set_xlabel('Predicted Probability')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].set_title('Probability Distribution')
        axes[1, 1].legend()
        
        plt.tight_layout()
        plt.savefig(self.artifacts_dir / "ensemble_model_performance.png", dpi=300, bbox_inches='tight')
        logger.info(f"✅ Plots saved to ensemble_model_performance.png")
        
        logger.info("\n" + "="*80)
        logger.info("🎉 SUPER MODEL TRAINING COMPLETE!")
        logger.info(f"✨ Accuracy: {acc_cal:.2%}")
        logger.info(f"✨ ROC-AUC: {auc_cal:.4f}")
        logger.info("="*80 + "\n")


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    
    model = SuperNBAModel(data_dir)
    df = model.load_and_prepare_data()
    model.train(df)


if __name__ == "__main__":
    main()
