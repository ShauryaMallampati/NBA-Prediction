# Reproducing an evaluation

## What is available

The repository contains code and offline software tests, but no frozen trained NBA ensemble, schedule feed, or scored held-out dataset. Synthetic test fixtures must not be reported as NBA performance.

## Input contract

Use one immutable CSV or Parquet snapshot containing both the earlier training history and the later evaluation games:

| Column | Meaning |
|---|---|
| `game_id` | Unique game identifier; preserve leading zeros |
| `date` | Timezone-free calendar date, `YYYY-MM-DD` |
| `home`, `away` | Consistent, nonempty team identifiers; `home_team`/`away_team` aliases are accepted |
| `home_pts`, `away_pts` | Finite, nonnegative final scores; no ties |
| `home_win` | Optional binary result, required when final scores are absent; must agree with scores when both are present |

The contract supports one game per team per date. It rejects duplicates, missing teams/dates, invalid scores, and inconsistent labels. When scores are absent, scoring-history features retain their documented initial value; a score-complete snapshot is preferable.

Obtain the data from a provider you are permitted to use. Record its name, exact dataset version/download date, original file hash, licensing terms, and any filtering/conversion steps. Provider-specific ingestion prototypes are intentionally omitted from this release because no pinned provider snapshot was recovered; source links alone would not reproduce an older result.

## Fixed training/evaluation boundary

The supported trainer preserves the original exclusive cutoff: only games **before 2024-10-01** are used to fit models. It records the source snapshot SHA-256, training range, game count, training home-win rate, and model parameters in `ensemble_metadata.json`.

```bash
poetry install --only main,dev
poetry run python scripts/train_ensemble_fixed.py \
  --games data/raw/games.csv \
  --output-dir artifacts/models/pregame
poetry run python scripts/evaluate_release.py \
  --games data/raw/games.csv \
  --model-dir artifacts/models/pregame \
  --start 2024-10-01 --end 2025-06-30 \
  --output artifacts/evaluation.json
```

Use the same unchanged full snapshot for both commands. Evaluation verifies the recorded snapshot hash when available and rejects a window overlapping training. `--expected-source-sha256 HASH` additionally pins a requested input. An old model without training dates is rejected rather than assigned invented provenance.

The evaluation command never trains a model. It reconstructs the same pregame features over the ordered history, using each completed game's outcome only for subsequent games. This is sequential feature updating with fixed models, not independent predictions made before the entire held-out season began.

## Report contents

The JSON report includes the evaluated dates and game count; accuracy, ROC-AUC, Brier score, and log loss; always-home and Elo baselines; a training-home-win-rate baseline when recorded; model and input hashes; feature names; and Python/package versions. ROC-AUC is `null` for a single-outcome evaluation window, where it is undefined. The decision threshold is 0.5.

Keep the raw snapshot, all four model/metadata files, `poetry.lock`, Git commit, and report together. Do not replace historical reports with corrected runs under the same provenance. Dataset contents and results are excluded from source control by default.

## Software checks

```bash
poetry run pytest -q
poetry run ruff check src scripts tests
poetry run python -m compileall -q src scripts tests
poetry build
```

Tests cover date-grouped validation splits, current/future-outcome perturbations, explicit feature selection, real-estimator serialization, API errors, deterministic evaluation, hash mismatches, and training/evaluation separation. They provide software evidence, not a claim of predictive performance on real NBA games.
