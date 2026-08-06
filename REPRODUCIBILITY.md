# Reproducibility

What you can reproduce from a fresh clone, what you cannot, and why.

## What is included

- All training, prediction and evaluation code.
- The feature engine (`src/common/features.py`), which fully determines the
  80-column schema.
- A test suite that runs with no data and no trained artifacts.
- Fixed random seeds: `random_state=42` / `random_seed=42` on all four base models
  and the meta-learner, and `src/common/seed.py` for the stdlib and NumPy.

## What is not included

| Missing | Why | How to get it |
| --- | --- | --- |
| `data/kaggle_nba/Games.csv` | Third-party dataset, CC BY-SA 4.0; not redistributed here | [Download from Kaggle](https://www.kaggle.com/datasets/wyattowalsh/basketball) |
| `data/nba_games_enhanced.csv` | Derived from the above | `python scripts/data_prep/process_kaggle_games.py` |
| `artifacts/models/pregame/*` | ~320 MB of pickled models, dominated by ExtraTrees | `python scripts/training/train_ensemble_v2.py` |

**No trained model artifacts are distributed with this repository.** Every command
that predicts or evaluates needs you to train first.

## Reproducible without any data

```bash
poetry install
poetry run python -m compileall src scripts
poetry run pytest -q
```

Expected: everything compiles, 61 tests pass in a few seconds. The suite trains a
real (small) ensemble on a synthetic game log generated from a fixed seed, so it
exercises the production training and prediction code rather than mocks.

## Reproducible with the public dataset

```bash
# 1. place Kaggle Games.csv in data/kaggle_nba/, then:
poetry run python scripts/data_prep/process_kaggle_games.py
poetry run python scripts/training/train_ensemble_v2.py
poetry run python scripts/eval/evaluate_holdout.py
```

Expected outputs:

- `data/nba_games_enhanced.csv` — one row per completed game.
- `artifacts/models/pregame/` — seven files: four base models, the meta-learner,
  the meta-scaler, and `ensemble_metadata.json`.
- A holdout table: accuracy, AUC, log loss, Brier score, and the
  always-pick-the-home-team baseline.

You will get *a* number in the mid-60s. You will not get an identical number to
the one below, because the Kaggle dataset is updated over time and your snapshot
will differ from the one used here.

## The numbers this project reports, and their provenance

| Figure | What it measures | Where it came from | Reproducible from a clone? |
| --- | --- | --- | --- |
| **65.2%** accuracy, 0.708 AUC, 1,383 games | Walk-forward holdout on 2024-25, after the `2024-10-01` training cutoff | `scripts/eval/evaluate_holdout.py`, run locally against artifacts trained 2026-02-06 | **No** — needs those artifacts and that data snapshot |
| 64.4% / 65.7% / 65.9% / 65.9% | Per-model out-of-fold accuracy during training (XGB / LGB / Cat / ET) | `ensemble_metadata.json` from the same run | No |
| 65.86% | Unweighted mean of the four out-of-fold predictions, over the training period | `ensemble_metadata.json`, key `simple_avg.accuracy` | No |
| 65.97% | Meta-learner accuracy — **measured on the rows it was fitted on**, so optimistic | `ensemble_metadata.json`, key `meta.accuracy` | No |

The holdout figure is the one to quote. The other three are training-period
diagnostics over a different set of games and are not comparable to it.

Historical evaluation placed the system in the mid-60% range, but trained model
artifacts and full datasets are not included in this repository.

## Pickled models are tied to the library versions that made them

Predictions are deterministic within one environment and drift slightly across
environments. The same artifacts, on the same input, measured here:

| Environment | `P(home win)` for Lakers vs Celtics, 2025-01-15 |
| --- | --- |
| xgboost 3.1.3 / lightgbm 4.6.0 / catboost 1.2.8 | 0.3899 |
| xgboost 3.2.0 / lightgbm 4.7.0 / catboost 1.2.10 | 0.3935 |

Roughly 0.4 percentage points from library versions alone, and XGBoost emits a
version-mismatch warning when unpickling a model saved by an older release. Pin
via `poetry.lock` if you need bit-identical predictions, and re-train rather than
carrying old pickles across major upgrades.

## Development history that is not a public benchmark

Earlier versions of this project experimented with highlight video, crowd audio, a
momentum sequence model, player-relationship features, and multimodal fusion.
Whatever comparisons were made between those versions and the tabular baseline
were development-time observations on local data. They were not produced by any
code in this release, no artifacts survive that would let anyone re-run them, and
they should not be read as a benchmark. **No formal ablation study was performed.**

## Recording a run

If you are writing up results, capture:

- Git commit hash.
- Kaggle dataset version / download date, and the date range in your game log.
- `cutoff_date` used for training and the holdout window used for evaluation.
- The full contents of `artifacts/models/pregame/ensemble_metadata.json`, which
  records the feature schema, weights, metrics and a `metric_definitions` block
  saying exactly what each metric measures.
