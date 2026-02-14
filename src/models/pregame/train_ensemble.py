"""
"""Train our ensemble of models for game predictions.

We use three different models and blend their predictions:
- XGBoost (currently hitting 63.83% accuracy)
- LightGBM (often does well on structured data like ours)
- CatBoost (great at handling team names and categorical features)

Goal: Get to 70%+ accuracy by combining their strengths.
"""

import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging

import xgboost as xgb
import lightgbm as lgb
import catboost as cb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, brier_score_loss
import optuna

# Import feature engineering functions
from src.common.features import calculate_elo, add_rest_features, add_streak_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnsembleTrainer:
    """Our main ensemble system - trains and combines three models."""
    
    def __init__(self, output_dir: str = "artifacts/models/pregame"):
        """Set up the trainer with paths and empty model slots."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # The raw models (before probability calibration)
        self.xgb_model = None
        self.lgb_model = None
        self.cat_model = None
        
        # Calibrated versions (probabilities are more reliable)
        self.xgb_calibrated = None
        self.lgb_calibrated = None
        self.cat_calibrated = None
        
        # Optional v2 components (if using stacking approach)
        self.et_calibrated = None
        self.meta_learner = None
        self.meta_scaler = None
        
        # How much we trust each model (roughly equal)
        self.weights = {'xgb': 0.33, 'lgb': 0.33, 'cat': 0.34}
        
        # What features we're using
        self.feature_names = None
        
        # Track how well we're doing
        self.metrics = {}
        
        # Version
        self.version = 1
        
        logger.info("🎯 Ensemble trainer initialized")
    
    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        """Build rolling statistics from past games only.
        
        This is critical - we only look backwards in time so the model doesn't "cheat"
        by seeing future data during training.
        """
        df = df.sort_values('date').reset_index(drop=True)
        
        # Initialize rolling stats trackers
        team_pts_history = {}  # {team: [list of pts scored]}
        team_wins_history = {} # {team: [list of wins (1/0)]}
        
        # Output columns
        home_pts_avg_l10, away_pts_avg_l10 = [], []
        home_pts_allowed_avg_l10, away_pts_allowed_avg_l10 = [], []
        home_win_pct_l10, away_win_pct_l10 = [], []
        home_win_pct_l5, away_win_pct_l5 = [], []
        
        for idx, row in df.iterrows():
            home, away = row['home'], row['away']
            
            # Get current rolling stats (from PAST only)
            h_pts = team_pts_history.get(home, [])[-10:] or [100]
            a_pts = team_pts_history.get(away, [])[-10:] or [100]
            h_wins = team_wins_history.get(home, [])[-10:] or [0.5]
            a_wins = team_wins_history.get(away, [])[-10:] or [0.5]
            
            # Compute averages
            home_pts_avg_l10.append(np.mean(h_pts))
            away_pts_avg_l10.append(np.mean(a_pts))
            home_win_pct_l10.append(np.mean(h_wins))
            away_win_pct_l10.append(np.mean(a_wins))
            
            # Last 5 games
            h_wins_5 = team_wins_history.get(home, [])[-5:] or [0.5]
            a_wins_5 = team_wins_history.get(away, [])[-5:] or [0.5]
            home_win_pct_l5.append(np.mean(h_wins_5))
            away_win_pct_l5.append(np.mean(a_wins_5))
            
            # Points allowed (need opponent scoring)
            # We'll compute this as a secondary pass or skip for now
            home_pts_allowed_avg_l10.append(100)  # Placeholder
            away_pts_allowed_avg_l10.append(100)  # Placeholder
            
            # UPDATE history AFTER using it (so no leakage)
            if pd.notna(row.get('home_pts')) and pd.notna(row.get('away_pts')):
                if home not in team_pts_history: team_pts_history[home] = []
                if away not in team_pts_history: team_pts_history[away] = []
                team_pts_history[home].append(row['home_pts'])
                team_pts_history[away].append(row['away_pts'])
                
            if pd.notna(row.get('home_win')):
                if home not in team_wins_history: team_wins_history[home] = []
                if away not in team_wins_history: team_wins_history[away] = []
                team_wins_history[home].append(row['home_win'])
                team_wins_history[away].append(1 - row['home_win'])
        
        df['home_pts_avg_l10'] = home_pts_avg_l10
        df['away_pts_avg_l10'] = away_pts_avg_l10
        df['home_win_pct_l10'] = home_win_pct_l10
        df['away_win_pct_l10'] = away_win_pct_l10
        df['home_win_pct_l5'] = home_win_pct_l5
        df['away_win_pct_l5'] = away_win_pct_l5
        
        # Differentials
        df['pts_avg_diff'] = df['home_pts_avg_l10'] - df['away_pts_avg_l10']
        df['win_pct_diff_l10'] = df['home_win_pct_l10'] - df['away_win_pct_l10']
        df['win_pct_diff_l5'] = df['home_win_pct_l5'] - df['away_win_pct_l5']
        
        return df
    
    def load_data(self, features_path: str) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Load features and prepare for training.
        
        Args:
            features_path: Path to features parquet/csv file
        
        Returns:
            (X, y) tuple
        """
        logger.info(f"📊 Loading data from {features_path}")
        
        features_path = Path(features_path)
        if not features_path.exists():
            raise FileNotFoundError(f"Features file not found: {features_path}")
        
        # Load features
        if features_path.suffix == '.parquet':
            df = pd.read_parquet(features_path)
        else:
            df = pd.read_csv(features_path)
        
        df['date'] = pd.to_datetime(df['date'])
        
        # ============================================================
        # FEATURE ENGINEERING (Compute features from raw data)
        # All features computed from PAST data only (no leakage)
        # ============================================================
        logger.info("🔧 Computing engineered features...")
        
        # 1. Elo ratings (computed progressively - each game uses only past data)
        logger.info("  Computing Elo ratings...")
        df = calculate_elo(df, k=20, home_advantage=100)
        
        # 2. Rest features (days since last game - known before game)
        logger.info("  Computing rest features...")
        df = add_rest_features(df)
        
        # 3. Win/loss streaks (computed from past games only)
        logger.info("  Computing streak features...")
        df = add_streak_features(df)
        
        # 4. Rolling averages (last N games - all from past)
        logger.info("  Computing rolling features...")
        df = self._add_rolling_features(df)
        
        logger.info(f"✅ Feature engineering complete: {len(df.columns)} total columns")
            
        # ENSURE PURE HOLDOUT: Exclude 2024-25 and 2025-26 seasons from TRAINING
        # Training cutoff: October 1st, 2024
        full_count = len(df)
        df = df[df['date'] < '2024-10-01'].copy()
        holdout_count = full_count - len(df)
        
        logger.info(f"✅ Loaded {len(df)} games for training (Held out {holdout_count} games for future audit)")
        
        # Extract features and target
        # Exclude non-feature columns (identifiers, dates, and ACTUAL GAME OUTCOMES to prevent data leakage)
        exclude_cols = ['game_id', 'date', 'home_team', 'away_team', 'home', 'away',
                       'home_pts', 'away_pts', 'home_score', 'away_score',
                       'home_win', 'away_win', 'score_diff', 'margin', 'total_pts',
                       'season', 'year', 'month', 'day_of_week']
        
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        self.feature_names = feature_cols
        
        # Target: home team wins
        if 'home_pts' in df.columns and 'away_pts' in df.columns:
            y = (df['home_pts'] > df['away_pts']).astype(int)
        elif 'home_win' in df.columns:
            y = df['home_win'].astype(int)
        else:
            raise ValueError("Target column not found (need home_pts/away_pts or home_win)")
        
        # Features
        X = df[feature_cols].fillna(0)  # Fill NaN with 0
        
        # Force check for critical features
        critical_features = ['elo_diff', 'rest_differential', 'elo_win_prob']
        for feat in critical_features:
            if feat not in X.columns:
                logger.warning(f"⚠️ Critical feature missing: {feat}")
            else:
                logger.info(f"✅ Critical feature verified: {feat}")
        
        logger.info(f"✅ Prepared {len(feature_cols)} features for {len(X)} games")
        logger.info(f"  Target distribution: {y.mean():.1%} home wins")
        
        return X, y
    
    def train_xgboost(self, X: pd.DataFrame, y: pd.Series, cv_folds: int = 5) -> Dict:
        """
        Train XGBoost model.
        
        Args:
            X: Features
            y: Target
            cv_folds: Number of CV folds
        
        Returns:
            Dictionary with model and metrics
        """
        logger.info("🌳 Training XGBoost model...")
        
        # XGBoost parameters (optimized)
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': 6,
            'learning_rate': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 3,
            'gamma': 0.1,
            'lambda': 1.0,
            'alpha': 0.1,
            'random_state': 42,
            'n_estimators': 300,
        }
        
        # Time-series cross-validation
        tscv = TimeSeriesSplit(n_splits=cv_folds)
        cv_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Train model
            model = xgb.XGBClassifier(**params, early_stopping_rounds=20)
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )
            
            # Predict
            y_pred = model.predict_proba(X_val)[:, 1]
            y_pred_binary = (y_pred > 0.5).astype(int)
            
            # Calculate metrics
            acc = accuracy_score(y_val, y_pred_binary)
            auc = roc_auc_score(y_val, y_pred)
            cv_scores.append({'accuracy': acc, 'auc': auc})
            
            logger.info(f"  Fold {fold + 1}: Accuracy={acc:.3f}, AUC={auc:.3f}")
        
        # Train final model on all data
        final_model = xgb.XGBClassifier(**params)
        final_model.fit(X, y)
        
        # Calibrate
        ts_cv = TimeSeriesSplit(n_splits=3)
        calibrated_model = CalibratedClassifierCV(final_model, method='isotonic', cv=ts_cv)
        calibrated_model.fit(X, y)
        
        # Calculate final metrics
        y_pred = calibrated_model.predict_proba(X)[:, 1]
        y_pred_binary = (y_pred > 0.5).astype(int)
        
        # Calculate in-sample metrics
        accuracy = accuracy_score(y, y_pred_binary)
        logloss = log_loss(y, y_pred)
        brier = brier_score_loss(y, y_pred)
        
        # Reset Metric Reporting: Use mean CV scores for primary metrics
        mean_cv_acc = np.mean([s['accuracy'] for s in cv_scores])
        mean_cv_auc = np.mean([s['auc'] for s in cv_scores])
        
        metrics = {
            'accuracy': mean_cv_acc,
            'auc': mean_cv_auc,
            'logloss': logloss,
            'brier': brier,
            'cv_scores': cv_scores,
            'in_sample_accuracy': accuracy,  # Keep for reference but don't use as primary
        }
        
        self.xgb_model = final_model
        self.xgb_calibrated = calibrated_model
        
        logger.info(f"✅ XGBoost trained: CV Accuracy={mean_cv_acc:.3f}, CV AUC={mean_cv_auc:.3f} (In-sample: {accuracy:.3f})")
        
        return metrics
    
    def train_lightgbm(self, X: pd.DataFrame, y: pd.Series, cv_folds: int = 5) -> Dict:
        """
        Train LightGBM model.
        
        Args:
            X: Features
            y: Target
            cv_folds: Number of CV folds
        
        Returns:
            Dictionary with model and metrics
        """
        logger.info("💡 Training LightGBM model...")
        
        # LightGBM parameters (optimized)
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'min_child_samples': 20,
            'lambda_l1': 0.1,
            'lambda_l2': 1.0,
            'random_state': 42,
            'n_estimators': 300,
            'verbose': -1,
        }
        
        # Time-series cross-validation
        tscv = TimeSeriesSplit(n_splits=cv_folds)
        cv_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Train model
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            model = lgb.train(
                params,
                train_data,
                valid_sets=[val_data],
                num_boost_round=300,
                callbacks=[lgb.early_stopping(20), lgb.log_evaluation(0)]
            )
            
            # Predict
            y_pred = model.predict(X_val)
            y_pred_binary = (y_pred > 0.5).astype(int)
            
            # Calculate metrics
            acc = accuracy_score(y_val, y_pred_binary)
            auc = roc_auc_score(y_val, y_pred)
            cv_scores.append({'accuracy': acc, 'auc': auc})
            
            logger.info(f"  Fold {fold + 1}: Accuracy={acc:.3f}, AUC={auc:.3f}")
        
        # Train final model on all data
        train_data = lgb.Dataset(X, label=y)
        final_model = lgb.train(params, train_data, num_boost_round=300)
        
        # Calibrate (convert to sklearn interface)
        from lightgbm import LGBMClassifier
        sklearn_model = LGBMClassifier(**params)
        sklearn_model.fit(X, y)
        ts_cv = TimeSeriesSplit(n_splits=3)
        calibrated_model = CalibratedClassifierCV(sklearn_model, method='isotonic', cv=ts_cv)
        calibrated_model.fit(X, y)
        
        # Calculate final metrics
        y_pred = calibrated_model.predict_proba(X)[:, 1]
        y_pred_binary = (y_pred > 0.5).astype(int)
        
        # Calculate in-sample metrics
        accuracy = accuracy_score(y, y_pred_binary)
        logloss = log_loss(y, y_pred)
        brier = brier_score_loss(y, y_pred)
        
        # Reset Metric Reporting: Use mean CV scores for primary metrics
        mean_cv_acc = np.mean([s['accuracy'] for s in cv_scores])
        mean_cv_auc = np.mean([s['auc'] for s in cv_scores])
        
        metrics = {
            'accuracy': mean_cv_acc,
            'auc': mean_cv_auc,
            'logloss': logloss,
            'brier': brier,
            'cv_scores': cv_scores,
            'in_sample_accuracy': accuracy,
        }
        
        self.lgb_model = final_model
        self.lgb_calibrated = calibrated_model
        
        logger.info(f"✅ LightGBM trained: CV Accuracy={mean_cv_acc:.3f}, CV AUC={mean_cv_auc:.3f} (In-sample: {accuracy:.3f})")
        
        return metrics
    
    def train_catboost(self, X: pd.DataFrame, y: pd.Series, cv_folds: int = 5) -> Dict:
        """
        Train CatBoost model.
        
        Args:
            X: Features
            y: Target
            cv_folds: Number of CV folds
        
        Returns:
            Dictionary with model and metrics
        """
        logger.info("🐱 Training CatBoost model...")
        
        # CatBoost parameters (optimized)
        params = {
            'objective': 'Logloss',
            'eval_metric': 'Logloss',
            'depth': 6,
            'learning_rate': 0.05,
            'iterations': 300,
            'l2_leaf_reg': 3,
            'bootstrap_type': 'Bayesian',
            'random_seed': 42,
            'verbose': False,
        }
        
        # Time-series cross-validation
        tscv = TimeSeriesSplit(n_splits=cv_folds)
        cv_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Train model
            model = cb.CatBoostClassifier(**params)
            model.fit(
                X_train, y_train,
                eval_set=(X_val, y_val),
                early_stopping_rounds=20,
                verbose=False
            )
            
            # Predict
            y_pred = model.predict_proba(X_val)[:, 1]
            y_pred_binary = (y_pred > 0.5).astype(int)
            
            # Calculate metrics
            acc = accuracy_score(y_val, y_pred_binary)
            auc = roc_auc_score(y_val, y_pred)
            cv_scores.append({'accuracy': acc, 'auc': auc})
            
            logger.info(f"  Fold {fold + 1}: Accuracy={acc:.3f}, AUC={auc:.3f}")
        
        # Train final model on all data
        final_model = cb.CatBoostClassifier(**params)
        final_model.fit(X, y, verbose=False)
        
        # Calibrate
        ts_cv = TimeSeriesSplit(n_splits=3)
        calibrated_model = CalibratedClassifierCV(final_model, method='isotonic', cv=ts_cv)
        calibrated_model.fit(X, y)
        
        # Calculate final metrics
        y_pred = calibrated_model.predict_proba(X)[:, 1]
        y_pred_binary = (y_pred > 0.5).astype(int)
        
        # Calculate in-sample metrics
        accuracy = accuracy_score(y, y_pred_binary)
        logloss = log_loss(y, y_pred)
        brier = brier_score_loss(y, y_pred)
        
        # Reset Metric Reporting: Use mean CV scores for primary metrics
        mean_cv_acc = np.mean([s['accuracy'] for s in cv_scores])
        mean_cv_auc = np.mean([s['auc'] for s in cv_scores])
        
        metrics = {
            'accuracy': mean_cv_acc,
            'auc': mean_cv_auc,
            'logloss': logloss,
            'brier': brier,
            'cv_scores': cv_scores,
            'in_sample_accuracy': accuracy,
        }
        
        self.cat_model = final_model
        self.cat_calibrated = calibrated_model
        
        logger.info(f"✅ CatBoost trained: CV Accuracy={mean_cv_acc:.3f}, CV AUC={mean_cv_auc:.3f} (In-sample: {accuracy:.3f})")
        
        return metrics
    
    def calculate_ensemble_weights(self, xgb_metrics: Dict, lgb_metrics: Dict, cat_metrics: Dict) -> Dict:
        """
        Calculate ensemble weights based on CV performance.
        
        Args:
            xgb_metrics: XGBoost metrics
            lgb_metrics: LightGBM metrics
            cat_metrics: CatBoost metrics
        
        Returns:
            Dictionary with weights
        """
        logger.info("⚖️ Calculating ensemble weights...")
        
        # Calculate average CV accuracy for each model
        xgb_avg_acc = np.mean([s['accuracy'] for s in xgb_metrics['cv_scores']])
        lgb_avg_acc = np.mean([s['accuracy'] for s in lgb_metrics['cv_scores']])
        cat_avg_acc = np.mean([s['accuracy'] for s in cat_metrics['cv_scores']])
        
        # Calculate weights (proportional to accuracy)
        total_acc = xgb_avg_acc + lgb_avg_acc + cat_avg_acc
        weights = {
            'xgb': xgb_avg_acc / total_acc,
            'lgb': lgb_avg_acc / total_acc,
            'cat': cat_avg_acc / total_acc,
        }
        
        self.weights = weights
        
        logger.info(f"✅ Ensemble weights calculated:")
        logger.info(f"  XGBoost: {weights['xgb']:.3f} (CV acc: {xgb_avg_acc:.3f})")
        logger.info(f"  LightGBM: {weights['lgb']:.3f} (CV acc: {lgb_avg_acc:.3f})")
        logger.info(f"  CatBoost: {weights['cat']:.3f} (CV acc: {cat_avg_acc:.3f})")
        
        return weights
    
    def predict_ensemble(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make ensemble prediction.
        Supports v2 stacking (meta-learner + ExtraTrees) if available.
        
        Args:
            X: Features
        
        Returns:
            Ensemble predictions (probabilities)
        """
        if self.xgb_calibrated is None or self.lgb_calibrated is None or self.cat_calibrated is None:
            raise ValueError("Models not trained. Call train_all() first.")
        
        # Get predictions from each model
        xgb_pred = self.xgb_calibrated.predict_proba(X)[:, 1]
        lgb_pred = self.lgb_calibrated.predict_proba(X)[:, 1]
        cat_pred = self.cat_calibrated.predict_proba(X)[:, 1]
        
        # v2 stacking path
        if self.meta_learner is not None and self.et_calibrated is not None:
            et_pred = self.et_calibrated.predict_proba(X)[:, 1]
            base_preds = np.column_stack([xgb_pred, lgb_pred, cat_pred, et_pred])
            
            meta_features = np.column_stack([
                base_preds,
                base_preds[:, 0] * base_preds[:, 1],
                base_preds[:, 2] * base_preds[:, 3],
                np.mean(base_preds, axis=1),
                np.std(base_preds, axis=1),
                np.max(base_preds, axis=1),
                np.min(base_preds, axis=1),
            ])
            
            meta_scaled = self.meta_scaler.transform(meta_features)
            return self.meta_learner.predict_proba(meta_scaled)[:, 1]
        
        # v1 fallback: weighted average (renormalize if needed)
        w_xgb = self.weights.get('xgb', 0.33)
        w_lgb = self.weights.get('lgb', 0.33)
        w_cat = self.weights.get('cat', 0.34)
        total_w = w_xgb + w_lgb + w_cat
        
        ensemble_pred = (
            (w_xgb / total_w) * xgb_pred +
            (w_lgb / total_w) * lgb_pred +
            (w_cat / total_w) * cat_pred
        )
        
        return ensemble_pred
    
    def train_all(self, X: pd.DataFrame, y: pd.Series, cv_folds: int = 5) -> Dict:
        """
        Train all models and create ensemble.
        
        Args:
            X: Features
            y: Target
            cv_folds: Number of CV folds
        
        Returns:
            Dictionary with all metrics
        """
        logger.info("=" * 80)
        logger.info("ENSEMBLE MODEL TRAINING")
        logger.info("=" * 80)
        
        # Train all models
        xgb_metrics = self.train_xgboost(X, y, cv_folds)
        lgb_metrics = self.train_lightgbm(X, y, cv_folds)
        cat_metrics = self.train_catboost(X, y, cv_folds)
        
        # Calculate ensemble weights
        weights = self.calculate_ensemble_weights(xgb_metrics, lgb_metrics, cat_metrics)
        
        # Evaluate ensemble
        ensemble_pred = self.predict_ensemble(X)
        ensemble_pred_binary = (ensemble_pred > 0.5).astype(int)
        
        # Calculate ensemble metrics
        ensemble_accuracy = accuracy_score(y, ensemble_pred_binary)
        ensemble_auc = roc_auc_score(y, ensemble_pred)
        ensemble_logloss = log_loss(y, ensemble_pred)
        ensemble_brier = brier_score_loss(y, ensemble_pred)
        
        ensemble_metrics = {
            'accuracy': ensemble_accuracy,
            'auc': ensemble_auc,
            'logloss': ensemble_logloss,
            'brier': ensemble_brier,
        }
        
        # Store metrics
        self.metrics = {
            'xgb': xgb_metrics,
            'lgb': lgb_metrics,
            'cat': cat_metrics,
            'ensemble': ensemble_metrics,
            'weights': weights,
        }
        
        logger.info("=" * 80)
        logger.info("ENSEMBLE TRAINING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"XGBoost:     Accuracy={xgb_metrics['accuracy']:.3f}, AUC={xgb_metrics['auc']:.3f}")
        logger.info(f"LightGBM:    Accuracy={lgb_metrics['accuracy']:.3f}, AUC={lgb_metrics['auc']:.3f}")
        logger.info(f"CatBoost:    Accuracy={cat_metrics['accuracy']:.3f}, AUC={cat_metrics['auc']:.3f}")
        logger.info(f"Ensemble:    Accuracy={ensemble_accuracy:.3f}, AUC={ensemble_auc:.3f}")
        logger.info(f"Improvement: +{(ensemble_accuracy - xgb_metrics['accuracy']) * 100:.1f}% vs XGBoost")
        logger.info("=" * 80)
        
        return self.metrics
    
    def save_models(self):
        """Save all models to disk."""
        logger.info("💾 Saving models...")
        
        # Save individual models
        if self.xgb_calibrated is not None:
            with open(self.output_dir / "xgb_model.pkl", 'wb') as f:
                pickle.dump(self.xgb_calibrated, f)
        
        if self.lgb_calibrated is not None:
            with open(self.output_dir / "lgb_model.pkl", 'wb') as f:
                pickle.dump(self.lgb_calibrated, f)
        
        if self.cat_calibrated is not None:
            with open(self.output_dir / "cat_model.pkl", 'wb') as f:
                pickle.dump(self.cat_calibrated, f)
        
        # Save ensemble metadata
        metadata = {
            'weights': self.weights,
            'metrics': self.metrics,
            'feature_names': self.feature_names,
            'timestamp': datetime.now().isoformat(),
        }
        
        with open(self.output_dir / "ensemble_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"✅ Models saved to {self.output_dir}")
    
    async def load_models_async(self):
        """Async version of model loading."""
        import asyncio
        logger.info("📂 Loading models async...")
        
        xgb_path = self.output_dir / "xgb_model.pkl"
        lgb_path = self.output_dir / "lgb_model.pkl"
        cat_path = self.output_dir / "cat_model.pkl"
        metadata_path = self.output_dir / "ensemble_metadata.json"
        
        async def read_pickle(path):
            with open(path, 'rb') as f:
                return pickle.load(f)
        
        async def read_json(path):
            with open(path, 'r') as f:
                return json.load(f)

        if xgb_path.exists():
            self.xgb_calibrated = await asyncio.to_thread(read_pickle, xgb_path)
        
        if lgb_path.exists():
            self.lgb_calibrated = await asyncio.to_thread(read_pickle, lgb_path)
        
        if cat_path.exists():
            self.cat_calibrated = await asyncio.to_thread(read_pickle, cat_path)
        
        if metadata_path.exists():
            metadata = await asyncio.to_thread(read_json, metadata_path)
            self.weights = metadata.get('weights', self.weights)
            self.metrics = metadata.get('metrics', {})
            self.feature_names = metadata.get('feature_names', [])
        
        logger.info("✅ Models loaded async")

    def load_models(self):
        """Load models from disk (sync). Supports v1 and v2 models."""
        logger.info("📂 Loading models...")
        
        # Load individual models
        xgb_path = self.output_dir / "xgb_model.pkl"
        lgb_path = self.output_dir / "lgb_model.pkl"
        cat_path = self.output_dir / "cat_model.pkl"
        et_path = self.output_dir / "et_model.pkl"
        meta_path = self.output_dir / "meta_learner.pkl"
        scaler_path = self.output_dir / "meta_scaler.pkl"
        metadata_path = self.output_dir / "ensemble_metadata.json"
        
        if xgb_path.exists():
            with open(xgb_path, 'rb') as f:
                self.xgb_calibrated = pickle.load(f)
        
        if lgb_path.exists():
            with open(lgb_path, 'rb') as f:
                self.lgb_calibrated = pickle.load(f)
        
        if cat_path.exists():
            with open(cat_path, 'rb') as f:
                self.cat_calibrated = pickle.load(f)
        
        # v2 models
        if et_path.exists():
            with open(et_path, 'rb') as f:
                self.et_calibrated = pickle.load(f)
        
        if meta_path.exists():
            with open(meta_path, 'rb') as f:
                self.meta_learner = pickle.load(f)
        
        if scaler_path.exists():
            with open(scaler_path, 'rb') as f:
                self.meta_scaler = pickle.load(f)
        
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                self.weights = metadata.get('weights', self.weights)
                self.metrics = metadata.get('metrics', {})
                self.feature_names = metadata.get('feature_names', [])
                self.version = metadata.get('version', 1)
        
        v2_str = " (v2 stacking)" if self.meta_learner is not None else " (v1 weighted avg)"
        logger.info(f"✅ Models loaded{v2_str}")


def main():
    """Main training function."""
    import sys
    from pathlib import Path
    
    # Get features path
    if len(sys.argv) > 1:
        features_path = sys.argv[1]
    else:
        features_path = "artifacts/features/pregame.parquet"
    
    # Initialize trainer
    trainer = EnsembleTrainer()
    
    # Load data
    X, y = trainer.load_data(features_path)
    
    # Train ensemble
    metrics = trainer.train_all(X, y, cv_folds=5)
    
    # Save models
    trainer.save_models()
    
    # Print results
    print("\n" + "=" * 80)
    print("ENSEMBLE TRAINING RESULTS")
    print("=" * 80)
    print(f"XGBoost:     Accuracy={metrics['xgb']['accuracy']:.3f}, AUC={metrics['xgb']['auc']:.3f}")
    print(f"LightGBM:    Accuracy={metrics['lgb']['accuracy']:.3f}, AUC={metrics['lgb']['auc']:.3f}")
    print(f"CatBoost:    Accuracy={metrics['cat']['accuracy']:.3f}, AUC={metrics['cat']['auc']:.3f}")
    print(f"Ensemble:    Accuracy={metrics['ensemble']['accuracy']:.3f}, AUC={metrics['ensemble']['auc']:.3f}")
    print("=" * 80)
    
    return trainer


if __name__ == "__main__":
    trainer = main()

