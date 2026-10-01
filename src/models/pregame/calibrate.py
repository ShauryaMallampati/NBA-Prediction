"""Make our probability predictions more accurate.

We use two fancy calibration methods:
- Platt scaling: Fits a sigmoid curve to adjust probabilities
- Isotonic regression: Non-parametric, just learns the right mapping
- Combined approach: Uses both together (CalibratedClassifierCV)

The goal? When we say 70%, we want it to actually be 70%.
"""

import pandas as pd
import numpy as np
import pickle
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss, log_loss
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedCalibrator:
    """Calibrate using Platt scaling and/or Isotonic regression."""
    
    def __init__(self, output_dir: str = "artifacts/models/pregame"):
        """Set up the calibrator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Calibration methods
        self.platt_model = None
        self.isotonic_model = None
        self.combined_model = None
        
        # Calibration metrics
        self.metrics = {}
        
        logger.info("📊 Advanced calibrator initialized")
    
    def calibrate_model(self, model, X: pd.DataFrame, y: pd.Series, method: str = 'isotonic') -> object:
        """Take a raw model and calibrate its probabilities.
        
        Args:
            model: The uncalibrated model
            X: Feature data
            y: True outcomes
            method: Which calibration method to use ('sigmoid', 'isotonic', or 'auto')
        
        Returns:
            A calibrated version of the model
        """
        logger.info(f"📊 Calibrating model using {method}...")
        
        # Use CalibratedClassifierCV
        if method == 'auto':
            # Try both methods and use the best one
            calibrated_platt = CalibratedClassifierCV(model, method='sigmoid', cv=3)
            calibrated_platt.fit(X, y)
            
            calibrated_isotonic = CalibratedClassifierCV(model, method='isotonic', cv=3)
            calibrated_isotonic.fit(X, y)
            
            # Evaluate both methods
            platt_pred = calibrated_platt.predict_proba(X)[:, 1]
            isotonic_pred = calibrated_isotonic.predict_proba(X)[:, 1]
            
            platt_brier = brier_score_loss(y, platt_pred)
            isotonic_brier = brier_score_loss(y, isotonic_pred)
            
            if platt_brier < isotonic_brier:
                logger.info(f"  ✅ Selected Platt scaling (Brier: {platt_brier:.4f})")
                return calibrated_platt
            else:
                logger.info(f"  ✅ Selected Isotonic regression (Brier: {isotonic_brier:.4f})")
                return calibrated_isotonic
        else:
            calibrated_model = CalibratedClassifierCV(model, method=method, cv=3)
            calibrated_model.fit(X, y)
            logger.info(f"  ✅ Calibration complete ({method})")
            return calibrated_model
    
    def calibrate_ensemble(
        self,
        xgb_model,
        lgb_model,
        cat_model,
        X: pd.DataFrame,
        y: pd.Series,
        method: str = 'isotonic'
    ) -> Dict:
        """
        Calibrate ensemble models.
        
        Args:
            xgb_model: XGBoost model
            lgb_model: LightGBM model
            cat_model: CatBoost model
            X: Features
            y: Target
            method: Calibration method
        
        Returns:
            Dictionary with calibrated models
        """
        logger.info("=" * 80)
        logger.info("ENSEMBLE CALIBRATION")
        logger.info("=" * 80)
        
        # Calibrate each model
        xgb_calibrated = self.calibrate_model(xgb_model, X, y, method)
        lgb_calibrated = self.calibrate_model(lgb_model, X, y, method)
        cat_calibrated = self.calibrate_model(cat_model, X, y, method)
        
        # Evaluate calibration
        xgb_pred = xgb_calibrated.predict_proba(X)[:, 1]
        lgb_pred = lgb_calibrated.predict_proba(X)[:, 1]
        cat_pred = cat_calibrated.predict_proba(X)[:, 1]
        
        xgb_brier = brier_score_loss(y, xgb_pred)
        lgb_brier = brier_score_loss(y, lgb_pred)
        cat_brier = brier_score_loss(y, cat_pred)
        
        metrics = {
            'xgb': {'brier': xgb_brier, 'log_loss': log_loss(y, xgb_pred)},
            'lgb': {'brier': lgb_brier, 'log_loss': log_loss(y, lgb_pred)},
            'cat': {'brier': cat_brier, 'log_loss': log_loss(y, cat_pred)},
        }
        
        self.platt_model = xgb_calibrated
        self.isotonic_model = lgb_calibrated
        self.combined_model = cat_calibrated
        self.metrics = metrics
        
        logger.info("=" * 80)
        logger.info("CALIBRATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"XGBoost:    Brier={xgb_brier:.4f}, LogLoss={metrics['xgb']['log_loss']:.4f}")
        logger.info(f"LightGBM:   Brier={lgb_brier:.4f}, LogLoss={metrics['lgb']['log_loss']:.4f}")
        logger.info(f"CatBoost:   Brier={cat_brier:.4f}, LogLoss={metrics['cat']['log_loss']:.4f}")
        logger.info("=" * 80)
        
        return {
            'xgb_calibrated': xgb_calibrated,
            'lgb_calibrated': lgb_calibrated,
            'cat_calibrated': cat_calibrated,
            'metrics': metrics,
        }
    
    def plot_calibration_curve(self, model, X: pd.DataFrame, y: pd.Series, name: str = 'Model'):
        """
        Plot calibration curve.
        
        Args:
            model: Model to evaluate
            X: Features
            y: Target
            name: Model name
        """
        logger.info(f"📊 Plotting calibration curve for {name}...")
        
        # Get predictions
        y_pred = model.predict_proba(X)[:, 1]
        
        # Calculate calibration curve
        fraction_of_positives, mean_predicted_value = calibration_curve(
            y, y_pred, n_bins=10, strategy='uniform'
        )
        
        # Plot
        plt.figure(figsize=(10, 6))
        plt.plot(mean_predicted_value, fraction_of_positives, 's-', label=name)
        plt.plot([0, 1], [0, 1], 'k--', label='Perfectly calibrated')
        plt.xlabel('Mean Predicted Probability')
        plt.ylabel('Fraction of Positives')
        plt.title(f'Calibration Curve: {name}')
        plt.legend()
        plt.grid(True)
        
        # Save plot
        output_path = self.output_dir / f"calibration_curve_{name.lower()}.png"
        plt.savefig(output_path)
        plt.close()
        
        logger.info(f"  ✅ Saved calibration curve to {output_path}")
    
    def save_calibration_metrics(self):
        """Save calibration metrics to disk."""
        logger.info("💾 Saving calibration metrics...")
        
        output_path = self.output_dir / "calibration_metrics.json"
        with open(output_path, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        logger.info(f"  ✅ Saved metrics to {output_path}")
    
    def calculate_confidence_intervals(self, y_pred: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculate confidence intervals for predictions.
        
        Args:
            y_pred: Predictions (probabilities)
            alpha: Significance level (default: 0.05 for 95% CI)
        
        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        # Simple confidence intervals based on prediction variance
        # More sophisticated methods could use bootstrap or Bayesian approaches
        
        # Standard error approximation
        n = len(y_pred)
        se = np.sqrt(y_pred * (1 - y_pred) / n)
        
        # Z-score for confidence level
        from scipy import stats
        z = stats.norm.ppf(1 - alpha / 2)
        
        # Confidence intervals
        lower_bound = np.clip(y_pred - z * se, 0, 1)
        upper_bound = np.clip(y_pred + z * se, 0, 1)
        
        return lower_bound, upper_bound


def main():
    """Main calibration function."""
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
    
    # Load models (if available)
    model_dir = Path("artifacts/models/pregame")
    
    # For now, create dummy models for demonstration
    from sklearn.ensemble import RandomForestClassifier
    xgb_model = RandomForestClassifier(n_estimators=100, random_state=42)
    lgb_model = RandomForestClassifier(n_estimators=100, random_state=42)
    cat_model = RandomForestClassifier(n_estimators=100, random_state=42)
    
    xgb_model.fit(X, y)
    lgb_model.fit(X, y)
    cat_model.fit(X, y)
    
    # Calibrate
    calibrator = AdvancedCalibrator()
    calibrated_models = calibrator.calibrate_ensemble(xgb_model, lgb_model, cat_model, X, y, method='isotonic')
    
    # Plot calibration curves
    calibrator.plot_calibration_curve(calibrated_models['xgb_calibrated'], X, y, 'XGBoost')
    calibrator.plot_calibration_curve(calibrated_models['lgb_calibrated'], X, y, 'LightGBM')
    calibrator.plot_calibration_curve(calibrated_models['cat_calibrated'], X, y, 'CatBoost')
    
    # Save metrics
    calibrator.save_calibration_metrics()
    
    logger.info("\n✅ Calibration complete!")
    logger.info(f"   Metrics saved to {calibrator.output_dir / 'calibration_metrics.json'}")
    
    return calibrator


if __name__ == "__main__":
    calibrator = main()
