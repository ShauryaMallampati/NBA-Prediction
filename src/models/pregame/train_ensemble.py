"""Train a calibrated XGBoost, LightGBM, and CatBoost pregame ensemble.

Cross-validation metrics and training-set diagnostics are reported separately.
Neither is a substitute for evaluating the frozen ensemble on later games.
"""

import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple
import logging

import xgboost as xgb
import lightgbm as lgb
import catboost as cb
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, brier_score_loss
from src.common.features import add_rest_features, add_streak_features, calculate_elo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnsembleTrainer:
    """Train and persist the supported three-model pregame ensemble."""

    FEATURE_NAMES = [
        'elo_home', 'elo_away', 'elo_diff', 'elo_win_prob', 'elo_p_home',
        'home_adv_flag', 'home_court_adv', 'home_rest_days', 'away_rest_days',
        'rest_differential', 'home_rest_advantage', 'away_rest_advantage',
        'home_back_to_back', 'away_back_to_back', 'home_win_streak',
        'away_win_streak', 'home_loss_streak', 'away_loss_streak',
        'home_pts_avg_l10', 'away_pts_avg_l10', 'home_win_pct_l10',
        'away_win_pct_l10', 'home_win_pct_l5', 'away_win_pct_l5',
        'pts_avg_diff', 'win_pct_diff_l10', 'win_pct_diff_l5',
    ]
    
    def __init__(self, output_dir: str = "artifacts/models/pregame", *,
                 n_estimators: int = 300, threads: int = 1):
        """Set up the trainer with paths and empty model slots."""
        if any(isinstance(value, bool) or not isinstance(value, int) or value < 1
               for value in (n_estimators, threads)):
            raise ValueError("n_estimators and threads must be positive integers")
        self.n_estimators = n_estimators
        self.threads = threads
        self.training_data = None
        self.training_dates = None
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
        
        self.weights = {'xgb': 0.33, 'lgb': 0.33, 'cat': 0.34}
        self.feature_names = None
        self.metrics = {}
        
        logger.info("Ensemble trainer initialized")
    
    @staticmethod
    def _add_rolling_features(df: pd.DataFrame) -> pd.DataFrame:
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
    
    @staticmethod
    def prepare_game_rows(frame: pd.DataFrame) -> pd.DataFrame:
        """Validate completed games before outcome-dependent state updates."""
        frame = frame.copy()
        for team in ('home', 'away'):
            if team not in frame and f'{team}_team' in frame:
                frame = frame.rename(columns={f'{team}_team': team})
        required = {'date', 'home', 'away'}
        if not required.issubset(frame.columns):
            raise ValueError(f"Missing game columns: {sorted(required - set(frame.columns))}")
        frame['date'] = pd.to_datetime(frame['date'], errors='raise')
        if frame[list(required)].isna().any().any():
            raise ValueError("Game dates and teams cannot be missing")
        if frame['date'].dt.tz is not None:
            raise ValueError("Use timezone-free game dates, not timestamps")
        frame['date'] = frame['date'].dt.normalize()
        for column in ('home', 'away'):
            if not frame[column].map(lambda value: isinstance(value, str) and bool(value.strip())).all():
                raise ValueError("Team names must be nonempty strings")
            frame[column] = frame[column].str.strip()
        if (frame['home'] == frame['away']).any():
            raise ValueError("A team cannot play itself")
        if frame.duplicated(['date', 'home', 'away']).any():
            raise ValueError("Duplicate games are not allowed")
        team_days = pd.concat([
            pd.DataFrame({'day': frame['date'].dt.normalize(), 'team': frame[team]})
            for team in ('home', 'away')
        ], ignore_index=True)
        if team_days.duplicated(['day', 'team']).any():
            raise ValueError("The daily feature contract supports one game per team per day")
        if 'home_pts' in frame and 'away_pts' in frame:
            scores = frame[['home_pts', 'away_pts']].apply(pd.to_numeric, errors='raise')
            if not np.isfinite(scores.to_numpy()).all() or (scores < 0).any().any():
                raise ValueError("Completed-game scores must be finite and nonnegative")
            if (scores['home_pts'] == scores['away_pts']).any():
                raise ValueError("Completed NBA games cannot have tied final scores")
            target = (scores['home_pts'] > scores['away_pts']).astype(int)
            if 'home_win' in frame:
                supplied = pd.to_numeric(frame['home_win'], errors='raise')
                if not (supplied == target).all():
                    raise ValueError("home_win disagrees with final scores")
            frame[['home_pts', 'away_pts']] = scores
            frame['home_win'] = target
        elif 'home_win' not in frame:
            raise ValueError("Completed games require home_win or both final scores")
        if not frame['home_win'].isin([0, 1]).all():
            raise ValueError("home_win must contain only 0 or 1")
        return frame.sort_values('date', kind='stable').reset_index(drop=True)

    @classmethod
    def engineer_game_rows(cls, frame: pd.DataFrame) -> pd.DataFrame:
        """Build the same causal features for both training and later evaluation.

        Outcome-dependent state is updated after each game's features are read.
        No team may appear twice on a date, so same-date row order is immaterial.
        """
        frame = cls.prepare_game_rows(frame)
        frame = calculate_elo(frame, k=20, home_advantage=100)
        frame = add_rest_features(frame)
        frame = add_streak_features(frame)
        return cls._add_rolling_features(frame)

    def _temporal_splits(self, X, y, n_splits):
        """Keep entire game dates together in expanding-window validation."""
        dates = self.training_dates
        if dates is None:
            # Preserve direct feature-matrix training for callers that supply
            # chronological rows. Without dates, no calendar provenance is
            # recorded and the later-game evaluation command will reject it.
            return list(TimeSeriesSplit(n_splits=n_splits).split(X))
        if len(dates) != len(X):
            raise ValueError("Training dates must align with the supplied feature rows")
        unique_dates = np.unique(dates)
        splits = []
        for train_days, validation_days in TimeSeriesSplit(n_splits=n_splits).split(unique_dates):
            train = np.flatnonzero(np.isin(dates, unique_dates[train_days]))
            validation = np.flatnonzero(np.isin(dates, unique_dates[validation_days]))
            if set(y.iloc[train].unique()) != {0, 1} or set(y.iloc[validation].unique()) != {0, 1}:
                raise ValueError("Each temporal training and validation fold needs both outcomes")
            splits.append((train, validation))
        return splits

    def load_data(self, features_path: str) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Load features and prepare for training.
        
        Args:
            features_path: Path to features parquet/csv file
        
        Returns:
            (X, y) tuple
        """
        logger.info("Loading data from %s", features_path)
        
        features_path = Path(features_path)
        if not features_path.exists():
            raise FileNotFoundError(f"Features file not found: {features_path}")
        
        # Load features
        if features_path.suffix == '.parquet':
            df = pd.read_parquet(features_path)
        else:
            df = pd.read_csv(features_path)
        
        df = self.engineer_game_rows(df)
        
        logger.info("Feature engineering complete: %d total columns", len(df.columns))
            
        # ENSURE PURE HOLDOUT: Exclude 2024-25 and 2025-26 seasons from TRAINING
        # Training cutoff: October 1st, 2024
        full_count = len(df)
        df = df[df['date'] < '2024-10-01'].copy()
        holdout_count = full_count - len(df)
        
        if df.empty:
            raise ValueError("No completed training games before 2024-10-01")
        import hashlib
        self.training_data = {
            'source_sha256': hashlib.sha256(features_path.read_bytes()).hexdigest(),
            'start_date': df['date'].min().date().isoformat(),
            'end_date': df['date'].max().date().isoformat(),
            'cutoff_exclusive': '2024-10-01',
            'games': len(df),
            'home_win_rate': float(df['home_win'].mean()),
        }
        logger.info(f"Loaded {len(df)} training games; excluded {holdout_count} later games.")
        
        # Never select arbitrary raw box-score columns as pregame features.
        feature_cols = list(self.FEATURE_NAMES)
        self.feature_names = feature_cols
        self.training_dates = df['date'].to_numpy()
        
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
                logger.warning("Critical feature missing: %s", feat)
            else:
                logger.info("Critical feature verified: %s", feat)
        
        logger.info("Prepared %d features for %d games", len(feature_cols), len(X))
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
            'n_jobs': self.threads,
            'n_estimators': self.n_estimators,
        }

        cv_scores = []
        for fold, (train_idx, val_idx) in enumerate(self._temporal_splits(X, y, cv_folds)):
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

        # Calibration also uses complete, chronologically separated game dates.
        ts_cv = self._temporal_splits(X, y, 3)
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
        
        logger.info("XGBoost trained: CV accuracy=%.3f, CV AUC=%.3f, in-sample accuracy=%.3f", mean_cv_acc, mean_cv_auc, accuracy)
        
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
            'num_threads': self.threads,
            'n_estimators': self.n_estimators,
            'verbose': -1,
        }

        cv_scores = []
        for fold, (train_idx, val_idx) in enumerate(self._temporal_splits(X, y, cv_folds)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            # Train model
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            model = lgb.train(
                params,
                train_data,
                valid_sets=[val_data],
                num_boost_round=self.n_estimators,
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
        final_model = lgb.train(params, train_data, num_boost_round=self.n_estimators)
        
        # Calibrate (convert to sklearn interface)
        from lightgbm import LGBMClassifier
        sklearn_model = LGBMClassifier(**params)
        sklearn_model.fit(X, y)
        ts_cv = self._temporal_splits(X, y, 3)
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
        
        logger.info("LightGBM trained: CV accuracy=%.3f, CV AUC=%.3f, in-sample accuracy=%.3f", mean_cv_acc, mean_cv_auc, accuracy)
        
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
            'iterations': self.n_estimators,
            'thread_count': self.threads,
            'allow_writing_files': False,
            'l2_leaf_reg': 3,
            'bootstrap_type': 'Bayesian',
            'random_seed': 42,
            'verbose': False,
        }

        cv_scores = []
        for fold, (train_idx, val_idx) in enumerate(self._temporal_splits(X, y, cv_folds)):
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

        # Calibration also uses complete, chronologically separated game dates.
        ts_cv = self._temporal_splits(X, y, 3)
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
        
        logger.info("CatBoost trained: CV accuracy=%.3f, CV AUC=%.3f, in-sample accuracy=%.3f", mean_cv_acc, mean_cv_auc, accuracy)
        
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
        logger.info("Calculating ensemble weights")
        
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
        
        logger.info("Ensemble weights calculated:")
        logger.info(f"  XGBoost: {weights['xgb']:.3f} (CV acc: {xgb_avg_acc:.3f})")
        logger.info(f"  LightGBM: {weights['lgb']:.3f} (CV acc: {lgb_avg_acc:.3f})")
        logger.info(f"  CatBoost: {weights['cat']:.3f} (CV acc: {cat_avg_acc:.3f})")
        
        return weights
    
    def predict_ensemble(self, X: pd.DataFrame) -> np.ndarray:
        """Return weighted home-win probabilities from the calibrated ensemble."""
        if self.xgb_calibrated is None or self.lgb_calibrated is None or self.cat_calibrated is None:
            raise ValueError("Models not trained. Call train_all() first.")
        
        # Get predictions from each model
        xgb_pred = self.xgb_calibrated.predict_proba(X)[:, 1]
        lgb_pred = self.lgb_calibrated.predict_proba(X)[:, 1]
        cat_pred = self.cat_calibrated.predict_proba(X)[:, 1]
        
        # Renormalize defensively in case metadata was written with rounded weights.
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
            'evaluation_scope': 'in_sample_training_diagnostic',
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
        logger.info(f"Training-set ensemble: Accuracy={ensemble_accuracy:.3f}, AUC={ensemble_auc:.3f}")
        logger.info("Training-set ensemble metrics are not held-out performance or a CV comparison.")
        logger.info("=" * 80)
        
        return self.metrics
    
    def save_models(self):
        """Save all models to disk."""
        logger.info("Saving models")
        
        if self.feature_names is None or any(model is None for model in (
                self.xgb_calibrated, self.lgb_calibrated, self.cat_calibrated)):
            raise ValueError("Cannot save an incomplete ensemble")

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
            'training_data': self.training_data,
            'parameters': {'n_estimators': self.n_estimators, 'threads': self.threads},
            'metric_scope': {
                'base_accuracy_auc': 'uncalibrated_time_series_cross_validation',
                'base_logloss_brier': 'in_sample_calibrated_diagnostic',
                'ensemble': 'in_sample_training_diagnostic',
            },
        }
        
        with open(self.output_dir / "ensemble_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info("Models saved to %s", self.output_dir)
    
    async def load_models_async(self):
        """Async version of model loading."""
        import asyncio
        logger.info("Loading models asynchronously")
        
        xgb_path = self.output_dir / "xgb_model.pkl"
        lgb_path = self.output_dir / "lgb_model.pkl"
        cat_path = self.output_dir / "cat_model.pkl"
        metadata_path = self.output_dir / "ensemble_metadata.json"
        for path in (xgb_path, lgb_path, cat_path, metadata_path):
            if not path.is_file():
                raise FileNotFoundError(f"Missing ensemble artifact: {path}")

        def read_pickle(path):
            with open(path, 'rb') as f:
                return pickle.load(f)
        
        def read_json(path):
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
        
        logger.info("Models loaded asynchronously")

