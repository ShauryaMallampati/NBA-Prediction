#!/usr/bin/env python3
"""
🏀 4+ DIFFERENT MODELING APPROACHES
Compare multiple strategies to find the best one

Approach 1: Hyperparameter Tuned XGBoost
Approach 2: Ensemble (Voting Classifier)
Approach 3: LightGBM (Faster XGBoost alternative)
Approach 4: Stacked Ensemble (Meta-learner)
Approach 5: CatBoost (Categorical Boosting)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import VotingClassifier, RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import xgboost as xgb
import logging
import json
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class MultiApproachTester:
    """Test 4+ different modeling approaches"""
    
    def __init__(self):
        self.df = None
        self.results = {}
        self.best_model_info = None
    
    def load_data(self):
        """Load pre-game features only"""
        logger.info("\n" + "="*100)
        logger.info("📂 LOADING DATA")
        logger.info("="*100)
        
        features_path = Path(__file__).parent.parent / "data" / "processed" / "engineered_features.csv"
        self.df = pd.read_csv(features_path, low_memory=False)
        
        logger.info(f"✅ Loaded {len(self.df):,} games")
        return self
    
    def prepare_data(self):
        """Prepare pre-game features only"""
        # Pre-game features
        allowed_features = {
            'home_elo', 'away_elo', 'elo_win_prob',
            'home_last_5_wins', 'home_last_5_win_pct', 'home_last_10_wins', 'home_last_10_win_pct',
            'away_last_5_wins', 'away_last_5_win_pct', 'away_last_10_wins', 'away_last_10_win_pct',
            'h2h_home_wins', 'h2h_away_wins',
            'home_rest_days', 'away_rest_days', 'home_back_to_back', 'away_back_to_back',
            'home_home_win_pct', 'away_away_win_pct', 'elo_diff'
        }
        
        feature_cols = [col for col in self.df.columns if col in allowed_features]
        
        X = self.df[feature_cols].fillna(0)
        y = self.df['home_win'].astype(int)
        
        logger.info(f"✅ Features: {len(feature_cols)}")
        logger.info(f"✅ Samples: {len(X):,}")
        
        return X, y
    
    def approach_1_tuned_xgboost(self, X, y):
        """Approach 1: Hyperparameter-tuned XGBoost"""
        logger.info("\n" + "="*100)
        logger.info("🚀 APPROACH 1: HYPERPARAMETER-TUNED XGBOOST")
        logger.info("="*100)
        
        tscv = TimeSeriesSplit(n_splits=5)
        fold_scores = []
        
        # Grid search parameters
        param_grid = {
            'max_depth': [4, 5, 6],
            'learning_rate': [0.01, 0.05, 0.1],
            'n_estimators': [100, 200, 300],
        }
        
        best_params = None
        best_score = 0
        
        logger.info("\n🔍 Hyperparameter tuning...")
        
        for depth in param_grid['max_depth'][:2]:  # Test subset for speed
            for lr in param_grid['learning_rate'][:2]:
                for n_est in [200]:
                    model = xgb.XGBClassifier(
                        max_depth=depth,
                        learning_rate=lr,
                        n_estimators=n_est,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        random_state=42,
                        verbosity=0,
                    )
                    
                    cv_scores = []
                    for train_idx, test_idx in tscv.split(X):
                        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
                        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
                        
                        scaler = StandardScaler()
                        X_train_scaled = scaler.fit_transform(X_train)
                        X_test_scaled = scaler.transform(X_test)
                        
                        model.fit(X_train_scaled, y_train, verbose=0)
                        y_pred = model.predict(X_test_scaled)
                        
                        cv_scores.append(accuracy_score(y_test, y_pred))
                    
                    avg_score = np.mean(cv_scores)
                    
                    if avg_score > best_score:
                        best_score = avg_score
                        best_params = {'max_depth': depth, 'learning_rate': lr, 'n_estimators': n_est}
        
        logger.info(f"   Best params: {best_params}")
        logger.info(f"   Best CV accuracy: {best_score:.4f}")
        
        # Train final model
        best_model = xgb.XGBClassifier(**best_params, subsample=0.8, colsample_bytree=0.8, random_state=42)
        
        final_scores = []
        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            best_model.fit(X_train_scaled, y_train, verbose=0)
            y_pred = best_model.predict(X_test_scaled)
            y_proba = best_model.predict_proba(X_test_scaled)[:, 1]
            
            acc = accuracy_score(y_test, y_pred)
            auc = roc_auc_score(y_test, y_proba)
            final_scores.append({'accuracy': acc, 'roc_auc': auc})
        
        final_df = pd.DataFrame(final_scores)
        
        approach_1_acc = final_df['accuracy'].mean()
        approach_1_auc = final_df['roc_auc'].mean()
        
        logger.info(f"\n✅ FINAL: Accuracy={approach_1_acc:.4f}, AUC={approach_1_auc:.4f}")
        
        self.results['Approach 1: Tuned XGBoost'] = {
            'accuracy': approach_1_acc,
            'roc_auc': approach_1_auc,
            'params': best_params,
        }
        
        return approach_1_acc
    
    def approach_2_voting_ensemble(self, X, y):
        """Approach 2: Voting Classifier Ensemble"""
        logger.info("\n" + "="*100)
        logger.info("🚀 APPROACH 2: VOTING ENSEMBLE (XGBoost + RF + GB)")
        logger.info("="*100)
        
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Create ensemble
        xgb_clf = xgb.XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42)
        rf_clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        gb_clf = GradientBoostingClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
        
        voting_clf = VotingClassifier(
            estimators=[('xgb', xgb_clf), ('rf', rf_clf), ('gb', gb_clf)],
            voting='soft'
        )
        
        logger.info("   Ensemble: XGBoost + Random Forest + Gradient Boosting")
        
        fold_scores = []
        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            voting_clf.fit(X_train_scaled, y_train)
            y_pred = voting_clf.predict(X_test_scaled)
            y_proba = voting_clf.predict_proba(X_test_scaled)[:, 1]
            
            acc = accuracy_score(y_test, y_pred)
            auc = roc_auc_score(y_test, y_proba)
            fold_scores.append({'accuracy': acc, 'roc_auc': auc})
        
        fold_df = pd.DataFrame(fold_scores)
        
        approach_2_acc = fold_df['accuracy'].mean()
        approach_2_auc = fold_df['roc_auc'].mean()
        
        logger.info(f"✅ FINAL: Accuracy={approach_2_acc:.4f}, AUC={approach_2_auc:.4f}")
        
        self.results['Approach 2: Voting Ensemble'] = {
            'accuracy': approach_2_acc,
            'roc_auc': approach_2_auc,
            'components': ['XGBoost', 'Random Forest', 'Gradient Boosting'],
        }
        
        return approach_2_acc
    
    def approach_3_lightgbm(self, X, y):
        """Approach 3: LightGBM (faster alternative)"""
        logger.info("\n" + "="*100)
        logger.info("🚀 APPROACH 3: LightGBM (Fast Gradient Boosting)")
        logger.info("="*100)
        
        try:
            import lightgbm as lgb
        except ImportError:
            logger.warning("   ⚠️  LightGBM not installed, skipping...")
            self.results['Approach 3: LightGBM'] = {'accuracy': 0, 'roc_auc': 0, 'status': 'skipped'}
            return 0
        
        tscv = TimeSeriesSplit(n_splits=5)
        
        lgb_clf = lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.05,
            num_leaves=31,
            random_state=42,
            verbosity=-1,
        )
        
        fold_scores = []
        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            lgb_clf.fit(X_train_scaled, y_train)
            y_pred = lgb_clf.predict(X_test_scaled)
            y_proba = lgb_clf.predict_proba(X_test_scaled)[:, 1]
            
            acc = accuracy_score(y_test, y_pred)
            auc = roc_auc_score(y_test, y_proba)
            fold_scores.append({'accuracy': acc, 'roc_auc': auc})
        
        fold_df = pd.DataFrame(fold_scores)
        
        approach_3_acc = fold_df['accuracy'].mean()
        approach_3_auc = fold_df['roc_auc'].mean()
        
        logger.info(f"✅ FINAL: Accuracy={approach_3_acc:.4f}, AUC={approach_3_auc:.4f}")
        
        self.results['Approach 3: LightGBM'] = {
            'accuracy': approach_3_acc,
            'roc_auc': approach_3_auc,
            'advantage': 'Faster training, handles categorical features',
        }
        
        return approach_3_acc
    
    def approach_4_stacked_ensemble(self, X, y):
        """Approach 4: Stacked Ensemble with Meta-learner"""
        logger.info("\n" + "="*100)
        logger.info("🚀 APPROACH 4: STACKED ENSEMBLE (Meta-learner)")
        logger.info("="*100)
        
        from sklearn.model_selection import cross_val_predict
        
        tscv = TimeSeriesSplit(n_splits=5)
        
        # Base learners
        base_learners = [
            ('xgb', xgb.XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42)),
            ('rf', RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)),
            ('gb', GradientBoostingClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)),
        ]
        
        # Meta-learner
        meta_learner = LogisticRegression(random_state=42, max_iter=1000)
        
        logger.info("   Base learners: XGBoost, Random Forest, Gradient Boosting")
        logger.info("   Meta-learner: Logistic Regression")
        
        fold_scores = []
        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Generate meta-features
            meta_train = np.zeros((X_train_scaled.shape[0], len(base_learners)))
            meta_test = np.zeros((X_test_scaled.shape[0], len(base_learners)))
            
            for i, (name, estimator) in enumerate(base_learners):
                estimator.fit(X_train_scaled, y_train)
                meta_train[:, i] = estimator.predict_proba(X_train_scaled)[:, 1]
                meta_test[:, i] = estimator.predict_proba(X_test_scaled)[:, 1]
            
            # Train meta-learner
            meta_learner.fit(meta_train, y_train)
            y_pred = meta_learner.predict(meta_test)
            y_proba = meta_learner.predict_proba(meta_test)[:, 1]
            
            acc = accuracy_score(y_test, y_pred)
            auc = roc_auc_score(y_test, y_proba)
            fold_scores.append({'accuracy': acc, 'roc_auc': auc})
        
        fold_df = pd.DataFrame(fold_scores)
        
        approach_4_acc = fold_df['accuracy'].mean()
        approach_4_auc = fold_df['roc_auc'].mean()
        
        logger.info(f"✅ FINAL: Accuracy={approach_4_acc:.4f}, AUC={approach_4_auc:.4f}")
        
        self.results['Approach 4: Stacked Ensemble'] = {
            'accuracy': approach_4_acc,
            'roc_auc': approach_4_auc,
            'advantage': 'Leverages base learner strengths',
        }
        
        return approach_4_acc
    
    def approach_5_catboost(self, X, y):
        """Approach 5: CatBoost (Categorical Boosting)"""
        logger.info("\n" + "="*100)
        logger.info("🚀 APPROACH 5: CATBOOST")
        logger.info("="*100)
        
        try:
            from catboost import CatBoostClassifier
        except ImportError:
            logger.warning("   ⚠️  CatBoost not installed, skipping...")
            self.results['Approach 5: CatBoost'] = {'accuracy': 0, 'roc_auc': 0, 'status': 'skipped'}
            return 0
        
        tscv = TimeSeriesSplit(n_splits=5)
        
        cb_clf = CatBoostClassifier(
            iterations=200,
            max_depth=5,
            learning_rate=0.05,
            random_state=42,
            verbose=0,
        )
        
        fold_scores = []
        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            cb_clf.fit(X_train_scaled, y_train)
            y_pred = cb_clf.predict(X_test_scaled)
            y_proba = cb_clf.predict_proba(X_test_scaled)[:, 1]
            
            acc = accuracy_score(y_test, y_pred)
            auc = roc_auc_score(y_test, y_proba)
            fold_scores.append({'accuracy': acc, 'roc_auc': auc})
        
        fold_df = pd.DataFrame(fold_scores)
        
        approach_5_acc = fold_df['accuracy'].mean()
        approach_5_auc = fold_df['roc_auc'].mean()
        
        logger.info(f"✅ FINAL: Accuracy={approach_5_acc:.4f}, AUC={approach_5_auc:.4f}")
        
        self.results['Approach 5: CatBoost'] = {
            'accuracy': approach_5_acc,
            'roc_auc': approach_5_auc,
            'advantage': 'Handles categorical data natively',
        }
        
        return approach_5_acc
    
    def compare_and_rank(self):
        """Compare all approaches and rank them"""
        logger.info("\n" + "="*100)
        logger.info("📊 RESULTS COMPARISON")
        logger.info("="*100)
        
        # Sort by accuracy
        sorted_results = sorted(self.results.items(), key=lambda x: x[1].get('accuracy', 0), reverse=True)
        
        logger.info(f"\n🏆 RANKING (Best to Worst):\n")
        
        for rank, (approach, metrics) in enumerate(sorted_results, 1):
            acc = metrics.get('accuracy', 0)
            auc = metrics.get('roc_auc', 0)
            improvement = (acc - 0.6132) * 100  # vs baseline
            
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
            
            logger.info(f"{medal} {rank}. {approach}")
            logger.info(f"   Accuracy: {acc:.4f}")
            logger.info(f"   ROC-AUC:  {auc:.4f}")
            logger.info(f"   vs Baseline: {improvement:+.2f}%\n")
        
        # Determine best
        best_approach = sorted_results[0]
        self.best_model_info = best_approach
        
        logger.info("="*100)
        logger.info(f"\n✅ BEST APPROACH: {best_approach[0]}")
        logger.info(f"   Accuracy: {best_approach[1]['accuracy']:.4f}")
        logger.info(f"   ROC-AUC:  {best_approach[1]['roc_auc']:.4f}")
        logger.info("="*100)
    
    def save_results(self):
        """Save results to JSON"""
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'approaches_tested': len(self.results),
            'best_approach': self.best_model_info[0] if self.best_model_info else None,
            'best_accuracy': self.best_model_info[1]['accuracy'] if self.best_model_info else 0,
            'all_results': {name: {k: float(v) if isinstance(v, (int, np.integer, float)) else v 
                                   for k, v in metrics.items()} 
                           for name, metrics in self.results.items()},
            'baseline': 0.6132,
            'benchmark': {'Vegas': 0.54, 'FiveThirtyEight': 0.65},
        }
        
        output_path = Path(__file__).parent.parent / "artifacts" / "approach_comparison.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"\n💾 Results saved to {output_path}")
    
    def run(self):
        """Execute all approaches"""
        logger.info("\n" + "="*100)
        logger.info("🏀 MULTI-APPROACH COMPARISON")
        logger.info("="*100)
        
        try:
            self.load_data()
            X, y = self.prepare_data()
            
            start_time = time.time()
            
            self.approach_1_tuned_xgboost(X, y)
            self.approach_2_voting_ensemble(X, y)
            self.approach_3_lightgbm(X, y)
            self.approach_4_stacked_ensemble(X, y)
            self.approach_5_catboost(X, y)
            
            elapsed = time.time() - start_time
            
            self.compare_and_rank()
            self.save_results()
            
            logger.info(f"\n⏱️  Total time: {elapsed:.1f} seconds")
            logger.info(f"✅ All approaches tested successfully!")
            
        except Exception as e:
            logger.error(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    tester = MultiApproachTester()
    tester.run()
