"""Synthetic fixtures verify software behavior, not NBA prediction accuracy."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scripts.evaluate_release import digest as file_sha256
from scripts.evaluate_release import evaluate, metrics as probability_metrics
from src.models.pregame.predictor import EnsemblePredictor
from src.models.pregame.train_ensemble import EnsembleTrainer


@pytest.fixture
def games():
    count = 100
    dates = pd.date_range(pd.Timestamp("2024-10-01") - pd.Timedelta(days=80), periods=count)
    rng = np.random.default_rng(431)
    away_scores = rng.integers(80, 120, count)
    margins = rng.integers(1, 20, count) * np.where(np.arange(count) % 2, 1, -1)
    teams = ["Alpha", "Beta", "Gamma", "Delta"]
    return pd.DataFrame({
        "game_id": [f"fixture-{index:04d}" for index in range(count)],
        "date": dates,
        "home": [teams[index % 4] for index in range(count)],
        "away": [teams[(index + 1) % 4] for index in range(count)],
        "home_pts": away_scores + margins,
        "away_pts": away_scores,
    })


def test_current_and_future_outcomes_cannot_change_pregame_features(games, tmp_path):
    trainer = EnsembleTrainer(tmp_path)
    before = trainer.engineer_game_rows(games)
    changed = games.copy()
    changed.loc[30:, ["home_pts", "away_pts"]] = games.loc[
        30:, ["away_pts", "home_pts"]].to_numpy()
    after = trainer.engineer_game_rows(changed)
    pd.testing.assert_frame_equal(before.loc[:30, trainer.FEATURE_NAMES],
                                  after.loc[:30, trainer.FEATURE_NAMES])
    assert not before.loc[31:, trainer.FEATURE_NAMES].equals(
        after.loc[31:, trainer.FEATURE_NAMES])


def test_training_cutoff_and_allowlisted_features(games, tmp_path):
    games["actual_box_score_leak"] = games["home_pts"]
    path = tmp_path / "games.csv"
    games.to_csv(path, index=False)
    trainer = EnsembleTrainer(tmp_path / "models")
    features, labels = trainer.load_data(path)
    assert len(features) == len(labels) == 80
    assert list(features.columns) == trainer.FEATURE_NAMES
    assert "actual_box_score_leak" not in features
    assert trainer.training_data["end_date"] == "2024-09-30"
    assert trainer.training_data["source_sha256"] == file_sha256(path)
    assert features.iloc[0]["home_win_streak"] == 0
    assert features.iloc[0]["home_pts_avg_l10"] == 100


def test_cross_validation_keeps_complete_dates_together(games, tmp_path):
    other = games.copy()
    other["game_id"] += "-other"
    other["home"] += "-other"
    other["away"] += "-other"
    path = tmp_path / "games.csv"
    pd.concat([games, other]).to_csv(path, index=False)
    trainer = EnsembleTrainer(tmp_path / "models")
    features, labels = trainer.load_data(path)
    for train, validation in trainer._temporal_splits(features, labels, 3):
        assert trainer.training_dates[train].max() < trainer.training_dates[validation].min()
        assert len(train) % 2 == len(validation) % 2 == 0


@pytest.mark.parametrize("kind", ["duplicate", "same_team_date", "missing_team", "empty_team",
                                 "infinite_score", "tie", "wrong_label", "missing_date"])
def test_invalid_completed_games_are_rejected(games, kind):
    if kind == "duplicate":
        games = pd.concat([games, games.iloc[[0]]])
    elif kind == "same_team_date":
        games.loc[1, "date"] = games.loc[0, "date"]
        games.loc[1, "home"] = games.loc[0, "home"]
    elif kind == "missing_team":
        games.loc[0, "home"] = None
    elif kind == "empty_team":
        games.loc[0, "home"] = " "
    elif kind == "infinite_score":
        games = games.astype({"home_pts": float})
        games.loc[0, "home_pts"] = np.inf
    elif kind == "tie":
        games.loc[0, "home_pts"] = games.loc[0, "away_pts"]
    elif kind == "wrong_label":
        games["home_win"] = (games["home_pts"] < games["away_pts"]).astype(int)
    else:
        games.loc[0, "date"] = pd.NaT
    with pytest.raises(ValueError):
        EnsembleTrainer.prepare_game_rows(games)


def test_metrics_have_known_values_and_single_class_auc_is_explicit():
    result = probability_metrics([0, 1], [0.25, 0.75])
    assert result["accuracy"] == 1
    assert result["roc_auc"] == 1
    assert result["brier_score"] == pytest.approx(0.0625)
    assert probability_metrics([1, 1], [0.5, 0.9])["roc_auc"] is None


@pytest.mark.parametrize("labels,probabilities", [([], []), ([0], [0.1, 0.2]),
                                                  ([2], [0.4]), ([1], [np.nan]),
                                                  ([0], [-0.1]), ([0], [1.1])])
def test_metrics_reject_invalid_inputs(labels, probabilities):
    with pytest.raises(ValueError):
        probability_metrics(labels, probabilities)


def test_real_estimators_train_reload_evaluate_and_cli(games, tmp_path, monkeypatch):
    """Exercise all three installed ML libraries without external services/data."""
    source = tmp_path / "synthetic-games.csv"
    models = tmp_path / "models"
    games.to_csv(source, index=False)
    trainer = EnsembleTrainer(models, n_estimators=3, threads=1)
    features, labels = trainer.load_data(source)
    trainer.train_all(features, labels, cv_folds=3)
    trainer.save_models()
    predictor = EnsemblePredictor(models)
    np.testing.assert_allclose(predictor.predict(features), trainer.predict_ensemble(features))
    hashes = {path.name: file_sha256(path) for path in models.iterdir()}

    def no_training(*args, **kwargs):
        raise AssertionError("Evaluation must not fit a model")

    monkeypatch.setattr(EnsembleTrainer, "train_all", no_training)
    report = evaluate(source, models, "2024-10-01", "2024-10-20")
    assert report["games"] == 20
    assert report["start_date"] == "2024-10-01"
    assert report["training_data"]["games"] == 80
    assert hashes == {path.name: file_sha256(path) for path in models.iterdir()}
    assert evaluate(source, models, "2024-10-01", "2024-10-20", report["input_sha256"]) == report
    with pytest.raises(ValueError, match="after training"):
        evaluate(source, models, "2024-09-01", "2024-10-20")
    with pytest.raises(ValueError, match="No completed games"):
        evaluate(source, models, "2030-01-01", "2030-02-01")
    different_source = tmp_path / "different.csv"
    different_source.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="SHA-256"):
        evaluate(different_source, models, "2024-10-01", "2024-10-20", report["input_sha256"])
    root = Path(__file__).resolve().parents[1]
    report_path = tmp_path / "cli-summary.json"
    run = subprocess.run([
        sys.executable, str(root / "scripts/evaluate_release.py"), "--games", str(source),
        "--model-dir", str(models), "--start", "2024-10-01", "--end", "2024-10-20",
        "--output", str(report_path),
    ], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)["games"] == 20
    assert json.loads(report_path.read_text()) == report
