"""Load trusted local ensemble artifacts and predict home-team win probabilities."""

import asyncio
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


class EnsemblePredictor:
    """Inference for the three-model artifact format written by EnsembleTrainer.

    Pickle files can execute code. Only load artifacts you created or otherwise
    trust; never accept uploaded model files from an untrusted caller.
    """

    MODEL_NAMES = ("xgb", "lgb", "cat")

    def __init__(self, model_dir: str | Path = "artifacts/models/pregame", *, autoload=True):
        self.model_dir = Path(model_dir)
        self.xgb_model = self.lgb_model = self.cat_model = None
        self.weights = self.feature_names = self.metadata = None
        if autoload:
            self._load_models()

    async def load_async(self) -> None:
        """Run blocking disk reads in a worker, not an async function in a worker."""
        await asyncio.to_thread(self._load_models)

    def _load_models(self) -> None:
        metadata_path = self.model_dir / "ensemble_metadata.json"
        if not metadata_path.is_file():
            raise FileNotFoundError(f"Missing ensemble metadata: {metadata_path}")
        with metadata_path.open(encoding="utf-8") as handle:
            metadata = json.load(handle)
        if not isinstance(metadata, dict):
            raise ValueError("Ensemble metadata must be a JSON object")

        features = metadata.get("feature_names")
        if (not isinstance(features, list) or not features
                or not all(isinstance(name, str) and name for name in features)
                or len(features) != len(set(features))):
            raise ValueError("feature_names must be a nonempty list of unique strings")
        weights = metadata.get("weights")
        if not isinstance(weights, dict) or set(weights) != set(self.MODEL_NAMES):
            raise ValueError("weights must contain exactly xgb, lgb, and cat")
        if any(isinstance(value, bool) or not isinstance(value, (int, float))
               or not np.isfinite(value) or value < 0 for value in weights.values()):
            raise ValueError("Ensemble weights must be finite, nonnegative numbers")
        if not np.isclose(sum(weights.values()), 1.0, rtol=0, atol=1e-8):
            raise ValueError("Ensemble weights must sum to 1")

        paths = {name: self.model_dir / f"{name}_model.pkl" for name in self.MODEL_NAMES}
        for path in paths.values():
            if not path.is_file():
                raise FileNotFoundError(f"Missing model artifact: {path}")
        models = {}
        for name, path in paths.items():
            with path.open("rb") as handle:
                model = pickle.load(handle)
            if not callable(getattr(model, "predict_proba", None)):
                raise ValueError(f"{name} model does not implement predict_proba")
            models[name] = model

        # Do not replace a working ensemble with a partially loaded one.
        self.__dict__.update(
            metadata=metadata, weights=weights, feature_names=features,
            xgb_model=models["xgb"], lgb_model=models["lgb"], cat_model=models["cat"],
        )

    def _ordered_features(self, features: pd.DataFrame) -> pd.DataFrame:
        if self.feature_names is None:
            raise RuntimeError("Models are not loaded; call load_async or enable autoload")
        if not isinstance(features, pd.DataFrame):
            raise TypeError("Features must be a pandas DataFrame")
        if not features.columns.is_unique:
            raise ValueError("Feature columns must be unique")
        missing = set(self.feature_names) - set(features.columns)
        if missing:
            raise ValueError(f"Missing features: {sorted(missing)}")
        try:
            ordered = features.loc[:, self.feature_names].astype(float).fillna(0)
        except (TypeError, ValueError) as exc:
            raise ValueError("Model features must be numeric") from exc
        if not np.isfinite(ordered.to_numpy()).all():
            raise ValueError("Model features cannot contain infinity")
        return ordered

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Return one probability per row, preserving row order.

        Columns are ordered by the saved schema. Missing values are filled with
        zero, matching the original training path; missing columns are errors.
        """
        ordered = self._ordered_features(X)
        if ordered.empty:
            return np.empty(0, dtype=float)
        result = np.zeros(len(ordered), dtype=float)
        for name in self.MODEL_NAMES:
            model = getattr(self, f"{name}_model")
            classes = np.asarray(getattr(model, "classes_", []))
            if classes.shape != (2,) or set(classes.tolist()) != {0, 1}:
                raise ValueError(f"{name} model must have binary classes 0 and 1")
            probabilities = np.asarray(model.predict_proba(ordered), dtype=float)
            if (probabilities.shape != (len(ordered), 2)
                    or not np.isfinite(probabilities).all()
                    or (probabilities < 0).any() or (probabilities > 1).any()
                    or not np.allclose(probabilities.sum(axis=1), 1.0, rtol=0, atol=1e-6)):
                raise ValueError(f"{name} returned invalid probability rows")
            positive_column = int(np.flatnonzero(classes == 1)[0])
            result += self.weights[name] * probabilities[:, positive_column]
        # Validated weights may differ from 1 only by floating-point roundoff.
        return np.clip(result, 0, 1)

    def predict_with_features(self, X: pd.DataFrame, top_n: int = 5) -> list[dict[str, Any]]:
        """Return probabilities and global LightGBM importance, not local attribution."""
        if isinstance(top_n, bool) or not isinstance(top_n, int) or top_n < 0:
            raise ValueError("top_n must be a nonnegative integer")
        predictions = self.predict(X)
        ordered = self._ordered_features(X)
        base = self.lgb_model
        if hasattr(base, "calibrated_classifiers_"):
            base = base.calibrated_classifiers_[0].estimator
        importance = getattr(base, "feature_importances_", None)
        if importance is None:
            return [{"prediction": float(probability), "top_features": []}
                    for probability in predictions]
        importance = np.asarray(importance, dtype=float)
        if importance.shape != (len(self.feature_names),) or not np.isfinite(importance).all():
            raise ValueError("Feature importance does not match the saved schema")
        indices = np.argsort(-importance, kind="stable")[:top_n]
        return [
            {
                "prediction": float(probability),
                "top_features": [
                    {"feature": self.feature_names[index],
                     "importance": float(importance[index]),
                     "value": float(ordered.iloc[row, index])}
                    for index in indices
                ],
            }
            for row, probability in enumerate(predictions)
        ]

    def get_model_info(self) -> dict[str, Any]:
        if self.metadata is None:
            raise RuntimeError("Models are not loaded")
        return {
            "feature_count": len(self.feature_names),
            "features": list(self.feature_names),
            "weights": dict(self.weights),
            "metrics": self.metadata.get("metrics", {}),
            "timestamp": self.metadata.get("timestamp"),
        }
