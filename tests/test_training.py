"""Feature chronology and real-estimator smoke tests, not accuracy benchmarks."""

import asyncio
import json
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from src.common.features import add_rest_features, add_streak_features, calculate_elo
from src.models.pregame.predictor import EnsemblePredictor
from src.models.pregame.train_ensemble import EnsembleTrainer


def games():
    return pd.DataFrame({
        "game_id": ["g1", "g2", "g3", "g4"],
        "date": pd.to_datetime(["2024-01-01", "2024-01-03", "2024-01-05", "2024-01-07"]),
        "home": ["AAA", "BBB", "AAA", "BBB"],
        "away": ["BBB", "AAA", "BBB", "AAA"],
        "home_pts": [110, 90, 105, 120], "away_pts": [100, 100, 95, 100],
        "home_win": [1, 0, 1, 1],
    })


@pytest.mark.parametrize("transform", [calculate_elo, add_streak_features])
def test_current_and_future_results_cannot_change_prior_features(transform):
    frame = games()
    changed = frame.copy()
    changed.loc[2:, "home_win"] = 1 - changed.loc[2:, "home_win"]
    left, right = transform(frame), transform(changed)
    columns = list(set(left.columns) - set(frame.columns))
    pd.testing.assert_frame_equal(left.loc[:2, columns], right.loc[:2, columns])
    assert not left.loc[3:, columns].equals(right.loc[3:, columns])


def test_rest_days_and_streaks_use_previous_games():
    frame = add_streak_features(add_rest_features(games()))
    assert frame["home_rest_days"].tolist() == [3, 2, 2, 2]
    assert frame["home_win_streak"].tolist() == [0, 0, 2, 0]
    assert frame["away_win_streak"].tolist() == [0, 1, 0, 3]


def test_score_only_input_is_accepted_before_elo_update(tmp_path):
    path = tmp_path / "games.csv"
    frame = games().drop(columns="home_win")
    frame.to_csv(path, index=False)
    trainer = EnsembleTrainer(tmp_path / "models")
    features, target = trainer.load_data(path)
    assert target.tolist() == [1, 0, 1, 1]
    assert features.shape == (4, 27)
    assert trainer.training_data["games"] == 4
    assert len(trainer.training_data["source_sha256"]) == 64


def test_unexpected_postgame_columns_are_not_features(tmp_path):
    frame = games()
    frame["home_field_goals_made"] = [40, 25, 38, 43]
    frame["final_result_leak"] = frame["home_win"]
    path = tmp_path / "games.csv"
    frame.to_csv(path, index=False)
    features, _ = EnsembleTrainer(tmp_path / "models").load_data(path)
    assert "home_field_goals_made" not in features
    assert "final_result_leak" not in features
    assert "home_pts" not in features
    assert "home_win" not in features


def test_holdout_rows_do_not_change_training_features(tmp_path):
    frame = games()
    path = tmp_path / "games.csv"
    frame.to_csv(path, index=False)
    trainer = EnsembleTrainer(tmp_path / "models")
    original, y = trainer.load_data(path)
    later = frame.iloc[[0]].copy()
    later["date"] = pd.Timestamp("2025-01-01")
    later["game_id"] = "later"
    pd.concat([later, frame.iloc[::-1]], ignore_index=True).to_csv(path, index=False)
    actual, actual_y = trainer.load_data(path)
    pd.testing.assert_frame_equal(original, actual)
    pd.testing.assert_series_equal(y, actual_y)
    assert trainer.training_data["end_date"] == "2024-01-07"


@pytest.mark.parametrize("mutation", ["disagree", "missing_date", "duplicate", "tie", "same_team"])
def test_invalid_raw_games_fail_before_feature_updates(mutation):
    frame = games()
    if mutation == "disagree":
        frame.loc[0, "home_win"] = 0
    elif mutation == "missing_date":
        frame.loc[0, "date"] = pd.NaT
    elif mutation == "duplicate":
        frame = pd.concat([frame, frame.iloc[[0]]])
    elif mutation == "tie":
        frame.loc[0, "home_pts"] = frame.loc[0, "away_pts"]
    else:
        frame.loc[0, "away"] = frame.loc[0, "home"]
    with pytest.raises(ValueError):
        EnsembleTrainer.prepare_game_rows(frame)


def test_actual_three_model_train_save_reload_and_cli(tmp_path):
    # Synthetic data only: the purpose is model-library/artifact integration.
    rows = 64
    labels = pd.Series(np.tile([0, 1], rows // 2))
    features = pd.DataFrame({"elo_diff": np.where(labels == 1, 1.0, -1.0),
                             "rest_differential": np.tile([0., 1., -1., 2.], rows // 4)})
    model_dir = tmp_path / "models"
    trainer = EnsembleTrainer(model_dir, n_estimators=3, threads=1)
    trainer.feature_names = list(features.columns)
    metrics = trainer.train_all(features, labels, cv_folds=2)
    assert metrics["ensemble"]["evaluation_scope"] == "in_sample_training_diagnostic"
    trainer.save_models()
    predictor = EnsemblePredictor(model_dir)
    expected = trainer.predict_ensemble(features)
    np.testing.assert_allclose(predictor.predict(features), expected)
    assert np.isfinite(expected).all()
    reloaded = EnsembleTrainer(model_dir)
    asyncio.run(reloaded.load_models_async())
    np.testing.assert_allclose(reloaded.predict_ensemble(features), expected)

    snapshot = features.iloc[:2].copy()
    snapshot["game_id"] = ["001", "002"]
    snapshot["date"] = "2024-11-01"
    snapshot["home_team"] = ["AAA", "CCC"]
    snapshot["away_team"] = ["BBB", "DDD"]
    feature_path = tmp_path / "features.csv"
    snapshot.to_csv(feature_path, index=False)
    result = subprocess.run(
        [sys.executable, "scripts/run_daily_predictions.py", "--date", "2024-11-01",
         "--model-dir", str(model_dir), "--features", str(feature_path),
         "--output-dir", str(tmp_path / "output")],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    records = [json.loads(line) for line in
               (tmp_path / "output/2024-11-01.jsonl").read_text().splitlines()]
    assert len(records) == 2
    assert records[0]["game_id"] == "001"
    np.testing.assert_allclose([row["home_win_prob"] for row in records], expected[:2])
