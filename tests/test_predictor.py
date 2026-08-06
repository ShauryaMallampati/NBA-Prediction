"""The prediction interface: artifact loading, schema validation, end-to-end use."""

import json

import numpy as np
import pandas as pd
import pytest

from src.common.features import RunningWorldState
from src.models.pregame.predictor import (
    REQUIRED_ARTIFACTS,
    EnsemblePredictor,
    MissingArtifactsError,
)


# --- Missing or incomplete artifacts -----------------------------------------

def test_missing_directory_raises_a_clear_error(tmp_path):
    with pytest.raises(MissingArtifactsError) as excinfo:
        EnsemblePredictor(str(tmp_path / "not-trained-yet"))

    message = str(excinfo.value)
    assert "not-trained-yet" in message
    assert "train_ensemble_v2.py" in message


def test_empty_directory_lists_every_missing_artifact(tmp_path):
    empty = tmp_path / "pregame"
    empty.mkdir()

    with pytest.raises(MissingArtifactsError) as excinfo:
        EnsemblePredictor(str(empty))

    message = str(excinfo.value)
    for artifact in REQUIRED_ARTIFACTS:
        assert artifact in message


@pytest.mark.parametrize("dropped", REQUIRED_ARTIFACTS)
def test_each_artifact_is_individually_required(tmp_path, trained_model_dir, dropped):
    """Removing any single artifact must fail loudly, not degrade silently."""
    partial = tmp_path / f"without-{dropped}"
    partial.mkdir()
    for artifact in REQUIRED_ARTIFACTS:
        if artifact != dropped:
            (partial / artifact).write_bytes((trained_model_dir / artifact).read_bytes())

    with pytest.raises(MissingArtifactsError) as excinfo:
        EnsemblePredictor(str(partial))
    assert dropped in str(excinfo.value)


def test_metadata_without_feature_names_is_rejected(tmp_path, trained_model_dir):
    broken = tmp_path / "no-features"
    broken.mkdir()
    for artifact in REQUIRED_ARTIFACTS:
        (broken / artifact).write_bytes((trained_model_dir / artifact).read_bytes())

    metadata = json.loads((broken / "ensemble_metadata.json").read_text())
    metadata["feature_names"] = []
    (broken / "ensemble_metadata.json").write_text(json.dumps(metadata))

    with pytest.raises(MissingArtifactsError):
        EnsemblePredictor(str(broken))


# --- Schema validation --------------------------------------------------------

@pytest.fixture(scope="module")
def predictor(trained_model_dir):
    return EnsemblePredictor(str(trained_model_dir))


@pytest.fixture
def one_game_features():
    state = RunningWorldState()
    state.update("ALB", "BOU", pd.Timestamp("2024-01-02"), 1, 110, 101)
    state.update("CAL", "DEN", pd.Timestamp("2024-01-04"), 0, 98, 107)
    return pd.DataFrame([
        state.get_team_features("ALB", "CAL", pd.Timestamp("2024-01-10"))
    ])


def test_missing_feature_columns_are_reported_by_name(predictor, one_game_features):
    incomplete = one_game_features.drop(columns=["elo_diff", "home_win_pct_l5"])

    with pytest.raises(ValueError) as excinfo:
        predictor.predict(incomplete)

    message = str(excinfo.value)
    assert "elo_diff" in message
    assert "home_win_pct_l5" in message


def test_predictor_schema_carries_no_outcome_columns(predictor):
    for column in ("home_score", "away_score", "score_diff", "home_win", "away_win"):
        assert column not in predictor.feature_names


def test_column_order_does_not_change_the_prediction(predictor, one_game_features):
    shuffled = one_game_features[list(reversed(one_game_features.columns))]

    assert np.allclose(predictor.predict(one_game_features),
                       predictor.predict(shuffled))


def test_extra_columns_are_ignored(predictor, one_game_features):
    with_extras = one_game_features.assign(scouting_note=1.0, ticket_price=99.0)

    assert np.allclose(predictor.predict(one_game_features),
                       predictor.predict(with_extras))


def test_prepare_features_returns_the_training_order(predictor, one_game_features):
    prepared = predictor.prepare_features(one_game_features)
    assert list(prepared.columns) == predictor.feature_names


# --- End to end ---------------------------------------------------------------

def test_synthetic_fixture_flows_through_the_prediction_interface(predictor, game_log):
    """Replay part of the log, then predict a batch of later games."""
    state = RunningWorldState()
    warmup = game_log.iloc[:800]
    upcoming = game_log.iloc[800:810]

    for row in warmup.itertuples(index=False):
        state.update(row.home, row.away, row.date, row.home_win, row.home_pts, row.away_pts)

    features = pd.DataFrame([
        state.get_team_features(row.home, row.away, row.date)
        for row in upcoming.itertuples(index=False)
    ])

    probabilities = predictor.predict(features)

    assert probabilities.shape == (len(upcoming),)
    assert np.all((probabilities > 0.0) & (probabilities < 1.0))


def test_predictions_are_reproducible(predictor, one_game_features):
    assert np.array_equal(predictor.predict(one_game_features),
                          predictor.predict(one_game_features))


def test_base_models_all_contribute(predictor, one_game_features):
    base = predictor.predict_base_models(one_game_features)

    assert set(base) == {"xgb", "lgb", "cat", "et"}
    for name, probs in base.items():
        assert probs.shape == (1,)
        assert 0.0 < probs[0] < 1.0


def test_model_info_reports_the_released_architecture(predictor):
    info = predictor.get_model_info()

    assert info["version"] == 2
    assert info["architecture"] == "stacking_4base_meta"
    assert info["base_models"] == ["XGBoost", "LightGBM", "CatBoost", "ExtraTrees"]
    assert info["meta_learner"] == "LogisticRegression"
    assert info["feature_count"] == len(predictor.feature_names)
