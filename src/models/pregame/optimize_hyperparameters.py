"""Find the best hyperparameters for our models using Optuna.

We optimize:
- XGBoost settings
- LightGBM parameters
- CatBoost configuration

We use time-series cross-validation to make sure we're not overfitting.
"""

import pandas as pd
import numpy as np
import json
import optuna
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
import xgboost as xgb
import lightgbm as lgb
import catboost as cb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HyperparameterOptimizer:
    """Use Optuna to find the best hyperparameters for each model."""
    
    def __init__(self, output_dir: str = "artifacts/models/pregame"):
        """Set up the optimizer."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Best parameters
        self.best_xgb_params = None
        self.best_lgb_params = None
        self.best_cat_params = None
        
        logger.info("🔧 Hyperparameter optimizer initialized")
    
    def optimize_xgboost(self, X: pd.DataFrame, y: pd.Series, n_trials: int = 50) -> Dict:
        """Find the best XGBoost settings.
        
        Args:
            X: Training features
            y: Target labels
            n_trials: How many combinations to try
        
        Returns:
            Best hyperparameters we found
        """
        logger.info("🔧 Optimizing XGBoost hyperparameters...")
        
        def objective(trial):
            # Suggest hyperparameters
            params = {
                'objective': 'binary:logistic',
                'eval_metric': 'logloss',
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                'gamma': trial.suggest_float('gamma', 0, 0.5),
                'lambda': trial.suggest_float('lambda', 0.1, 10.0, log=True),
                'alpha': trial.suggest_float('alpha', 0.1, 10.0, log=True),
                'random_state': 42,
                'n_estimators': 300,
            }
            
            # Time-series cross-validation
            tscv = TimeSeriesSplit(n_splits=5)
            scores = []
            
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                # Train model
                model = xgb.XGBClassifier(**params)
                model.fit(
                    X_train, y_train,
                    eval_set=[(X_val, y_val)],
                    early_stopping_rounds=20,
                    verbose=False
                )
                
                # Predict
                y_pred = model.predict_proba(X_val)[:, 1]
                auc = roc_auc_score(y_val, y_pred)
                scores.append(auc)
            
            # Return mean AUC
            return np.mean(scores)
        
        # Create study
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        # Get best parameters
        best_params = study.best_params
        best_params['objective'] = 'binary:logistic'
        best_params['eval_metric'] = 'logloss'
        best_params['random_state'] = 42
        best_params['n_estimators'] = 300
        
        self.best_xgb_params = best_params
        
        logger.info(f"✅ XGBoost optimization complete: Best AUC={study.best_value:.3f}")
        logger.info(f"   Best parameters: {best_params}")
        
        return best_params
    
    def optimize_lightgbm(self, X: pd.DataFrame, y: pd.Series, n_trials: int = 50) -> Dict:
        """
        Optimize LightGBM hyperparameters.
        
        Args:
            X: Features
            y: Target
            n_trials: Number of Optuna trials
        
        Returns:
            Best hyperparameters
        """
        logger.info("🔧 Optimizing LightGBM hyperparameters...")
        
        def objective(trial):
            # Suggest hyperparameters
            params = {
                'objective': 'binary',
                'metric': 'binary_logloss',
                'boosting_type': 'gbdt',
                'num_leaves': trial.suggest_int('num_leaves', 10, 50),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
                'feature_fraction': trial.suggest_float('feature_fraction', 0.6, 1.0),
                'bagging_fraction': trial.suggest_float('bagging_fraction', 0.6, 1.0),
                'bagging_freq': trial.suggest_int('bagging_freq', 1, 10),
                'min_child_samples': trial.suggest_int('min_child_samples', 10, 50),
                'lambda_l1': trial.suggest_float('lambda_l1', 0.1, 10.0, log=True),
                'lambda_l2': trial.suggest_float('lambda_l2', 0.1, 10.0, log=True),
                'random_state': 42,
                'n_estimators': 300,
                'verbose': -1,
            }
            
            # Time-series cross-validation
            tscv = TimeSeriesSplit(n_splits=5)
            scores = []
            
            for train_idx, val_idx in tscv.split(X):
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
                auc = roc_auc_score(y_val, y_pred)
                scores.append(auc)
            
            # Return mean AUC
            return np.mean(scores)
        
        # Create study
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        # Get best parameters
        best_params = study.best_params
        best_params['objective'] = 'binary'
        best_params['metric'] = 'binary_logloss'
        best_params['boosting_type'] = 'gbdt'
        best_params['random_state'] = 42
        best_params['n_estimators'] = 300
        best_params['verbose'] = -1
        
        self.best_lgb_params = best_params
        
        logger.info(f"✅ LightGBM optimization complete: Best AUC={study.best_value:.3f}")
        logger.info(f"   Best parameters: {best_params}")
        
        return best_params
    
    def optimize_catboost(self, X: pd.DataFrame, y: pd.Series, n_trials: int = 50) -> Dict:
        """
        Optimize CatBoost hyperparameters.
        
        Args:
            X: Features
            y: Target
            n_trials: Number of Optuna trials
        
        Returns:
            Best hyperparameters
        """
        logger.info("🔧 Optimizing CatBoost hyperparameters...")
        
        def objective(trial):
            # Suggest hyperparameters
            params = {
                'objective': 'Logloss',
                'eval_metric': 'Logloss',
                'depth': trial.suggest_int('depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
                'iterations': 300,
                'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1, 10, log=True),
                'bootstrap_type': trial.suggest_categorical('bootstrap_type', ['Bayesian', 'Bernoulli', 'MVS']),
                'random_seed': 42,
                'verbose': False,
            }
            
            # Time-series cross-validation
            tscv = TimeSeriesSplit(n_splits=5)
            scores = []
            
            for train_idx, val_idx in tscv.split(X):
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
                auc = roc_auc_score(y_val, y_pred)
                scores.append(auc)
            
            # Return mean AUC
            return np.mean(scores)
        
        # Create study
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
        
        # Get best parameters
        best_params = study.best_params
        best_params['objective'] = 'Logloss'
        best_params['eval_metric'] = 'Logloss'
        best_params['iterations'] = 300
        best_params['random_seed'] = 42
        best_params['verbose'] = False
        
        self.best_cat_params = best_params
        
        logger.info(f"✅ CatBoost optimization complete: Best AUC={study.best_value:.3f}")
        logger.info(f"   Best parameters: {best_params}")
        
        return best_params
    
    def optimize_all(self, X: pd.DataFrame, y: pd.Series, n_trials: int = 50) -> Dict:
        """
        Optimize all models.
        
        Args:
            X: Features
            y: Target
            n_trials: Number of Optuna trials per model
        
        Returns:
            Dictionary with best parameters for all models
        """
        logger.info("=" * 80)
        logger.info("HYPERPARAMETER OPTIMIZATION")
        logger.info("=" * 80)
        
        # Optimize all models
        xgb_params = self.optimize_xgboost(X, y, n_trials)
        lgb_params = self.optimize_lightgbm(X, y, n_trials)
        cat_params = self.optimize_catboost(X, y, n_trials)
        
        # Save best parameters
        best_params = {
            'xgb': xgb_params,
            'lgb': lgb_params,
            'cat': cat_params,
        }
        
        output_path = self.output_dir / "best_hyperparameters.json"
        with open(output_path, 'w') as f:
            json.dump(best_params, f, indent=2)
        
        logger.info(f"✅ Saved best parameters to {output_path}")
        
        return best_params


def main():
    """Main optimization function."""
    import sys
    from pathlib import Path
    
    # Get features path
    if len(sys.argv) > 1:
        features_path = sys.argv[1]
    else:
        features_path = "artifacts/features/pregame.parquet"
    
    # Load data
    logger.info(f"📊 Loading data from {features_path}")
    features_path = Path(features_path)
    
    if features_path.suffix == '.parquet':
        df = pd.read_parquet(features_path)
    else:
        df = pd.read_csv(features_path)
    
    # Extract features and target
    exclude_cols = ['game_id', 'date', 'home', 'away', 'home_pts', 'away_pts',
                   'season', 'year', 'month', 'day_of_week']
    
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    X = df[feature_cols].fillna(0)
    
    if 'home_pts' in df.columns and 'away_pts' in df.columns:
        y = (df['home_pts'] > df['away_pts']).astype(int)
    elif 'home_win' in df.columns:
        y = df['home_win'].astype(int)
    else:
        raise ValueError("Target column not found")
    
    logger.info(f"✅ Loaded {len(feature_cols)} features for {len(X)} games")
    
    # Optimize
    optimizer = HyperparameterOptimizer()
    best_params = optimizer.optimize_all(X, y, n_trials=50)
    
    logger.info("\n✅ Hyperparameter optimization complete!")
    logger.info(f"   Best parameters saved to artifacts/models/pregame/best_hyperparameters.json")
    
    return best_params


if __name__ == "__main__":
    best_params = main()

