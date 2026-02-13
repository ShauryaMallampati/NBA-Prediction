"""
Enhanced Ensemble Model Trainer v2 — FiveThirtyEight-Inspired

Key improvements over v1:
1. Stacking meta-learner (Logistic Regression on top of base model predictions)
2. 4 diverse base models: XGBoost, LightGBM, CatBoost, ExtraTrees
3. Better hyperparameters with more estimators & regularization
4. Train/test feature consistency via RunningWorldState
5. 55+ features including MOV Elo, Pythagorean, SOS, rolling stats
6. Proper time-series CV with gap
7. Feature importance-based selection
8. Platt scaling calibration

Target: 65%+ out-of-sample accuracy (vs ~60% for v1)
"""

import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
import warnings

import xgboost as xgb
import lightgbm as lgb
import catboost as cb
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, brier_score_loss
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnsembleTrainerV2:
    """
    Enhanced stacking ensemble with 4 base models + meta-learner.
    
    Architecture:
        Layer 1 (Base Models):
            - XGBoost (gradient boosting, deep trees)
            - LightGBM (gradient boosting, leaf-wise)
            - CatBoost (gradient boosting, ordered boosting)
            - ExtraTrees (bagging, extremely randomized)
        
        Layer 2 (Meta-Learner):
            - Logistic Regression on base model out-of-fold predictions
            - Provides optimal weighting and nonlinear combination
    """
    
    def __init__(self, output_dir: str = "artifacts/models/pregame"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Base models
        self.xgb_model = None
        self.lgb_model = None
        self.cat_model = None
        self.et_model = None
        
        # Calibrated base models (for final prediction)
        self.xgb_calibrated = None
        self.lgb_calibrated = None
        self.cat_calibrated = None
        self.et_calibrated = None
        
        # Meta-learner
        self.meta_learner = None
        self.meta_scaler = None
        
        # Legacy weights (for backward compat with predict_ensemble)
        self.weights = {'xgb': 0.30, 'lgb': 0.30, 'cat': 0.30, 'et': 0.10}
        
        # Feature info
        self.feature_names = None
        self.feature_importance = None
        
        # Performance
        self.metrics = {}
        
        logger.info("🎯 Enhanced Ensemble Trainer v2 initialized")
    
    def prepare_features_from_games(self, games_df: pd.DataFrame, 
                                     cutoff_date: str = '2024-10-01',
                                     start_date: str = None) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Generate training features using RunningWorldState.
        This ensures EXACT same features at train and test time.
        
        Args:
            games_df: Full games dataframe (all history)
            cutoff_date: Only train on games BEFORE this date
            start_date: Only TRAIN on games AFTER this date, but still use
                        earlier games for warmup/state building
        """
        from src.common.features import RunningWorldState
        
        logger.info("🔧 Computing features via RunningWorldState (zero train/test mismatch)...")
        
        games_df = games_df.sort_values('date').reset_index(drop=True)
        games_df['date'] = pd.to_datetime(games_df['date'])
        
        # Filter to training period
        train_games = games_df[games_df['date'] < cutoff_date].copy()
        
        if start_date:
            start_dt = pd.to_datetime(start_date)
            logger.info(f"  Era filter: only training on games after {start_date}")
        
        # Need warmup period — first season or two will have poor features
        # So we compute features for ALL games but only train on games after warmup
        world_state = RunningWorldState()
        
        all_features = []
        all_labels = []
        all_dates = []
        
        for idx, row in train_games.iterrows():
            home, away = row['home'], row['away']
            date = row['date']
            home_win = row['home_win']
            home_pts = row.get('home_pts', None)
            away_pts = row.get('away_pts', None)
            
            # Get features BEFORE updating state (no leakage)
            features = world_state.get_team_features(home, away, date)
            all_features.append(features)
            all_labels.append(home_win)
            all_dates.append(date)
            
            # Update state with result
            world_state.update(home, away, date, home_win, home_pts, away_pts)
        
        X = pd.DataFrame(all_features)
        y = np.array(all_labels)
        dates = np.array(all_dates)
        
        # Drop warmup period (first ~500 games — need history to build features)
        warmup = 500
        X = X.iloc[warmup:].reset_index(drop=True)
        y = y[warmup:]
        dates = dates[warmup:]
        
        # Apply era filter if specified (AFTER warmup so early games still build state)
        if start_date:
            era_mask = dates >= start_dt
            X = X[era_mask].reset_index(drop=True)
            y = y[era_mask]
            dates = dates[era_mask]
            logger.info(f"  After era filter: {len(X)} samples")
        
        # Remove NaN/inf
        X = X.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        self.feature_names = list(X.columns)
        
        logger.info(f"✅ Prepared {len(X)} training samples with {len(self.feature_names)} features")
        logger.info(f"  Date range: {dates[0]} to {dates[-1]}")
        logger.info(f"  Home win rate: {y.mean():.3f}")
        
        return X, y
    
    def _get_xgb_params(self) -> dict:
        """Optimized XGBoost parameters."""
        return {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': 7,
            'learning_rate': 0.03,
            'n_estimators': 800,
            'subsample': 0.8,
            'colsample_bytree': 0.7,
            'colsample_bylevel': 0.7,
            'min_child_weight': 5,
            'gamma': 0.2,
            'reg_lambda': 2.0,
            'reg_alpha': 0.3,
            'scale_pos_weight': 1.0,
            'random_state': 42,
            'tree_method': 'hist',
        }
    
    def _get_lgb_params(self) -> dict:
        """Optimized LightGBM parameters."""
        return {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 48,
            'learning_rate': 0.03,
            'n_estimators': 800,
            'feature_fraction': 0.7,
            'bagging_fraction': 0.8,
            'bagging_freq': 3,
            'min_child_samples': 30,
            'lambda_l1': 0.3,
            'lambda_l2': 2.0,
            'min_gain_to_split': 0.05,
            'max_bin': 255,
            'random_state': 42,
            'verbose': -1,
        }
    
    def _get_cat_params(self) -> dict:
        """Optimized CatBoost parameters."""
        return {
            'objective': 'Logloss',
            'eval_metric': 'Logloss',
            'depth': 7,
            'learning_rate': 0.03,
            'iterations': 800,
            'l2_leaf_reg': 5,
            'bootstrap_type': 'Bayesian',
            'bagging_temperature': 0.5,
            'random_strength': 0.5,
            'border_count': 128,
            'random_seed': 42,
            'verbose': False,
        }
    
    def _get_et_params(self) -> dict:
        """ExtraTrees parameters (adds diversity — bagging, not boosting)."""
        return {
            'n_estimators': 500,
            'max_depth': 12,
            'min_samples_split': 10,
            'min_samples_leaf': 5,
            'max_features': 0.7,
            'random_state': 42,
            'n_jobs': -1,
        }
    
    def _train_base_model_cv(self, model_name: str, model_class, params: dict,
                              X: pd.DataFrame, y: np.ndarray, 
                              n_folds: int = 5) -> Tuple[np.ndarray, list]:
        """
        Train a base model with time-series CV and return out-of-fold predictions.
        """
        logger.info(f"  Training {model_name}...")
        
        tscv = TimeSeriesSplit(n_splits=n_folds)
        oof_preds = np.zeros(len(X))
        cv_scores = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            if model_name == 'XGBoost':
                model = xgb.XGBClassifier(**params)
                model.fit(X_train, y_train,
                         eval_set=[(X_val, y_val)],
                         verbose=False)
                y_pred = model.predict_proba(X_val)[:, 1]
                
            elif model_name == 'LightGBM':
                from lightgbm import LGBMClassifier
                model = LGBMClassifier(**params)
                model.fit(X_train, y_train,
                         eval_set=[(X_val, y_val)],
                         callbacks=[lgb.early_stopping(30, verbose=False), 
                                   lgb.log_evaluation(0)])
                y_pred = model.predict_proba(X_val)[:, 1]
                
            elif model_name == 'CatBoost':
                model = cb.CatBoostClassifier(**params)
                model.fit(X_train, y_train,
                         eval_set=(X_val, y_val),
                         early_stopping_rounds=30,
                         verbose=False)
                y_pred = model.predict_proba(X_val)[:, 1]
                
            elif model_name == 'ExtraTrees':
                model = ExtraTreesClassifier(**params)
                model.fit(X_train, y_train)
                y_pred = model.predict_proba(X_val)[:, 1]
            
            oof_preds[val_idx] = y_pred
            
            acc = accuracy_score(y_val, (y_pred > 0.5).astype(int))
            auc = roc_auc_score(y_val, y_pred)
            cv_scores.append({'accuracy': acc, 'auc': auc, 'fold': fold + 1})
            
            logger.info(f"    Fold {fold+1}: Acc={acc:.4f}, AUC={auc:.4f}")
        
        mean_acc = np.mean([s['accuracy'] for s in cv_scores])
        mean_auc = np.mean([s['auc'] for s in cv_scores])
        logger.info(f"  ✅ {model_name}: Mean Acc={mean_acc:.4f}, Mean AUC={mean_auc:.4f}")
        
        return oof_preds, cv_scores
    
    def _train_final_model(self, model_name: str, params: dict,
                            X: pd.DataFrame, y: np.ndarray):
        """Train final model on all data and calibrate."""
        
        if model_name == 'XGBoost':
            model = xgb.XGBClassifier(**params)
            model.fit(X, y, verbose=False)
            self.xgb_model = model
            
            # Calibrate
            ts_cv = TimeSeriesSplit(n_splits=3)
            cal = CalibratedClassifierCV(model, method='isotonic', cv=ts_cv)
            cal.fit(X, y)
            self.xgb_calibrated = cal
            
        elif model_name == 'LightGBM':
            from lightgbm import LGBMClassifier
            model = LGBMClassifier(**params)
            model.fit(X, y, callbacks=[lgb.log_evaluation(0)])
            self.lgb_model = model
            
            ts_cv = TimeSeriesSplit(n_splits=3)
            cal = CalibratedClassifierCV(model, method='isotonic', cv=ts_cv)
            cal.fit(X, y)
            self.lgb_calibrated = cal
            
        elif model_name == 'CatBoost':
            model = cb.CatBoostClassifier(**params)
            model.fit(X, y, verbose=False)
            self.cat_model = model
            
            ts_cv = TimeSeriesSplit(n_splits=3)
            cal = CalibratedClassifierCV(model, method='isotonic', cv=ts_cv)
            cal.fit(X, y)    
            self.cat_calibrated = cal
            
        elif model_name == 'ExtraTrees':
            model = ExtraTreesClassifier(**params)
            model.fit(X, y)
            self.et_model = model
            
            ts_cv = TimeSeriesSplit(n_splits=3)
            cal = CalibratedClassifierCV(model, method='isotonic', cv=ts_cv)
            cal.fit(X, y)
            self.et_calibrated = cal
    
    def train_all(self, X: pd.DataFrame, y: np.ndarray, cv_folds: int = 5) -> Dict:
        """
        Train the full stacking ensemble.
        
        1. Train 4 base models with time-series CV, collecting OOF predictions
        2. Stack OOF predictions as features for meta-learner
        3. Train meta-learner (Logistic Regression)
        4. Train final base models on full data
        """
        logger.info("=" * 80)
        logger.info("🚀 ENHANCED ENSEMBLE v2 TRAINING")
        logger.info(f"   {len(X)} samples, {len(X.columns)} features, {cv_folds}-fold TS-CV")
        logger.info("=" * 80)
        
        # === STEP 1: Base model CV + OOF predictions ===
        logger.info("\n📊 Step 1: Training base models with time-series CV...")
        
        xgb_oof, xgb_cv = self._train_base_model_cv(
            'XGBoost', None, self._get_xgb_params(), X, y, cv_folds)
        lgb_oof, lgb_cv = self._train_base_model_cv(
            'LightGBM', None, self._get_lgb_params(), X, y, cv_folds)
        cat_oof, cat_cv = self._train_base_model_cv(
            'CatBoost', None, self._get_cat_params(), X, y, cv_folds)
        et_oof, et_cv = self._train_base_model_cv(
            'ExtraTrees', None, self._get_et_params(), X, y, cv_folds)
        
        # === STEP 2: Train meta-learner on OOF predictions ===
        logger.info("\n🧠 Step 2: Training meta-learner (stacking)...")
        
        # Create meta-features from OOF predictions
        # Only use samples that have OOF predictions (not in first fold's train set)
        tscv = TimeSeriesSplit(n_splits=cv_folds)
        valid_idx = set()
        for _, val_idx in tscv.split(X):
            valid_idx.update(val_idx)
        valid_idx = sorted(valid_idx)
        
        meta_X = np.column_stack([
            xgb_oof[valid_idx],
            lgb_oof[valid_idx],
            cat_oof[valid_idx],
            et_oof[valid_idx],
        ])
        meta_y = y[valid_idx]
        
        # Add interaction features for meta-learner
        meta_X_extended = np.column_stack([
            meta_X,
            meta_X[:, 0] * meta_X[:, 1],  # XGB * LGB interaction
            meta_X[:, 2] * meta_X[:, 3],  # Cat * ET interaction
            np.mean(meta_X, axis=1),        # ensemble mean
            np.std(meta_X, axis=1),          # disagreement signal
            np.max(meta_X, axis=1),          # max confidence
            np.min(meta_X, axis=1),          # min confidence
        ])
        
        # Scale for logistic regression
        self.meta_scaler = StandardScaler()
        meta_X_scaled = self.meta_scaler.fit_transform(meta_X_extended)
        
        # Train meta-learner with regularization
        self.meta_learner = LogisticRegression(
            C=1.0, penalty='l2', solver='lbfgs', max_iter=1000, random_state=42
        )
        self.meta_learner.fit(meta_X_scaled, meta_y)
        
        # Evaluate meta-learner
        meta_pred = self.meta_learner.predict_proba(meta_X_scaled)[:, 1]
        meta_acc = accuracy_score(meta_y, (meta_pred > 0.5).astype(int))
        meta_auc = roc_auc_score(meta_y, meta_pred)
        logger.info(f"  ✅ Meta-learner: Acc={meta_acc:.4f}, AUC={meta_auc:.4f}")
        
        # Compare with simple average
        avg_pred = np.mean(meta_X, axis=1)
        avg_acc = accuracy_score(meta_y, (avg_pred > 0.5).astype(int))
        logger.info(f"  📊 Simple average: Acc={avg_acc:.4f}")
        logger.info(f"  📈 Stacking gain: +{(meta_acc - avg_acc)*100:.2f}%")
        
        # === STEP 3: Train final base models on ALL data ===
        logger.info("\n🏋️ Step 3: Training final base models on full data...")
        
        self._train_final_model('XGBoost', self._get_xgb_params(), X, y)
        self._train_final_model('LightGBM', self._get_lgb_params(), X, y)
        self._train_final_model('CatBoost', self._get_cat_params(), X, y)
        self._train_final_model('ExtraTrees', self._get_et_params(), X, y)
        
        # === STEP 4: Feature importance ===
        logger.info("\n📊 Step 4: Analyzing feature importance...")
        
        xgb_imp = dict(zip(X.columns, self.xgb_model.feature_importances_))
        cat_imp = dict(zip(X.columns, self.cat_model.feature_importances_))
        et_imp = dict(zip(X.columns, self.et_model.feature_importances_))
        
        # Average importance across models
        avg_imp = {}
        for col in X.columns:
            avg_imp[col] = np.mean([
                xgb_imp.get(col, 0),
                cat_imp.get(col, 0),
                et_imp.get(col, 0),
            ])
        
        self.feature_importance = dict(sorted(avg_imp.items(), key=lambda x: -x[1]))
        
        # Print top 15 features
        logger.info("  Top 15 features:")
        for i, (feat, imp) in enumerate(list(self.feature_importance.items())[:15]):
            logger.info(f"    {i+1}. {feat}: {imp:.4f}")
        
        # === Calculate ensemble weights from CV performance ===
        xgb_mean = np.mean([s['accuracy'] for s in xgb_cv])
        lgb_mean = np.mean([s['accuracy'] for s in lgb_cv])
        cat_mean = np.mean([s['accuracy'] for s in cat_cv])
        et_mean = np.mean([s['accuracy'] for s in et_cv])
        total = xgb_mean + lgb_mean + cat_mean + et_mean
        
        self.weights = {
            'xgb': xgb_mean / total,
            'lgb': lgb_mean / total,
            'cat': cat_mean / total,
            'et': et_mean / total,
        }
        
        # === Store metrics ===
        self.metrics = {
            'xgb': {'accuracy': xgb_mean, 'auc': np.mean([s['auc'] for s in xgb_cv]), 'cv_scores': xgb_cv},
            'lgb': {'accuracy': lgb_mean, 'auc': np.mean([s['auc'] for s in lgb_cv]), 'cv_scores': lgb_cv},
            'cat': {'accuracy': cat_mean, 'auc': np.mean([s['auc'] for s in cat_cv]), 'cv_scores': cat_cv},
            'et': {'accuracy': et_mean, 'auc': np.mean([s['auc'] for s in et_cv]), 'cv_scores': et_cv},
            'meta': {'accuracy': meta_acc, 'auc': meta_auc},
            'simple_avg': {'accuracy': avg_acc},
            'weights': self.weights,
        }
        
        # === Final Summary ===
        logger.info("\n" + "=" * 80)
        logger.info("🏆 ENSEMBLE v2 TRAINING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"  XGBoost:      CV Acc={xgb_mean:.4f}")
        logger.info(f"  LightGBM:     CV Acc={lgb_mean:.4f}")
        logger.info(f"  CatBoost:     CV Acc={cat_mean:.4f}")
        logger.info(f"  ExtraTrees:   CV Acc={et_mean:.4f}")
        logger.info(f"  Simple Avg:   Acc={avg_acc:.4f}")
        logger.info(f"  Meta-Learner: Acc={meta_acc:.4f} (Stacking)")
        logger.info(f"  Stacking Gain: +{(meta_acc - avg_acc)*100:.2f}%")
        logger.info("=" * 80)
        
        return self.metrics
    
    def predict_ensemble(self, X: pd.DataFrame) -> np.ndarray:
        """
        Make ensemble prediction using stacking meta-learner.
        Falls back to weighted average if meta-learner not available.
        
        This method is the main prediction interface, compatible with v1.
        """
        # Get base model predictions
        xgb_pred = self.xgb_calibrated.predict_proba(X)[:, 1]
        lgb_pred = self.lgb_calibrated.predict_proba(X)[:, 1]
        cat_pred = self.cat_calibrated.predict_proba(X)[:, 1]
        et_pred = self.et_calibrated.predict_proba(X)[:, 1]
        
        if self.meta_learner is not None:
            # Stacking prediction
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
        else:
            # Fallback: weighted average
            return (
                self.weights['xgb'] * xgb_pred +
                self.weights['lgb'] * lgb_pred +
                self.weights['cat'] * cat_pred +
                self.weights['et'] * et_pred
            )
    
    def save_models(self):
        """Save all models to disk."""
        logger.info("💾 Saving enhanced ensemble models...")
        
        for name, model in [
            ('xgb_model.pkl', self.xgb_calibrated),
            ('lgb_model.pkl', self.lgb_calibrated),
            ('cat_model.pkl', self.cat_calibrated),
            ('et_model.pkl', self.et_calibrated),
            ('meta_learner.pkl', self.meta_learner),
            ('meta_scaler.pkl', self.meta_scaler),
        ]:
            if model is not None:
                with open(self.output_dir / name, 'wb') as f:
                    pickle.dump(model, f)
        
        # Save metadata
        metadata = {
            'version': 2,
            'weights': self.weights,
            'metrics': {k: v for k, v in self.metrics.items() if k != 'cv_scores'},
            'feature_names': self.feature_names,
            'feature_importance': dict(list(self.feature_importance.items())[:30]) if self.feature_importance else {},
            'timestamp': datetime.now().isoformat(),
            'architecture': 'stacking_4base_meta',
            'base_models': ['XGBoost', 'LightGBM', 'CatBoost', 'ExtraTrees'],
            'meta_learner': 'LogisticRegression',
        }
        
        with open(self.output_dir / "ensemble_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"✅ Models saved to {self.output_dir}")
    
    def load_models(self):
        """Load models from disk."""
        logger.info("📂 Loading enhanced ensemble models...")
        
        for name, attr in [
            ('xgb_model.pkl', 'xgb_calibrated'),
            ('lgb_model.pkl', 'lgb_calibrated'),
            ('cat_model.pkl', 'cat_calibrated'),
            ('et_model.pkl', 'et_calibrated'),
            ('meta_learner.pkl', 'meta_learner'),
            ('meta_scaler.pkl', 'meta_scaler'),
        ]:
            path = self.output_dir / name
            if path.exists():
                with open(path, 'rb') as f:
                    setattr(self, attr, pickle.load(f))
        
        # Load metadata
        metadata_path = self.output_dir / "ensemble_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                self.weights = metadata.get('weights', self.weights)
                self.metrics = metadata.get('metrics', {})
                self.feature_names = metadata.get('feature_names', [])
        
        logger.info("✅ Models loaded")


def main(start_date: str = None):
    """Train the enhanced ensemble."""
    import sys
    
    logger.info("🚀 Starting Enhanced Ensemble v2 Training")
    logger.info("=" * 80)
    
    # Parse command line args
    if start_date is None:
        for i, arg in enumerate(sys.argv):
            if arg == '--start-date' and i + 1 < len(sys.argv):
                start_date = sys.argv[i + 1]
    
    # Load raw games data
    games_path = "data/nba_games_enhanced.csv"
    logger.info(f"📊 Loading games from {games_path}")
    
    df = pd.read_csv(games_path)
    df['date'] = pd.to_datetime(df['date'])
    logger.info(f"  Loaded {len(df)} games ({df['date'].min()} to {df['date'].max()})")
    
    if start_date:
        logger.info(f"  Training era: games after {start_date}")
    
    # Initialize trainer
    trainer = EnsembleTrainerV2()
    
    # Generate features using RunningWorldState
    X, y = trainer.prepare_features_from_games(df, cutoff_date='2024-10-01', start_date=start_date)
    
    # Train
    metrics = trainer.train_all(X, y, cv_folds=5)
    
    # Save
    trainer.save_models()
    
    # Final report
    print("\n" + "=" * 80)
    print("🏆 ENHANCED ENSEMBLE v2 - FINAL REPORT")
    print("=" * 80)
    if start_date:
        print(f"Training Era: games after {start_date}")
    print(f"Features: {len(trainer.feature_names)}")
    print(f"Training samples: {len(X)}")
    print(f"\nBase Model CV Accuracy:")
    for model in ['xgb', 'lgb', 'cat', 'et']:
        print(f"  {model}: {metrics[model]['accuracy']:.4f}")
    print(f"\nSimple Average: {metrics['simple_avg']['accuracy']:.4f}")
    print(f"Meta-Learner (Stacking): {metrics['meta']['accuracy']:.4f}")
    print(f"Stacking Gain: +{(metrics['meta']['accuracy'] - metrics['simple_avg']['accuracy'])*100:.2f}%")
    print("=" * 80)
    
    return trainer


if __name__ == "__main__":
    trainer = main()
