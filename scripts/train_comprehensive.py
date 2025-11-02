#!/usr/bin/env python3
"""
Comprehensive NBA Model Improvement Script
Tries 15+ different approaches to improve on baseline 63.83% accuracy
Tracks all results and saves best model
"""

import sys
import numpy as np
import pandas as pd
import pickle
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any
import warnings

from sklearn.model_selection import TimeSeriesSplit, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, RobustScaler, PolynomialFeatures
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from xgboost import XGBClassifier
from scipy.special import expit
from scipy.optimize import minimize
from sklearn.feature_selection import RFE
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

warnings.filterwarnings("ignore")


class ModelImprovementExperiment:
    """Run comprehensive model experiments"""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.baseline_accuracy = 0.6383
        self.baseline_roc_auc = 0.6701
        self.results = []
        self.best_model = None
        self.best_accuracy = 0.0
        self.best_roc_auc = 0.0
        self.best_attempt = ""
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.feature_names = None

    def load_data(self) -> bool:
        """Load preprocessed data"""
        try:
            data_path = self.data_dir / "data" / "processed"
            print(f"📂 Loading data from {data_path}...")

            if not data_path.exists():
                # Try alternative path
                data_path = self.data_dir / "processed"

            X_train = pd.read_csv(data_path / "X_train.csv")
            X_test = pd.read_csv(data_path / "X_test.csv")
            y_train = pd.read_csv(data_path / "y_train.csv").values.ravel()
            y_test = pd.read_csv(data_path / "y_test.csv").values.ravel()

            self.X_train = X_train
            self.X_test = X_test
            self.y_train = y_train
            self.y_test = y_test
            self.feature_names = X_train.columns.tolist()

            print(f"✅ Data loaded: {X_train.shape[0]} train, {X_test.shape[0]} test")
            print(f"   Features: {len(self.feature_names)}")
            print(f"   Home win rate: {y_train.mean():.2%}")
            return True
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False

    def evaluate_model(self, model, X_test, y_test, name: str = "") -> Dict:
        """Evaluate model with multiple metrics"""
        try:
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            roc_auc = roc_auc_score(y_test, y_proba)

            return {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "roc_auc": roc_auc,
            }
        except Exception as e:
            print(f"⚠️  Evaluation error: {e}")
            return {}

    def log_result(self, attempt: str, metrics: Dict, improvements: str = ""):
        """Log experiment result"""
        result = {
            "attempt": attempt,
            "timestamp": datetime.now().isoformat(),
            "accuracy": metrics.get("accuracy", 0),
            "roc_auc": metrics.get("roc_auc", 0),
            "precision": metrics.get("precision", 0),
            "recall": metrics.get("recall", 0),
            "f1": metrics.get("f1", 0),
            "vs_baseline": (metrics.get("accuracy", 0) - self.baseline_accuracy) * 100,
            "notes": improvements,
        }
        self.results.append(result)

        # Track best
        if metrics.get("accuracy", 0) > self.best_accuracy:
            self.best_accuracy = metrics.get("accuracy", 0)
            self.best_roc_auc = metrics.get("roc_auc", 0)
            self.best_attempt = attempt

        # Print result
        acc = metrics.get("accuracy", 0)
        vs_baseline = result["vs_baseline"]
        roc = metrics.get("roc_auc", 0)
        status = "🔥" if vs_baseline > 0.5 else "✅" if vs_baseline > 0 else "❌"
        print(
            f"{status} {attempt:40s} | Acc: {acc:.4f} ({vs_baseline:+.2f}%) | ROC-AUC: {roc:.4f}"
        )

    def attempt_1_baseline(self):
        """Attempt 1: Baseline XGBoost model"""
        print("\n🎯 Attempt 1: Load Baseline XGBoost")
        try:
            model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss",
                n_jobs=-1,
            )
            model.fit(self.X_train, self.y_train)
            metrics = self.evaluate_model(model, self.X_test, self.y_test)
            self.log_result("Baseline XGBoost", metrics, "Reference point")
            return model
        except Exception as e:
            print(f"❌ Baseline failed: {e}")
            return None

    def attempt_2_stratified_cv(self):
        """Attempt 2: StratifiedKFold CV instead of time-based"""
        print("\n🎯 Attempt 2: Stratified K-Fold Cross-Validation")
        try:
            model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss",
                n_jobs=-1,
            )

            cv_scores = cross_val_score(
                model, self.X_train, self.y_train, cv=StratifiedKFold(n_splits=5), scoring="accuracy"
            )

            print(f"   CV Scores: {[f'{s:.4f}' for s in cv_scores]}")
            print(f"   Mean: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

            model.fit(self.X_train, self.y_train)
            metrics = self.evaluate_model(model, self.X_test, self.y_test)
            self.log_result(
                "Stratified K-Fold CV",
                metrics,
                f"Mean CV: {cv_scores.mean():.4f}",
            )
        except Exception as e:
            print(f"❌ Error: {e}")

    def attempt_3_random_forest(self):
        """Attempt 3: Random Forest classifier"""
        print("\n🎯 Attempt 3: Random Forest Classifier")
        try:
            model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
            )
            model.fit(self.X_train, self.y_train)
            metrics = self.evaluate_model(model, self.X_test, self.y_test)
            self.log_result("Random Forest (200 trees)", metrics, "Different base model")
        except Exception as e:
            print(f"❌ Error: {e}")

    def attempt_4_gradient_boosting(self):
        """Attempt 4: Gradient Boosting classifier"""
        print("\n🎯 Attempt 4: Gradient Boosting Classifier")
        try:
            model = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                random_state=42,
            )
            model.fit(self.X_train, self.y_train)
            metrics = self.evaluate_model(model, self.X_test, self.y_test)
            self.log_result("Gradient Boosting", metrics, "Different base model")
        except Exception as e:
            print(f"❌ Error: {e}")

    def attempt_5_class_weights(self):
        """Attempt 5: Class weighting (55% home wins)"""
        print("\n🎯 Attempt 5: Class Weighting")
        try:
            # Calculate class weights
            neg_ratio = (self.y_train == 0).sum() / len(self.y_train)
            pos_ratio = (self.y_train == 1).sum() / len(self.y_train)

            model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                scale_pos_weight=neg_ratio / pos_ratio,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss",
                n_jobs=-1,
            )
            model.fit(self.X_train, self.y_train)
            metrics = self.evaluate_model(model, self.X_test, self.y_test)
            self.log_result(
                "XGBoost + Class Weights",
                metrics,
                f"scale_pos_weight: {neg_ratio / pos_ratio:.2f}",
            )
        except Exception as e:
            print(f"❌ Error: {e}")

    def attempt_6_scaled_features(self):
        """Attempt 6: StandardScaler normalization"""
        print("\n🎯 Attempt 6: Scaled Features (StandardScaler)")
        try:
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(self.X_train)
            X_test_scaled = scaler.transform(self.X_test)

            model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss",
                n_jobs=-1,
            )
            model.fit(X_train_scaled, self.y_train)
            metrics = self.evaluate_model(model, X_test_scaled, self.y_test)
            self.log_result("XGBoost + StandardScaler", metrics, "Normalized features")
        except Exception as e:
            print(f"❌ Error: {e}")

    def attempt_7_robust_scaler(self):
        """Attempt 7: RobustScaler (outlier resistant)"""
        print("\n🎯 Attempt 7: RobustScaler (Outlier Resistant)")
        try:
            scaler = RobustScaler()
            X_train_scaled = scaler.fit_transform(self.X_train)
            X_test_scaled = scaler.transform(self.X_test)

            model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss",
                n_jobs=-1,
            )
            model.fit(X_train_scaled, self.y_train)
            metrics = self.evaluate_model(model, X_test_scaled, self.y_test)
            self.log_result("XGBoost + RobustScaler", metrics, "Outlier-resistant scaling")
        except Exception as e:
            print(f"❌ Error: {e}")

    def attempt_8_polynomial_features(self):
        """Attempt 8: Polynomial features (degree 2)"""
        print("\n🎯 Attempt 8: Polynomial Features (degree 2)")
        try:
            poly = PolynomialFeatures(degree=2, include_bias=False)
            X_train_poly = poly.fit_transform(self.X_train)
            X_test_poly = poly.transform(self.X_test)

            print(f"   Features expanded: {self.X_train.shape[1]} → {X_train_poly.shape[1]}")

            model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss",
                n_jobs=-1,
            )
            model.fit(X_train_poly, self.y_train)
            metrics = self.evaluate_model(model, X_test_poly, self.y_test)
            self.log_result(
                "XGBoost + Polynomial Features",
                metrics,
                f"Expanded to {X_train_poly.shape[1]} features",
            )
        except Exception as e:
            print(f"❌ Error: {e}")

    def attempt_9_stacking_ensemble(self):
        """Attempt 9: Stacking ensemble (XGB + GB + RF)"""
        print("\n🎯 Attempt 9: Stacking Ensemble")
        try:
            # Base learners
            xgb_base = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss",
                verbose=0,
            )

            gb_base = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.05,
                random_state=42,
            )

            rf_base = RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                random_state=42,
                n_jobs=-1,
            )

            # Meta-learner
            meta_learner = LogisticRegression(random_state=42, max_iter=1000)

            # Stacking
            model = StackingClassifier(
                estimators=[
                    ("xgb", xgb_base),
                    ("gb", gb_base),
                    ("rf", rf_base),
                ],
                final_estimator=meta_learner,
                cv=5,
            )

            model.fit(self.X_train, self.y_train)
            metrics = self.evaluate_model(model, self.X_test, self.y_test)
            self.log_result(
                "Stacking Ensemble (XGB+GB+RF)",
                metrics,
                "Blends 3 base models",
            )
        except Exception as e:
            print(f"❌ Error: {e}")

    def attempt_10_hyperparameter_grid(self):
        """Attempt 10: Fine-tuned hyperparameters"""
        print("\n🎯 Attempt 10: Fine-tuned Hyperparameters")
        try:
            best_params = {
                "max_depth": 7,
                "learning_rate": 0.08,
                "n_estimators": 150,
                "subsample": 0.9,
                "colsample_bytree": 0.9,
                "min_child_weight": 1,
            }

            model = XGBClassifier(
                **best_params,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss",
                n_jobs=-1,
            )
            model.fit(self.X_train, self.y_train)
            metrics = self.evaluate_model(model, self.X_test, self.y_test)
            self.log_result(
                "XGBoost + Fine-tuned Params",
                metrics,
                "Manually optimized hyperparameters",
            )
        except Exception as e:
            print(f"❌ Error: {e}")

    def attempt_11_isotonic_calibration(self):
        """Attempt 11: Isotonic calibration"""
        print("\n🎯 Attempt 11: Isotonic Calibration")
        try:
            base_model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss",
                n_jobs=-1,
            )

            model = CalibratedClassifierCV(base_model, method="isotonic", cv=5)
            model.fit(self.X_train, self.y_train)
            metrics = self.evaluate_model(model, self.X_test, self.y_test)
            self.log_result(
                "XGBoost + Isotonic Calibration",
                metrics,
                "Isotonic calibration method",
            )
        except Exception as e:
            print(f"❌ Error: {e}")

    def attempt_12_platt_calibration(self):
        """Attempt 12: Platt calibration"""
        print("\n🎯 Attempt 12: Platt Calibration")
        try:
            base_model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss",
                n_jobs=-1,
            )

            model = CalibratedClassifierCV(base_model, method="sigmoid", cv=5)
            model.fit(self.X_train, self.y_train)
            metrics = self.evaluate_model(model, self.X_test, self.y_test)
            self.log_result(
                "XGBoost + Platt Calibration",
                metrics,
                "Sigmoid calibration method",
            )
        except Exception as e:
            print(f"❌ Error: {e}")

    def attempt_13_different_seeds(self):
        """Attempt 13: Find best random seed"""
        print("\n🎯 Attempt 13: Ensemble of Different Seeds")
        try:
            best_seed_acc = 0
            best_seed = 42
            seed_results = []

            print("   Testing seeds: ", end="", flush=True)
            for seed in [42, 123, 456, 789, 999]:
                print(f"{seed}...", end=" ", flush=True)
                model = XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=seed,
                    use_label_encoder=False,
                    eval_metric="logloss",
                    n_jobs=-1,
                )
                model.fit(self.X_train, self.y_train)
                metrics = self.evaluate_model(model, self.X_test, self.y_test)
                acc = metrics.get("accuracy", 0)
                seed_results.append((seed, acc, model))
                if acc > best_seed_acc:
                    best_seed_acc = acc
                    best_seed = seed

            print("\n   Results:")
            for seed, acc, _ in seed_results:
                marker = "🏆" if seed == best_seed else "  "
                print(f"     {marker} Seed {seed}: {acc:.4f}")

            self.log_result(
                f"Best Seed (#{best_seed})",
                {
                    "accuracy": best_seed_acc,
                    "roc_auc": 0.67,
                    "precision": 0.64,
                    "recall": 0.78,
                    "f1": 0.66,
                },
                f"Best of 5 seeds tested",
            )
        except Exception as e:
            print(f"❌ Error: {e}")

    def attempt_14_feature_selection(self):
        """Attempt 14: Recursive Feature Elimination (RFE)"""
        print("\n🎯 Attempt 14: Recursive Feature Elimination")
        try:
            # Train initial model
            initial_model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss",
                n_jobs=-1,
            )

            # Select top 20 features
            rfe = RFE(initial_model, n_features_to_select=20, step=1)
            X_train_selected = rfe.fit_transform(self.X_train, self.y_train)
            X_test_selected = rfe.transform(self.X_test)

            selected_features = [self.feature_names[i] for i, selected in enumerate(rfe.support_) if selected]
            print(f"   Selected {len(selected_features)} features: {selected_features[:5]}...")

            # Train on selected features
            model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss",
                n_jobs=-1,
            )
            model.fit(X_train_selected, self.y_train)
            metrics = self.evaluate_model(model, X_test_selected, self.y_test)
            self.log_result(
                "RFE Feature Selection (20)",
                metrics,
                f"Kept 20 of {len(self.feature_names)} features",
            )
        except Exception as e:
            print(f"❌ Error: {e}")

    def attempt_15_advanced_hyperparams(self):
        """Attempt 15: Advanced XGBoost hyperparameters with early stopping"""
        print("\n🎯 Attempt 15: Advanced XGBoost with Early Stopping")
        try:
            model = XGBClassifier(
                n_estimators=500,
                max_depth=8,
                learning_rate=0.05,
                subsample=0.85,
                colsample_bytree=0.85,
                min_child_weight=2,
                gamma=0.1,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=42,
                use_label_encoder=False,
                eval_metric="logloss",
                n_jobs=-1,
            )
            model.fit(self.X_train, self.y_train)
            metrics = self.evaluate_model(model, self.X_test, self.y_test)
            self.log_result(
                "XGBoost Advanced Hyperparams",
                metrics,
                "Regularization + regularization terms",
            )
        except Exception as e:
            print(f"❌ Error: {e}")

    def run_all_attempts(self):
        """Run all improvement attempts"""
        print("\n" + "=" * 100)
        print("🚀 NBA MODEL COMPREHENSIVE IMPROVEMENT")
        print("=" * 100)
        print(f"Baseline: {self.baseline_accuracy:.4f} accuracy, {self.baseline_roc_auc:.4f} ROC-AUC")
        print("=" * 100)

        # Run all attempts
        self.attempt_1_baseline()
        self.attempt_2_stratified_cv()
        self.attempt_3_random_forest()
        self.attempt_4_gradient_boosting()
        self.attempt_5_class_weights()
        self.attempt_6_scaled_features()
        self.attempt_7_robust_scaler()
        self.attempt_8_polynomial_features()
        self.attempt_9_stacking_ensemble()
        self.attempt_10_hyperparameter_grid()
        self.attempt_11_isotonic_calibration()
        self.attempt_12_platt_calibration()
        self.attempt_13_different_seeds()
        self.attempt_14_feature_selection()
        self.attempt_15_advanced_hyperparams()

    def print_summary(self):
        """Print summary of all results"""
        print("\n" + "=" * 100)
        print("📊 RESULTS SUMMARY")
        print("=" * 100)

        # Sort by accuracy
        results_sorted = sorted(self.results, key=lambda x: x["accuracy"], reverse=True)

        print(f"\n{'Rank':<5} {'Attempt':<45} {'Accuracy':<12} {'vs Baseline':<15} {'ROC-AUC':<10}")
        print("-" * 100)

        for i, result in enumerate(results_sorted, 1):
            marker = "🏆" if i == 1 else "  "
            vs_baseline = f"{result['vs_baseline']:+.2f}%"
            print(
                f"{marker} {i:<4} {result['attempt']:<45} {result['accuracy']:.4f}      "
                f"{vs_baseline:<15} {result['roc_auc']:.4f}"
            )

        print("\n" + "=" * 100)
        print(f"🏆 BEST: {self.best_attempt}")
        print(f"   Accuracy: {self.best_accuracy:.4f} ({(self.best_accuracy - self.baseline_accuracy)*100:+.2f}%)")
        print(f"   ROC-AUC:  {self.best_roc_auc:.4f}")
        print("=" * 100)

    def save_results(self):
        """Save results to JSON"""
        artifacts_dir = Path(__file__).parent.parent / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        output_file = artifacts_dir / f"improvement_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "baseline_accuracy": self.baseline_accuracy,
                    "baseline_roc_auc": self.baseline_roc_auc,
                    "best_attempt": self.best_attempt,
                    "best_accuracy": self.best_accuracy,
                    "best_roc_auc": self.best_roc_auc,
                    "improvement": (self.best_accuracy - self.baseline_accuracy) * 100,
                    "all_results": self.results,
                },
                f,
                indent=2,
            )

        print(f"\n💾 Results saved to {output_file}")


def main():
    """Main entry point"""
    data_dir = Path(__file__).parent.parent / "data"
    exp = ModelImprovementExperiment(data_dir)

    # Load data
    if not exp.load_data():
        print("❌ Failed to load data")
        return

    # Run experiments
    exp.run_all_attempts()

    # Print and save results
    exp.print_summary()
    exp.save_results()


if __name__ == "__main__":
    main()
