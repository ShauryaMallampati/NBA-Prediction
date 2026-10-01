"""Small synthetic artifact fixtures; these are not NBA performance evidence."""

import json
import pickle

import numpy as np
import pandas as pd
import pytest


class FixtureClassifier:
    def __init__(self, probability):
        self.probability = probability
        self.classes_ = np.array([0, 1])
        self.feature_importances_ = np.array([3.0, 1.0])
        self.bad_output = None

    def predict_proba(self, features):
        self.last_columns = list(features.columns)
        self.last_values = features.to_numpy(copy=True)
        positive = self.probability + 0.01 * features.iloc[:, 0].to_numpy()
        result = np.column_stack([
            positive if label == 1 else 1 - positive for label in self.classes_
        ])
        if self.bad_output == "shape":
            return result[:, :1]
        if self.bad_output == "nan":
            result[0, 0] = np.nan
        if self.bad_output == "range":
            result[0] = [-0.1, 1.1]
        if self.bad_output == "sum":
            result[0] = [0.1, 0.1]
        return result


@pytest.fixture
def model_dir(tmp_path):
    directory = tmp_path / "artifacts" / "models" / "pregame"
    directory.mkdir(parents=True)
    metadata = {
        "feature_names": ["elo_diff", "rest_differential"],
        "weights": {"xgb": 0.25, "lgb": 0.25, "cat": 0.5},
    }
    (directory / "ensemble_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    for name, probability in (("xgb", 0.2), ("lgb", 0.4), ("cat", 0.8)):
        with (directory / f"{name}_model.pkl").open("wb") as handle:
            pickle.dump(FixtureClassifier(probability), handle)
    return directory


@pytest.fixture
def features():
    # Deliberately reverse schema order and use a non-default index.
    return pd.DataFrame({"rest_differential": [0.0, 2.0], "elo_diff": [1.0, 3.0]},
                        index=["second", "first"])
