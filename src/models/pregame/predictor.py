"""Load the trained ensemble and use it to predict games.

This is the inference side of `train_ensemble_v2.EnsembleTrainerV2`: four
calibrated base models (XGBoost, LightGBM, CatBoost, ExtraTrees) whose
probabilities are combined by a logistic-regression meta-learner.

The feature schema is whatever `RunningWorldState.get_team_features()` produced
at training time; it is stored in `ensemble_metadata.json` and is the single
source of truth for column order at prediction time.
"""

import json
import pickle
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from src.common.features import assert_no_leakage

# Every file `EnsembleTrainerV2.save_models()` writes. All of them are needed to
# reproduce a prediction, so a partial directory is an error rather than a
# silently degraded model.
REQUIRED_ARTIFACTS = (
    "ensemble_metadata.json",
    "xgb_model.pkl",
    "lgb_model.pkl",
    "cat_model.pkl",
    "et_model.pkl",
    "meta_learner.pkl",
    "meta_scaler.pkl",
)


class MissingArtifactsError(FileNotFoundError):
    """Raised when the trained model directory is absent or incomplete."""


class EnsemblePredictor:
    """Predict home-team win probabilities from a trained ensemble."""

    def __init__(self, model_dir: str = "artifacts/models/pregame"):
        """Load every model artifact from `model_dir`.

        Raises:
            MissingArtifactsError: If the directory or any artifact is missing.
        """
        self.model_dir = Path(model_dir)
        self._check_artifacts()

        with open(self.model_dir / "ensemble_metadata.json") as f:
            self.metadata = json.load(f)

        self.feature_names: List[str] = list(self.metadata["feature_names"])
        if not self.feature_names:
            raise MissingArtifactsError(
                f"{self.model_dir / 'ensemble_metadata.json'} lists no feature names."
            )
        # A model trained on an outcome column would score well and predict nothing.
        assert_no_leakage(self.feature_names)

        self.xgb_model = self._load_pickle("xgb_model.pkl")
        self.lgb_model = self._load_pickle("lgb_model.pkl")
        self.cat_model = self._load_pickle("cat_model.pkl")
        self.et_model = self._load_pickle("et_model.pkl")
        self.meta_learner = self._load_pickle("meta_learner.pkl")
        self.meta_scaler = self._load_pickle("meta_scaler.pkl")

    def _check_artifacts(self) -> None:
        """Report every missing artifact at once, not just the first."""
        if not self.model_dir.is_dir():
            raise MissingArtifactsError(
                f"No trained model directory at {self.model_dir}. "
                "Train one first: python scripts/training/train_ensemble_v2.py"
            )

        missing = [n for n in REQUIRED_ARTIFACTS if not (self.model_dir / n).is_file()]
        if missing:
            raise MissingArtifactsError(
                f"{self.model_dir} is missing {len(missing)} required artifact(s): "
                + ", ".join(missing)
                + ". Train the ensemble first: python scripts/training/train_ensemble_v2.py"
            )

    def _load_pickle(self, name: str):
        with open(self.model_dir / name, "rb") as f:
            return pickle.load(f)

    def prepare_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """Validate and order an incoming feature frame.

        Selects exactly the training columns, in the training order, so column
        ordering in the caller's DataFrame cannot change the prediction.

        Args:
            X: A DataFrame with one row per game.

        Returns:
            A DataFrame whose columns are exactly `self.feature_names`, in order.

        Raises:
            ValueError: If any training feature is absent from `X`.
            LeakageError: If the model's own schema carries a post-game outcome
                column (i.e. the metadata is corrupt).
        """
        missing = [c for c in self.feature_names if c not in X.columns]
        if missing:
            raise ValueError(
                f"Feature frame is missing {len(missing)} required column(s): "
                + ", ".join(missing[:10])
                + (" ..." if len(missing) > 10 else "")
            )

        assert_no_leakage(self.feature_names)
        return X.loc[:, self.feature_names]

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Return the home team's win probability for each row of `X`."""
        X_ordered = self.prepare_features(X)

        base_preds = np.column_stack([
            self.xgb_model.predict_proba(X_ordered)[:, 1],
            self.lgb_model.predict_proba(X_ordered)[:, 1],
            self.cat_model.predict_proba(X_ordered)[:, 1],
            self.et_model.predict_proba(X_ordered)[:, 1],
        ])

        # Same meta-feature construction as training; see EnsembleTrainerV2.train_all.
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

    def predict_base_models(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Return each base model's probability, for inspecting disagreement."""
        X_ordered = self.prepare_features(X)
        return {
            "xgb": self.xgb_model.predict_proba(X_ordered)[:, 1],
            "lgb": self.lgb_model.predict_proba(X_ordered)[:, 1],
            "cat": self.cat_model.predict_proba(X_ordered)[:, 1],
            "et": self.et_model.predict_proba(X_ordered)[:, 1],
        }

    def get_model_info(self) -> Dict:
        """Report what was loaded, straight from the training metadata."""
        return {
            "model_dir": str(self.model_dir),
            "version": self.metadata.get("version"),
            "architecture": self.metadata.get("architecture"),
            "base_models": self.metadata.get("base_models"),
            "meta_learner": self.metadata.get("meta_learner"),
            "feature_count": len(self.feature_names),
            "trained_at": self.metadata.get("timestamp"),
            "training_metrics": self.metadata.get("metrics", {}),
        }
