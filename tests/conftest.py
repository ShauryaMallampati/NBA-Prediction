"""Shared fixtures.

The synthetic game log here is generated from a fixed seed and a latent team
strength, so it behaves like a real season schedule: teams have different
quality, home teams win somewhat more often, and games arrive in date order.
That is enough for the models to learn something and for the leakage and
ordering tests to be meaningful.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.pregame.train_ensemble_v2 import EnsembleTrainerV2

TEAMS = ["ALB", "BOU", "CAL", "DEN", "ELM", "FAR", "GRE", "HAV", "IRV", "JAC"]

# Latent quality per team; drives who tends to win. Not visible to the model.
TEAM_STRENGTH = {team: 0.30 + 0.06 * i for i, team in enumerate(TEAMS)}

HOME_EDGE = 0.06


def make_game_log(n_games: int = 1200, seed: int = 7,
                  start: str = "2015-10-20") -> pd.DataFrame:
    """Build a deterministic synthetic game log in the trainer's input format."""
    rng = np.random.default_rng(seed)
    date = pd.Timestamp(start)
    rows = []

    for i in range(n_games):
        home, away = rng.choice(TEAMS, size=2, replace=False)
        p_home = np.clip(
            0.5 + (TEAM_STRENGTH[home] - TEAM_STRENGTH[away]) + HOME_EDGE, 0.05, 0.95
        )
        home_win = int(rng.random() < p_home)

        base = 105
        spread = rng.integers(3, 22)
        home_pts = base + (spread if home_win else 0) + int(rng.integers(0, 12))
        away_pts = base + (0 if home_win else spread) + int(rng.integers(0, 12))

        rows.append({
            "date": date,
            "game_id": f"g{i:05d}",
            "home": home,
            "away": away,
            "home_pts": home_pts,
            "away_pts": away_pts,
            "home_win": home_win,
            "margin": home_pts - away_pts,
        })

        # Roughly three games per calendar day.
        if i % 3 == 2:
            date += pd.Timedelta(days=1)

    return pd.DataFrame(rows)


class TinyTrainer(EnsembleTrainerV2):
    """The real trainer with cheap hyperparameters, so tests finish quickly.

    Only the model sizes change. Feature construction, chronological CV,
    calibration, stacking and the saved artifact format are the production code.
    """

    def _get_xgb_params(self) -> dict:
        params = super()._get_xgb_params()
        params.update(n_estimators=15, max_depth=3)
        return params

    def _get_lgb_params(self) -> dict:
        params = super()._get_lgb_params()
        params.update(n_estimators=15, num_leaves=7, min_child_samples=5)
        return params

    def _get_cat_params(self) -> dict:
        params = super()._get_cat_params()
        params.update(iterations=15, depth=3)
        return params

    def _get_et_params(self) -> dict:
        params = super()._get_et_params()
        params.update(n_estimators=15, max_depth=5)
        return params


@pytest.fixture(scope="session")
def game_log() -> pd.DataFrame:
    """A synthetic game log covering enough games to clear the 500-game warmup."""
    return make_game_log()


@pytest.fixture(scope="session")
def trained_model_dir(tmp_path_factory, game_log) -> Path:
    """Train a real (small) ensemble and return the directory it was saved to."""
    out = tmp_path_factory.mktemp("models") / "pregame"
    trainer = TinyTrainer(output_dir=str(out))

    X, y = trainer.prepare_features_from_games(game_log, cutoff_date="2100-01-01")
    trainer.train_all(X, y, cv_folds=3)
    trainer.save_models()

    return out
