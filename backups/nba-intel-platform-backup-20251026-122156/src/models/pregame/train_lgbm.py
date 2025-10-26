"""Train LightGBM pregame model."""

import pickle
from pathlib import Path

import lightgbm as lgb
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split

from src.common.config import load_config
from src.common.logger import setup_logger
from src.common.paths import Paths
from src.common.seed import set_seed

logger = setup_logger(__name__)


def prepare_training_data() -> tuple[pd.DataFrame, pd.Series]:
    """Load and prepare training data."""
    logger.info("Loading pregame features...")
    df = pd.read_parquet(Paths.PROCESSED / "pregame_features.parquet")

    # Feature columns (simplified - full version would include all features)
    feature_cols = [
        "is_home",
        "days_rest",
        "is_back_to_back",
        "pts_last_3",
        "pts_last_5",
        "pts_last_10",
        "margin_last_3",
        "margin_last_5",
        "margin_last_10",
    ]

    X = df[feature_cols].fillna(0)
    y = df["won"]

    logger.info(f"Training data: {len(X)} samples, {len(feature_cols)} features")
    return X, y


def train_model() -> None:
    """Train and calibrate LightGBM model."""
    set_seed(42)
    logger.info("Training pregame LightGBM model...")

    # Load data
    X, y = prepare_training_data()

    # Split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # Load hyperparameters
    params = load_config("params_pregame")["lightgbm"]

    # Train base model
    logger.info("Training base LightGBM...")
    model = lgb.LGBMClassifier(**params)
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(period=100)],
    )

    # Calibrate
    logger.info("Calibrating model...")
    calibrated_model = CalibratedClassifierCV(model, method="isotonic", cv="prefit")
    calibrated_model.fit(X_val, y_val)

    # Save
    model_path = Paths.MODELS / "pregame_lgbm.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(calibrated_model, f)

    logger.info(f"✓ Model saved to {model_path}")

    # Evaluate
    train_acc = model.score(X_train, y_train)
    val_acc = model.score(X_val, y_val)
    logger.info(f"Train accuracy: {train_acc:.4f}")
    logger.info(f"Val accuracy: {val_acc:.4f}")


if __name__ == "__main__":
    train_model()
