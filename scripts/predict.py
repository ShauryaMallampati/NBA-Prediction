#!/usr/bin/env python3
"""Predict upcoming games with a trained ensemble.

The model needs pregame features, and those features are a function of every game
that came before. So this script replays the historical game log through
`RunningWorldState` to bring team state up to the prediction date, then asks the
ensemble for a win probability for each requested matchup.

Usage:
    python scripts/predict.py --games upcoming.csv
    python scripts/predict.py --home BOS --away LAL --date 2025-01-15

`--games` expects a CSV with columns: date, home, away (game_id optional).
Team names must match the names in the historical game log.

Outputs JSON Lines to stdout, or to --out.
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.features import RunningWorldState, sort_games_chronologically
from src.common.logger import setup_logger
from src.models.pregame.predictor import EnsemblePredictor

logger = setup_logger("predict")

DEFAULT_HISTORY = Path("data/nba_games_enhanced.csv")
DEFAULT_MODEL_DIR = Path("artifacts/models/pregame")


def load_history(path: Path) -> pd.DataFrame:
    """Load the historical game log used to warm up team state."""
    if not path.exists():
        raise FileNotFoundError(
            f"No game log at {path}. Build one first:\n"
            "  1. download the Kaggle 'wyattowalsh/basketball' dataset into data/kaggle_nba/\n"
            "  2. python scripts/data_prep/process_kaggle_games.py"
        )

    df = pd.read_csv(path)
    required = {"date", "home", "away", "home_win"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing required column(s): {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"])
    return sort_games_chronologically(df)


def warm_up_state(history: pd.DataFrame, until: pd.Timestamp) -> RunningWorldState:
    """Replay every completed game strictly before `until` into a fresh state.

    The strict inequality is the whole point: a game on the prediction date is
    never fed into the state that predicts it.
    """
    state = RunningWorldState()
    past = history[history["date"] < until]

    for row in past.itertuples(index=False):
        state.update(
            row.home,
            row.away,
            row.date,
            row.home_win,
            getattr(row, "home_pts", None),
            getattr(row, "away_pts", None),
        )

    logger.info(f"Warmed up on {len(past)} games before {until.date()}")
    return state


def build_fixtures(args: argparse.Namespace) -> pd.DataFrame:
    """Assemble the matchups to predict, from --games or from --home/--away."""
    if args.games:
        fixtures = pd.read_csv(args.games)
        missing = {"date", "home", "away"} - set(fixtures.columns)
        if missing:
            raise ValueError(f"{args.games} is missing column(s): {sorted(missing)}")
    else:
        if not (args.home and args.away and args.date):
            raise ValueError("Provide --games, or all of --home, --away and --date.")
        fixtures = pd.DataFrame([{"date": args.date, "home": args.home, "away": args.away}])

    fixtures["date"] = pd.to_datetime(fixtures["date"])
    return fixtures.sort_values("date").reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Predict NBA game winners before tip-off")
    parser.add_argument("--games", type=Path, help="CSV of upcoming games (date,home,away)")
    parser.add_argument("--home", help="Home team, for a single-game prediction")
    parser.add_argument("--away", help="Away team, for a single-game prediction")
    parser.add_argument("--date", help="Game date YYYY-MM-DD, for a single-game prediction")
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY,
                        help=f"Historical game log (default: {DEFAULT_HISTORY})")
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR,
                        help=f"Trained model directory (default: {DEFAULT_MODEL_DIR})")
    parser.add_argument("--out", type=Path, help="Write JSON Lines here instead of stdout")
    args = parser.parse_args()

    fixtures = build_fixtures(args)
    history = load_history(args.history)
    predictor = EnsemblePredictor(str(args.model_dir))

    # One warm-up per distinct date, replaying history up to that date.
    records = []
    for date, day_games in fixtures.groupby("date"):
        state = warm_up_state(history, date)
        rows = [
            state.get_team_features(g.home, g.away, date)
            for g in day_games.itertuples(index=False)
        ]
        probabilities = predictor.predict(pd.DataFrame(rows))

        for game, prob in zip(day_games.itertuples(index=False), probabilities):
            records.append({
                "game_id": getattr(game, "game_id", f"{date.date()}_{game.away}_at_{game.home}"),
                "date": str(date.date()),
                "home": game.home,
                "away": game.away,
                "home_win_prob": round(float(prob), 4),
                "away_win_prob": round(float(1 - prob), 4),
                "predicted_winner": game.home if prob > 0.5 else game.away,
            })

    lines = "\n".join(json.dumps(r) for r in records)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(lines + "\n")
        logger.info(f"Wrote {len(records)} prediction(s) to {args.out}")
    else:
        print(lines)

    return 0


if __name__ == "__main__":
    sys.exit(main())
