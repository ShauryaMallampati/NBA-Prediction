"""Nothing in the pipeline may learn from a game that has not happened yet."""

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import pytest
from sklearn.model_selection import TimeSeriesSplit

from src.common.features import RunningWorldState, sort_games_chronologically

from .conftest import TinyTrainer, make_game_log


def _load_script(name: str, relative_path: str):
    """Import a scripts/ entry point, which is not part of the src package."""
    path = Path(__file__).parent.parent / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


predict_script = _load_script("predict_script", "scripts/predict.py")


def test_timeseries_folds_never_train_on_a_later_game(game_log):
    """Every training index must precede every validation index in its fold."""
    splitter = TimeSeriesSplit(n_splits=5)

    folds = list(splitter.split(range(len(game_log))))
    assert len(folds) == 5

    for train_idx, val_idx in folds:
        assert len(train_idx) and len(val_idx)
        assert max(train_idx) < min(val_idx)


def test_prepared_features_stay_in_date_order():
    """Row i of the training matrix must correspond to the i-th game by date.

    `make_game_log` emits games already in chronological order, so the generation
    order is the expected order — it does not come from the sorting code itself.
    `day_of_week` is computed straight from the game date and gives an
    independent read on which game each row came from.
    """
    log = make_game_log(n_games=700, seed=11)
    assert log["date"].is_monotonic_increasing, "fixture must already be in date order"

    trainer = TinyTrainer(output_dir="/tmp/unused-ordering-check")
    X, y = trainer.prepare_features_from_games(log, cutoff_date="2100-01-01")

    expected = log.iloc[500:]

    assert len(X) == len(expected)
    assert list(X["day_of_week"]) == [float(d) for d in expected["date"].dt.dayofweek]
    assert list(y) == list(expected["home_win"])


def test_replay_order_does_not_depend_on_how_the_log_was_filtered():
    """Same-date games must be replayed in one fixed order, not an arbitrary one.

    Sorting a filtered frame and filtering a sorted frame have to agree, or the
    features of later same-day games shift between runs.
    """
    log = make_game_log(n_games=400, seed=17)
    shuffled = log.sample(frac=1.0, random_state=3)
    midpoint = log["date"].iloc[200]

    sorted_then_filtered = sort_games_chronologically(shuffled)
    sorted_then_filtered = sorted_then_filtered[sorted_then_filtered["date"] < midpoint]
    filtered_then_sorted = sort_games_chronologically(shuffled[shuffled["date"] < midpoint])

    assert list(sorted_then_filtered["game_id"]) == list(filtered_then_sorted["game_id"])
    # And that fixed order is the order the games were generated in.
    assert list(filtered_then_sorted["game_id"]) == list(log[log["date"] < midpoint]["game_id"])


def test_games_after_the_cutoff_never_reach_the_training_matrix():
    """Appending later games must leave the training matrix untouched."""
    log = make_game_log(n_games=700, seed=13)
    cutoff = log["date"].iloc[600]

    before = log[log["date"] < cutoff].copy()
    trainer = TinyTrainer(output_dir="/tmp/unused-cutoff-check")

    X_truncated, y_truncated = trainer.prepare_features_from_games(
        before, cutoff_date=str(cutoff.date())
    )
    X_full, y_full = trainer.prepare_features_from_games(
        log, cutoff_date=str(cutoff.date())
    )

    pd.testing.assert_frame_equal(X_truncated, X_full)
    assert list(y_truncated) == list(y_full)


def test_warm_up_state_excludes_games_on_the_prediction_date():
    """Warm-up is strictly before the prediction date, so same-day games cannot leak."""
    history = pd.DataFrame([
        {"date": pd.Timestamp("2024-01-02"), "home": "ALB", "away": "BOU",
         "home_win": 1, "home_pts": 110, "away_pts": 101},
        {"date": pd.Timestamp("2024-01-09"), "home": "BOU", "away": "DEN",
         "home_win": 1, "home_pts": 130, "away_pts": 90},
        # Same day as the prediction, and afterwards: must be ignored.
        {"date": pd.Timestamp("2024-01-10"), "home": "BOU", "away": "CAL",
         "home_win": 0, "home_pts": 80, "away_pts": 120},
        {"date": pd.Timestamp("2024-01-14"), "home": "DEN", "away": "BOU",
         "home_win": 1, "home_pts": 125, "away_pts": 95},
    ])
    prediction_date = pd.Timestamp("2024-01-10")

    from_full = predict_script.warm_up_state(history, prediction_date)
    from_past_only = predict_script.warm_up_state(
        history[history["date"] < prediction_date].copy(), prediction_date
    )

    assert (from_full.get_team_features("BOU", "DEN", prediction_date)
            == from_past_only.get_team_features("BOU", "DEN", prediction_date))


def test_warm_up_state_uses_the_games_before_the_prediction_date():
    """The complement of the test above: earlier games must be consumed."""
    history = pd.DataFrame([
        {"date": pd.Timestamp("2024-01-02"), "home": "ALB", "away": "BOU",
         "home_win": 1, "home_pts": 110, "away_pts": 101},
        {"date": pd.Timestamp("2024-01-09"), "home": "BOU", "away": "DEN",
         "home_win": 1, "home_pts": 130, "away_pts": 90},
    ])
    prediction_date = pd.Timestamp("2024-01-10")

    warmed = predict_script.warm_up_state(history, prediction_date)
    cold = RunningWorldState()

    assert (warmed.get_team_features("BOU", "DEN", prediction_date)
            != cold.get_team_features("BOU", "DEN", prediction_date))
