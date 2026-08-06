#!/usr/bin/env python3
"""Walk-forward evaluation of a trained ensemble on games after the training cutoff.

This is the only honest out-of-sample number the project produces. It walks the
holdout games in date order: features for a game are computed from state that
contains only earlier games, the model predicts, and only then is the actual
result folded into the state. No holdout result ever informs a prediction that
precedes it.

Usage:
    python scripts/eval/evaluate_holdout.py
    python scripts/eval/evaluate_holdout.py --start 2024-10-01 --end 2025-07-01
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score

from src.common.features import RunningWorldState, sort_games_chronologically
from src.common.logger import setup_logger
from src.models.pregame.predictor import EnsemblePredictor

logger = setup_logger("evaluate_holdout")

DEFAULT_HISTORY = Path("data/nba_games_enhanced.csv")
DEFAULT_MODEL_DIR = Path("artifacts/models/pregame")

# Must match the cutoff_date used in EnsembleTrainerV2.prepare_features_from_games,
# otherwise the "holdout" contains games the model trained on.
TRAINING_CUTOFF = "2024-10-01"


def evaluate(history: pd.DataFrame, predictor: EnsemblePredictor,
             start: str, end: str) -> dict:
    """Predict every game in [start, end) in chronological order."""
    start_ts, end_ts = pd.Timestamp(start), pd.Timestamp(end)

    state = RunningWorldState()
    for row in history[history["date"] < start_ts].itertuples(index=False):
        state.update(row.home, row.away, row.date, row.home_win,
                     getattr(row, "home_pts", None), getattr(row, "away_pts", None))

    holdout = history[(history["date"] >= start_ts) & (history["date"] < end_ts)]
    if holdout.empty:
        raise ValueError(f"No games found in [{start}, {end}).")

    probabilities, actuals = [], []
    for row in holdout.itertuples(index=False):
        features = state.get_team_features(row.home, row.away, row.date)
        prob = predictor.predict(pd.DataFrame([features]))[0]

        probabilities.append(float(prob))
        actuals.append(int(row.home_win))

        # Result folded in only after the prediction is recorded.
        state.update(row.home, row.away, row.date, row.home_win,
                     getattr(row, "home_pts", None), getattr(row, "away_pts", None))

    probabilities = np.asarray(probabilities)
    actuals = np.asarray(actuals)
    predicted = (probabilities > 0.5).astype(int)

    return {
        "games": int(len(actuals)),
        "window": f"{start} to {end}",
        "accuracy": float(accuracy_score(actuals, predicted)),
        "auc": float(roc_auc_score(actuals, probabilities)),
        "log_loss": float(log_loss(actuals, probabilities)),
        "brier": float(brier_score_loss(actuals, probabilities)),
        "home_win_rate": float(actuals.mean()),
        "always_pick_home_accuracy": float(max(actuals.mean(), 1 - actuals.mean())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Walk-forward holdout evaluation")
    parser.add_argument("--start", default=TRAINING_CUTOFF,
                        help=f"First holdout date, inclusive (default: {TRAINING_CUTOFF})")
    parser.add_argument("--end", default="2100-01-01", help="Last holdout date, exclusive")
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    args = parser.parse_args()

    if not args.history.exists():
        raise FileNotFoundError(
            f"No game log at {args.history}. Run scripts/data_prep/process_kaggle_games.py first."
        )

    if pd.Timestamp(args.start) < pd.Timestamp(TRAINING_CUTOFF):
        logger.warning(
            f"--start {args.start} is before the training cutoff {TRAINING_CUTOFF}. "
            "Results will include games the model was trained on and will be optimistic."
        )

    history = pd.read_csv(args.history)
    history["date"] = pd.to_datetime(history["date"])
    history = sort_games_chronologically(history)

    predictor = EnsemblePredictor(str(args.model_dir))
    results = evaluate(history, predictor, args.start, args.end)

    print("=" * 60)
    print("HOLDOUT EVALUATION (walk-forward, out-of-sample)")
    print("=" * 60)
    print(f"  Window:                 {results['window']}")
    print(f"  Games:                  {results['games']}")
    print(f"  Accuracy:               {results['accuracy']:.4f}")
    print(f"  AUC:                    {results['auc']:.4f}")
    print(f"  Log loss:               {results['log_loss']:.4f}")
    print(f"  Brier score:            {results['brier']:.4f}")
    print(f"  Home win rate:          {results['home_win_rate']:.4f}")
    print(f"  Always-pick-home acc.:  {results['always_pick_home_accuracy']:.4f}  (baseline)")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
