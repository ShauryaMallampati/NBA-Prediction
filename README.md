# NBA Game Predictor

A chronological pregame NBA winner-prediction pipeline using tabular
team-performance features and an ensemble of tree-based models.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Given two teams and a date, it returns the home team's win probability using only
information available before tip-off.

## What's in this release

**Models** — four base models trained on the same 80 features, stacked by a
logistic-regression meta-learner:

| Model | Why it's in there |
| --- | --- |
| XGBoost | gradient boosting |
| LightGBM | leaf-wise boosting |
| CatBoost | ordered boosting |
| ExtraTrees | randomised bagging, to decorrelate the three boosters |

**Features** — 80 columns, all derived from past games by a single incremental
state machine (`RunningWorldState`): Elo and margin-adjusted Elo, rolling win
percentages and scoring over 5/10/20-game windows, Pythagorean expectation,
strength of schedule, recent-form trends, rest and back-to-backs, streaks,
head-to-head history, calendar context, and head-to-head differentials.

**Evaluation** — chronological throughout. `TimeSeriesSplit` for cross-validation,
a fixed date cutoff separating training from holdout seasons, and a walk-forward
holdout evaluation that predicts each game before folding in its result.

**Calibration** — isotonic regression (`CalibratedClassifierCV`, fitted with a
chronological CV) on every base model before it is saved.

The same feature function runs at training time and at prediction time, so there
is no separate serving path that can drift.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full breakdown, including
what stops future information from entering a feature.

## A note on earlier versions

Earlier versions of this project experimented with highlight video, crowd audio, a
momentum sequence model, player-relationship features, and multimodal fusion.
Those components were removed from the public release: evaluated against the
tabular baseline, they did not change enough decisions to justify their
complexity. They remain in the git history. Nothing in this release depends on
them, and no claim here rests on measurements of them.

## Performance

Walk-forward evaluation on the 2024-25 season, which is after the `2024-10-01`
training cutoff and was never trained on:

| Metric | Value |
| --- | --- |
| Games | 1,383 |
| Accuracy | **65.2%** |
| AUC | 0.708 |
| Log loss | 0.621 |
| Brier score | 0.216 |
| Always-pick-the-home-team baseline | 54.9% |

This was produced by `scripts/eval/evaluate_holdout.py` in this repository, on
trained artifacts and a full game log that are **not** included here (see
[REPRODUCIBILITY.md](REPRODUCIBILITY.md)). Historical evaluation placed the system
in the mid-60% range, but trained model artifacts and full datasets are not
included in this repository, so you cannot reproduce that exact number from a
fresh clone. You can reproduce the *method*: download the public dataset, retrain,
and evaluate on your own holdout. Your number will differ.

The training run also reports training-period cross-validation accuracies
(64.4%–65.9% per base model). Those are in-training-period numbers and are not
comparable to the holdout figure above.

## Installation

Requires Python 3.10+. No GPU.

```bash
git clone https://github.com/ShauryaMallampati/NBA-Prediction.git
cd NBA-Prediction
poetry install
```

Or without Poetry:

```bash
pip install numpy pandas scikit-learn xgboost lightgbm catboost pytest
```

## Getting the data

The repository ships no game data. Training needs a game log at
`data/nba_games_enhanced.csv`.

1. Download the [Kaggle basketball dataset](https://www.kaggle.com/datasets/wyattowalsh/basketball)
   and put `Games.csv` in `data/kaggle_nba/`.
2. Convert it:

```bash
poetry run python scripts/data_prep/process_kaggle_games.py
```

Any CSV with the columns `date, game_id, home, away, home_pts, away_pts, home_win`
works, so you can substitute your own source.

## Training

```bash
poetry run python scripts/training/train_ensemble_v2.py
```

Trains the four base models with chronological cross-validation, calibrates them,
fits the meta-learner, and writes seven artifacts to `artifacts/models/pregame/`.
Expect this to take a while on a full historical log, and expect the ExtraTrees
artifact to be a few hundred MB.

## Prediction

Prediction requires trained artifacts — they are not distributed with this
repository, so run the training step first. Without them the predictor raises
`MissingArtifactsError` naming each missing file.

```bash
# one game
poetry run python scripts/predict.py --home Lakers --away Celtics --date 2025-01-15

# a slate, from a CSV with columns date,home,away
poetry run python scripts/predict.py --games upcoming.csv --out predictions.jsonl
```

Output is JSON Lines:

```json
{"game_id": "2025-01-15_Celtics_at_Lakers", "date": "2025-01-15", "home": "Lakers", "away": "Celtics", "home_win_prob": 0.3935, "away_win_prob": 0.6065, "predicted_winner": "Celtics"}
```

Team names must match the names in your game log.

From Python:

```python
from src.models.pregame.predictor import EnsemblePredictor

predictor = EnsemblePredictor("artifacts/models/pregame")
probabilities = predictor.predict(features_df)  # features_df from RunningWorldState
```

## Evaluation

```bash
poetry run python scripts/eval/evaluate_holdout.py
```

Walks the holdout period in date order, predicting each game before its result is
folded into team state. Reports accuracy, AUC, log loss, Brier score, and the
home-team baseline.

`scripts/eval/era_comparison.py` retrains on several start years to check whether
older seasons still help. It trains one model per era, so it is slow.

## Testing

```bash
poetry run pytest -q
```

The suite needs no data and no trained artifacts — it trains a small real ensemble
on a synthetic game log. It covers the leakage guard, chronological ordering,
deterministic replay, artifact validation, and the prediction interface end to end.

## Project structure

```
src/common/features.py                  RunningWorldState + leakage guard
src/models/pregame/train_ensemble_v2.py trainer
src/models/pregame/predictor.py         inference
scripts/data_prep/                      Kaggle → game log
scripts/training/                       training entry point
scripts/eval/                           holdout + era evaluation
scripts/predict.py                      prediction CLI
tests/                                  test suite
```

## Data sources

- [Kaggle basketball dataset](https://www.kaggle.com/datasets/wyattowalsh/basketball) by Wyatt Walsh — historical game results.

See [DATASET_ACKNOWLEDGMENTS.md](DATASET_ACKNOWLEDGMENTS.md) for licensing.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgments

Built on scikit-learn, XGBoost, LightGBM and CatBoost. The Elo and Pythagorean
formulations follow the approaches popularised by FiveThirtyEight and
Basketball-Reference.
