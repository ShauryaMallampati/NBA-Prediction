"""The pregame feature schema must contain nothing that is known only after tip-off."""

import pandas as pd
import pytest

from src.common.features import (
    LEAKAGE_COLUMNS,
    LeakageError,
    RunningWorldState,
    assert_no_leakage,
)

# Named explicitly rather than looped over LEAKAGE_COLUMNS, so that shrinking
# LEAKAGE_COLUMNS cannot quietly shrink this test too.
FORBIDDEN = [
    "home_score",
    "away_score",
    "home_pts",
    "away_pts",
    "score_diff",
    "margin",
    "total_pts",
    "home_win",
    "away_win",
    "winner",
    "outcome",
    "final_score",
]


@pytest.fixture
def feature_names():
    state = RunningWorldState()
    return list(state.get_team_features("ALB", "BOU", pd.Timestamp("2024-01-15")))


@pytest.mark.parametrize("column", FORBIDDEN)
def test_schema_excludes_outcome_column(feature_names, column):
    assert column not in feature_names


def test_schema_passes_the_leakage_guard(feature_names):
    assert_no_leakage(feature_names)


@pytest.mark.parametrize("column", FORBIDDEN)
def test_leakage_guard_rejects_each_outcome_column(feature_names, column):
    with pytest.raises(LeakageError) as excinfo:
        assert_no_leakage(feature_names + [column])
    assert column in str(excinfo.value)


def test_leakage_guard_names_every_offender():
    with pytest.raises(LeakageError) as excinfo:
        assert_no_leakage(["elo_diff", "home_score", "away_score"])
    message = str(excinfo.value)
    assert "home_score" in message and "away_score" in message
    assert "elo_diff" not in message


def test_leakage_columns_cover_the_documented_names():
    assert set(FORBIDDEN) <= LEAKAGE_COLUMNS


def test_feature_order_is_deterministic():
    """Two states at the same point in history must agree on names and order."""
    log = [
        ("ALB", "BOU", "2024-01-02", 1, 110, 101),
        ("CAL", "DEN", "2024-01-03", 0, 98, 107),
        ("ALB", "CAL", "2024-01-05", 1, 115, 99),
    ]

    def build():
        state = RunningWorldState()
        for home, away, date, won, hp, ap in log:
            state.update(home, away, pd.Timestamp(date), won, hp, ap)
        return state.get_team_features("BOU", "DEN", pd.Timestamp("2024-01-10"))

    first, second = build(), build()

    assert list(first) == list(second)
    assert first == second


def test_state_reflects_every_game_it_is_given():
    """Guard against the ordering tests passing for the wrong reason.

    If feeding extra results into the state changed nothing, the chronology tests
    in test_chronology.py would be vacuous. This asserts the state is in fact
    sensitive to the games it consumes.
    """
    def features_after(history):
        state = RunningWorldState()
        for home, away, date, won, hp, ap in history:
            state.update(home, away, pd.Timestamp(date), won, hp, ap)
        return state.get_team_features("BOU", "DEN", pd.Timestamp("2024-02-01"))

    base = [("ALB", "BOU", "2024-01-02", 1, 110, 101)]
    more = base + [
        ("BOU", "DEN", "2024-01-20", 1, 130, 90),
        ("BOU", "CAL", "2024-01-22", 1, 128, 95),
    ]

    assert features_after(base) != features_after(more)
