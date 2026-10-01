"""Exercise the API and CLI with synthetic, local-only model artifacts."""

import json
import sys
from datetime import date

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from scripts import run_daily_predictions
from src.common.paths import Paths
from src.services.api import main as api


@pytest.fixture
def prepared(model_dir, monkeypatch):
    artifacts = model_dir.parents[1]
    directory = artifacts / "features"
    directory.mkdir()
    path = directory / "pregame.parquet"
    frame = pd.DataFrame({
        "game_id": ["001", "002", "003"],
        "date": pd.to_datetime(["2024-11-01", "2024-11-01", "2024-11-02"]),
        "home": ["AAA", "CCC", "AAA"], "away": ["BBB", "DDD", "DDD"],
        "elo_diff": [1.0, 3.0, 2.0], "rest_differential": [0.0, 2.0, 1.0],
    })
    frame.to_parquet(path, index=False)
    monkeypatch.setattr(Paths, "MODELS", model_dir.parent)
    monkeypatch.setattr(Paths, "ARTIFACTS", artifacts)
    api._get_predictor.cache_clear()
    yield model_dir, path, frame
    api._get_predictor.cache_clear()


@pytest.fixture
def client(prepared):
    with TestClient(api.app) as client:
        yield client


def test_health_reports_loaded_state_not_file_existence(client):
    assert client.get("/health").json()["models_loaded"] is False
    response = client.get("/predictions", params={"date": "2024-11-01"})
    assert response.status_code == 200
    assert client.get("/health").json()["models_loaded"] is True


def test_predictions_are_dated_json_with_complementary_probabilities(client):
    response = client.get("/predictions", params={"date": "2024-11-01"})
    assert response.status_code == 200
    rows = response.json()
    assert [row["game_id"] for row in rows] == ["001", "002"]
    assert [row["date"] for row in rows] == ["2024-11-01"] * 2
    assert rows[0]["home_win_prob"] == pytest.approx(0.56)
    for row in rows:
        assert row["home_win_prob"] + row["away_win_prob"] == pytest.approx(1)
        assert set(row["top_features"]) == {"elo_diff", "rest_differential"}


@pytest.mark.parametrize("parameters,expected", [
    ({"home_team": "aaa"}, ["001"]),
    ({"away_team": "ddd"}, ["002"]),
    ({"home_team": "AAA", "away_team": "DDD"}, []),
])
def test_independent_team_filters(client, parameters, expected):
    response = client.get("/predictions", params={"date": "2024-11-01", **parameters})
    assert response.status_code == 200
    assert [row["game_id"] for row in response.json()] == expected


@pytest.mark.parametrize("parameters", [
    {"date": "not-a-date"}, {"date": "2024-02-30"},
    {"home_team": ""}, {"away_team": "   "},
])
def test_invalid_request_returns_422(client, parameters):
    assert client.get("/predictions", params=parameters).status_code == 422


def test_absent_date_returns_empty_list_not_other_games(client):
    response = client.get("/predictions", params={"date": "2024-12-01"})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("missing", ["metadata", "model", "features"])
def test_missing_artifacts_return_503_without_leaking_paths(client, prepared, missing):
    model_dir, path, _ = prepared
    target = {"metadata": model_dir / "ensemble_metadata.json",
              "model": model_dir / "cat_model.pkl", "features": path}[missing]
    target.unlink()
    response = client.get("/predictions", params={"date": "2024-11-01"})
    assert response.status_code == 503
    assert str(model_dir) not in response.text
    assert "missing" in response.json()["detail"].lower()


@pytest.mark.parametrize("column", ["date", "home", "elo_diff"])
def test_missing_snapshot_columns_do_not_silently_predict(client, prepared, column):
    _, path, frame = prepared
    frame.drop(columns=column).to_parquet(path, index=False)
    response = client.get("/predictions", params={"date": "2024-11-01"})
    assert response.status_code == 503


def test_duplicate_game_ids_are_rejected(client, prepared):
    _, path, frame = prepared
    frame.loc[1, "game_id"] = "001"
    frame.to_parquet(path, index=False)
    assert client.get("/predictions", params={"date": "2024-11-01"}).status_code == 503


def test_unexpected_error_details_remain_private(client, monkeypatch):
    def fail(*args):
        raise RuntimeError("private-server-path-and-details")

    monkeypatch.setattr(api, "_predict", fail)
    response = client.get("/predictions", params={"date": "2024-11-01"})
    assert response.status_code == 500
    assert "private-server" not in response.text


def test_cli_writes_timestamp_safe_jsonl(prepared, tmp_path, monkeypatch):
    model_dir, path, _ = prepared
    output = tmp_path / "predictions"
    monkeypatch.setattr(sys, "argv", ["run_daily_predictions.py", "--date", "2024-11-01",
                                     "--features", str(path), "--model-dir", str(model_dir),
                                     "--output-dir", str(output)])
    assert run_daily_predictions.main() == 0
    rows = [json.loads(line) for line in (output / "2024-11-01.jsonl").read_text().splitlines()]
    assert len(rows) == 2
    assert rows[0]["date"] == "2024-11-01"
    assert rows[0]["game_id"] == "001"
    assert rows[0]["created_at"].endswith("+00:00")


def test_cli_fails_clearly_when_features_are_missing(prepared, tmp_path, monkeypatch):
    model_dir, _, _ = prepared
    monkeypatch.setattr(sys, "argv", ["run_daily_predictions.py", "--date", "2024-11-01",
                                     "--features", str(tmp_path / "absent.parquet"),
                                     "--model-dir", str(model_dir)])
    assert run_daily_predictions.main() == 1


def test_save_does_not_mutate_caller_records(tmp_path):
    records = [{"game_id": "001", "date": "2024-11-01", "home_win_prob": 0.5}]
    original = json.loads(json.dumps(records))
    run_daily_predictions.save_predictions(records, date(2024, 11, 1), tmp_path)
    assert records == original
