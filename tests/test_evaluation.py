"""Evaluation-contract tests use a synthetic snapshot, not NBA results."""

import json
import pickle

import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier

from scripts.evaluate_release import evaluate, metrics


@pytest.fixture
def evaluation_inputs(model_dir, tmp_path):
    metadata_path = model_dir / "ensemble_metadata.json"
    metadata = json.loads(metadata_path.read_text())
    metadata["training_data"] = {"start_date": "2024-09-28", "end_date": "2024-09-30",
                                 "home_win_rate": 0.5}
    metadata_path.write_text(json.dumps(metadata))
    model = DummyClassifier(strategy="prior").fit(
        pd.DataFrame({"elo_diff": [0., 1.], "rest_differential": [0., 1.]}), [0, 1]
    )
    for name in ("xgb", "lgb", "cat"):
        with (model_dir / f"{name}_model.pkl").open("wb") as handle:
            pickle.dump(model, handle)
    raw = pd.DataFrame({
        "game_id": ["a", "b", "c", "d"],
        "date": ["2024-09-28", "2024-09-30", "2024-10-01", "2024-10-03"],
        "home": ["AAA", "BBB", "AAA", "BBB"],
        "away": ["BBB", "AAA", "BBB", "AAA"],
        "home_pts": [110, 90, 110, 90], "away_pts": [100, 100, 100, 100],
    })
    path = tmp_path / "history.csv"
    raw.to_csv(path, index=False)
    return path, model_dir, raw


def test_repeated_evaluation_has_identical_results_and_hashes(evaluation_inputs):
    path, model_dir, _ = evaluation_inputs
    first = evaluate(path, model_dir, "2024-10-01", "2024-10-03")
    second = evaluate(path, model_dir, "2024-10-01", "2024-10-03", first["input_sha256"])
    assert first == second
    assert first["games"] == 2
    assert first["ensemble"]["accuracy"] == pytest.approx(0.5)
    assert first["ensemble"]["roc_auc"] == pytest.approx(0.5)
    assert first["ensemble"]["brier_score"] == pytest.approx(0.25)
    assert len(first["model_sha256"]) == 4
    assert "pregame_elo" in first["baselines"]


@pytest.mark.parametrize("start,end", [
    ("2024-09-30", "2024-10-03"), ("2024-10-03", "2024-10-01"),
    ("2025-01-01", "2025-01-02"),
])
def test_overlapping_reversed_and_empty_windows_are_rejected(evaluation_inputs, start, end):
    path, model_dir, _ = evaluation_inputs
    with pytest.raises(ValueError):
        evaluate(path, model_dir, start, end)


def test_wrong_snapshot_hash_is_rejected(evaluation_inputs):
    path, model_dir, _ = evaluation_inputs
    with pytest.raises(ValueError, match="SHA-256"):
        evaluate(path, model_dir, "2024-10-01", "2024-10-03", "0" * 64)


def test_missing_training_provenance_is_not_assumed(evaluation_inputs):
    path, model_dir, _ = evaluation_inputs
    metadata_path = model_dir / "ensemble_metadata.json"
    metadata = json.loads(metadata_path.read_text())
    del metadata["training_data"]
    metadata_path.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="training_data"):
        evaluate(path, model_dir, "2024-10-01", "2024-10-03")


def test_missing_warmup_history_is_rejected(evaluation_inputs):
    path, model_dir, frame = evaluation_inputs
    frame.iloc[2:].to_csv(path, index=False)
    with pytest.raises(ValueError, match="training-period history"):
        evaluate(path, model_dir, "2024-10-01", "2024-10-03")


def test_single_class_auc_is_explicitly_undefined():
    result = metrics([1, 1], [0.7, 0.8])
    assert result["roc_auc"] is None
    assert result["brier_score"] == pytest.approx(0.065)
    json.dumps(result, allow_nan=False)
