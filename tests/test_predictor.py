import asyncio
import json
import pickle
import threading

import numpy as np
import pandas as pd
import pytest

from src.models.pregame.predictor import EnsemblePredictor


def change_metadata(directory, key, value):
    path = directory / "ensemble_metadata.json"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata[key] = value
    path.write_text(json.dumps(metadata), encoding="utf-8")


def test_weighted_probabilities_and_feature_order(model_dir, features):
    predictor = EnsemblePredictor(model_dir)
    before = features.copy(deep=True)
    np.testing.assert_allclose(predictor.predict(features), [0.56, 0.58])
    assert predictor.xgb_model.last_columns == ["elo_diff", "rest_differential"]
    pd.testing.assert_frame_equal(features, before)


def test_positive_label_is_selected_by_class_not_column_number(model_dir, features):
    predictor = EnsemblePredictor(model_dir)
    predictor.xgb_model.classes_ = np.array([1, 0])
    predictor.lgb_model.classes_ = np.array([1, 0])
    predictor.cat_model.classes_ = np.array([1, 0])
    np.testing.assert_allclose(predictor.predict(features), [0.56, 0.58])


def test_extra_columns_are_ignored_and_nan_matches_training_policy(model_dir, features):
    predictor = EnsemblePredictor(model_dir)
    features["irrelevant"] = "not a feature"
    features.loc["second", "elo_diff"] = np.nan
    np.testing.assert_allclose(predictor.predict(features), [0.55, 0.58])
    assert np.isfinite(predictor.xgb_model.last_values).all()


def test_async_loading_runs_blocking_work_in_another_thread(model_dir, features, monkeypatch):
    predictor = EnsemblePredictor(model_dir, autoload=False)
    main_thread = threading.get_ident()
    observed = []
    original = predictor._load_models

    def load():
        observed.append(threading.get_ident())
        original()

    monkeypatch.setattr(predictor, "_load_models", load)
    asyncio.run(predictor.load_async())
    assert observed and observed[0] != main_thread
    assert isinstance(predictor.metadata, dict)
    np.testing.assert_allclose(predictor.predict(features), [0.56, 0.58])


def test_missing_metadata_is_not_a_silent_initialization(tmp_path):
    with pytest.raises(FileNotFoundError, match="metadata"):
        EnsemblePredictor(tmp_path)


@pytest.mark.parametrize("name", ["xgb", "lgb", "cat"])
def test_missing_artifact_has_clear_error(model_dir, name):
    (model_dir / f"{name}_model.pkl").unlink()
    with pytest.raises(FileNotFoundError, match=name):
        EnsemblePredictor(model_dir)


def test_failed_reload_preserves_loaded_ensemble(model_dir, features):
    predictor = EnsemblePredictor(model_dir)
    original = (predictor.xgb_model, predictor.lgb_model, predictor.cat_model, predictor.metadata)
    (model_dir / "cat_model.pkl").unlink()
    with pytest.raises(FileNotFoundError):
        asyncio.run(predictor.load_async())
    assert (predictor.xgb_model, predictor.lgb_model, predictor.cat_model, predictor.metadata) == original
    np.testing.assert_allclose(predictor.predict(features), [0.56, 0.58])


@pytest.mark.parametrize("weights", [
    {}, {"xgb": 1.0}, {"xgb": 1.0, "lgb": 1.0, "cat": 1.0},
    {"xgb": -0.1, "lgb": 0.5, "cat": 0.6},
    {"xgb": float("nan"), "lgb": 0.5, "cat": 0.5},
    {"xgb": float("inf"), "lgb": 0.0, "cat": 0.0},
    {"xgb": True, "lgb": 0.0, "cat": 0.0},
    {"xgb": "0.5", "lgb": 0.25, "cat": 0.25},
])
def test_invalid_weights_are_rejected(model_dir, weights):
    change_metadata(model_dir, "weights", weights)
    with pytest.raises(ValueError, match="[Ww]eights"):
        EnsemblePredictor(model_dir)


@pytest.mark.parametrize("names", [[], ["elo_diff", "elo_diff"], [1, 2], "elo_diff", [""]])
def test_invalid_feature_schema_is_rejected(model_dir, names):
    change_metadata(model_dir, "feature_names", names)
    with pytest.raises(ValueError, match="feature_names"):
        EnsemblePredictor(model_dir)


def test_malformed_metadata_is_rejected(model_dir):
    (model_dir / "ensemble_metadata.json").write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError):
        EnsemblePredictor(model_dir)


def test_model_must_implement_prediction(model_dir):
    with (model_dir / "xgb_model.pkl").open("wb") as handle:
        pickle.dump({"not": "a classifier"}, handle)
    with pytest.raises(ValueError, match="predict_proba"):
        EnsemblePredictor(model_dir)


def test_unloaded_model_cannot_predict(model_dir, features):
    predictor = EnsemblePredictor(model_dir, autoload=False)
    with pytest.raises(RuntimeError, match="not loaded"):
        predictor.predict(features)


def test_missing_feature_is_rejected(model_dir, features):
    with pytest.raises(ValueError, match="Missing features"):
        EnsemblePredictor(model_dir).predict(features.drop(columns="elo_diff"))


def test_duplicate_columns_are_rejected(model_dir, features):
    duplicated = pd.concat([features, features[["elo_diff"]]], axis=1)
    with pytest.raises(ValueError, match="unique"):
        EnsemblePredictor(model_dir).predict(duplicated)


@pytest.mark.parametrize("bad_value", [float("inf"), float("-inf"), "not numeric"])
def test_invalid_feature_values_are_rejected(model_dir, features, bad_value):
    features = features.astype(object)
    features.loc["second", "elo_diff"] = bad_value
    with pytest.raises(ValueError):
        EnsemblePredictor(model_dir).predict(features)


@pytest.mark.parametrize("bad_output", ["shape", "nan", "range", "sum"])
def test_invalid_probability_outputs_are_rejected(model_dir, features, bad_output):
    predictor = EnsemblePredictor(model_dir)
    predictor.xgb_model.bad_output = bad_output
    with pytest.raises(ValueError, match="probability"):
        predictor.predict(features)


def test_nonbinary_model_is_rejected(model_dir, features):
    predictor = EnsemblePredictor(model_dir)
    predictor.cat_model.classes_ = np.array([0, 2])
    with pytest.raises(ValueError, match="binary classes"):
        predictor.predict(features)


def test_empty_input_with_valid_schema_returns_empty_output(model_dir, features):
    predictor = EnsemblePredictor(model_dir)
    assert predictor.predict(features.iloc[:0]).shape == (0,)


def test_global_importance_uses_the_values_passed_to_the_model(model_dir, features):
    predictor = EnsemblePredictor(model_dir)
    features.loc["second", "elo_diff"] = np.nan
    result = predictor.predict_with_features(features, top_n=1)
    assert result[0]["top_features"] == [{"feature": "elo_diff", "importance": 3.0, "value": 0.0}]
    assert len(result) == 2
    assert predictor.get_model_info()["metrics"] == {}
    assert predictor.get_model_info()["timestamp"] is None


@pytest.mark.parametrize("top_n", [-1, True, 1.5])
def test_invalid_importance_count_is_rejected(model_dir, features, top_n):
    with pytest.raises(ValueError, match="top_n"):
        EnsemblePredictor(model_dir).predict_with_features(features, top_n=top_n)
