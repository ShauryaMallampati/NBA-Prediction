# Public Release Audit

Audit of the repository before the public-release cleanup. Every item below was
verified by running the command or reading the file named; nothing here is
assumed.

- **Date of audit:** 2026-08-06
- **HEAD at audit time:** `f1050ee495d3be138de392683d37dbd9b5c1adfa` ("move System_Architecture_v5.png to docs folder")
- **Branch created for the cleanup:** `cleanup-public-release` (from `main`)
- **Remote:** `https://github.com/ShauryaMallampati/NBA-Prediciton.git` (repository name is misspelled)

---

## 1. Working tree state

`git status --short` at the start of the audit:

```
 M CONTRIBUTING.md
 M REPRODUCIBILITY.md
```

Both modifications are **reversions**: the working-tree copies were older versions
that re-introduced `npm install`, `cp .env.example .env`, `npm run lint/typecheck/build`,
`make seed`, `make train-live`, `make train-vision`, `make train-chemistry` and a
"Frontend verification" section. None of those targets or files exist in the
repository. Both files are rewritten by this cleanup, so the divergence is resolved.

## 2. Environment

| Item | Result |
| --- | --- |
| Python on PATH | 3.10.14 (pyenv) |
| `pyproject.toml` requires | `python = "^3.10"` |
| Project virtualenv | none present (`.venv` absent, no poetry env) |
| Poetry | 2.2.1 available |

**Do the declared dependencies install?** Not verified against the *original*
`pyproject.toml`, and deliberately so: it declares `torch`, `torchvision`,
`opencv-python`, `librosa` and `moviepy` — several GB of multimedia/GPU wheels
that the retained code does not import (see §7). A clean virtualenv containing
only the dependencies the retained code actually imports (`pandas`, `numpy`,
`scikit-learn`, `xgboost`, `lightgbm`, `catboost`, `pyarrow`, `pytest`) installs
and imports successfully, and is what the tests in this cleanup run against.

## 3. Code health: 27 of 61 Python files did not compile

`python -m compileall src scripts` failed on **27 files**, i.e. essentially the
entire core of the project. Examples:

```
src/models/pregame/predictor.py:2       SyntaxError: invalid syntax
src/data/ingest/cache_manager.py:69     SyntaxError: unterminated string literal
src/models/pregame/train_ensemble.py    SyntaxError: unterminated triple-quoted string literal
```

**Cause, established by bisecting the history:** commit `d3c6ef5` ("Only kept
needed files") was a docstring-rewording pass that inserted a *second* opening
`"""` instead of replacing only the summary line:

```python
"""
"""Load our trained models and use them to predict games.
"""
```

Compile-error counts by commit: `bd6b4a5` → 1, `4168f1a` → 1, `d3c6ef5` → 27,
`f1050ee` (HEAD) → 27.

**Verification of the repair.** 45 damaged sites across the 27 files were fixed by
deleting the stray delimiter and keeping the reworded text. To prove the repair
touched nothing but docstrings, every file was parsed with `ast`, its docstrings
stripped, and the resulting tree compared to the same file at `4168f1a` (the last
commit where these files compiled): **52 of 61 files are byte-identical in code
structure**. The 9 that differ (`run_daily_predictions.py`, `common/config.py`,
`common/validators.py`, `ingest/cache_manager.py`, `ingest/game_fetcher.py`,
`ingest/nba_api_client.py`, `preprocess/build_pregame_features.py`,
`preprocess/engineer_features.py`, `services/api/main.py`) differ because
`d3c6ef5` also intentionally deleted code from them (unused API-key settings,
player-prop endpoints, imports of removed services). No logic was changed by the
repair.

## 4. Tests

There is no `tests/` directory and no test files anywhere in the repository.
`pytest -q` cannot run (`No module named pytest` in the ambient interpreter; no
tests to collect in any case). The README says only *"If you add tests, place them
under `tests/`"*, while `CONTRIBUTING.md` and the `Makefile` both instruct
contributors to run `poetry run pytest`, which would collect zero tests.

## 5. Broken references in documentation

| Reference | Where | Status |
| --- | --- | --- |
| `ARCHITECTURE.md` | README line 22 | **File does not exist** (no `ARCHITECTURE.md` anywhere) |
| `CITATION.cff` | README line 63 | **File does not exist** |
| `https://github.com/ShauryaMallampati/NBA-Prediction` | README lines 49, 156, 162 | **Wrong URL** — the real repo is `NBA-Prediciton` |
| `.env.example` | CONTRIBUTING, REPRODUCIBILITY | **File does not exist** |
| `KEYS.md` | `src/common/validators.py` error text | **File does not exist** |
| `package-lock.json`, `npm run lint/typecheck/build` | CONTRIBUTING, REPRODUCIBILITY | **No frontend in the repository** — no `package.json`, no JS/TS sources tracked |
| `make seed`, `make train-live`, `make train-vision`, `make train-chemistry`, `make eval` | REPRODUCIBILITY | **Targets do not exist** in the `Makefile` |
| `configs/` | `Dockerfile` line 39, `docker-compose.yml` line 69 | **Directory does not exist** — the Docker build fails on this `COPY` |
| `scripts/run_daily_evaluation.py` | `.github/workflows/daily-jobs.yml` | **Script does not exist** (workflow silently skips it) |
| `DATASET_ACKNOWLEDGMENTS.md` | README line 125 | Exists (link is valid) |
| `LICENSE` | README line 139 | Exists (MIT) |

## 6. Imports of modules that no longer exist

Verified by walking every tracked `.py` file's AST and resolving each `src.*` import
against the filesystem:

| File | Missing import |
| --- | --- |
| `scripts/ablation_comprehensive.py` | `src.models.chemistry_gnn` |
| `scripts/ablation_comprehensive.py` | `src.models.vision.vision_model` |
| `scripts/ablation_comprehensive.py` | `src.models.vision.audio_analytics` |
| `scripts/ablation_comprehensive.py` | `src.models.fusion.learnable_fusion` |
| `src/models/pregame/train_on_real_data.py` | `src.models.pregame.train_props_model` |

Both files are unrunnable as committed. Two files also hard-code an absolute
`sys.path.insert(...)` pointing at a directory that exists only on the original
author's machine: `src/models/pregame/integrate_rest_risk.py:11` and
`src/models/pregame/train_on_real_data.py:25`.

## 7. Obsolete dependencies

Declared in `pyproject.toml` but **not imported by any tracked file**:

| Dependency | Imported by |
| --- | --- |
| `librosa` | nothing |
| `moviepy` | nothing |
| `yt-dlp` | nothing (`scripts/data_prep/download_highlights.py` shells out to the binary) |
| `opencv-python` | `scripts/modal_video_analyzer.py` only |
| `torchvision` | `scripts/ablation_comprehensive.py`, `scripts/modal_video_analyzer.py` only |
| `torch` | `ablation_comprehensive.py`, `modal_video_analyzer.py`, `src/models/momentum/*`, `src/common/seed.py`, `src/common/hardware.py` |

Imported by tracked code but **not declared** in `pyproject.toml`:
`beautifulsoup4` (`bs4`), `redis`, `shap`, `scipy`, `modal`. The project therefore
does not install to a working state for several of its own modules.

`selenium` and frontend packages: not present in `pyproject.toml` (nothing to remove).

## 8. GitHub Actions

| Workflow | Assessment |
| --- | --- |
| `ci.yml` | Runs `python -m compileall src scripts` on push/PR. **Currently failing** — 27 files do not compile (§3). No `permissions:` block, so it inherits the repository default. Runs no tests. |
| `daily-jobs.yml` | **Cannot succeed and must not run.** Requests `contents: write`; runs `poetry install` (which pulls torch/opencv/librosa/moviepy and has previously failed at this step); calls `scripts/run_daily_predictions.py`, which exits 1 because `artifacts/features/pregame.parquet` is gitignored and absent from a fresh checkout; then `git add -f data/` — force-adding the entire gitignored `data/` tree — commits to `main`, and force-pushes with `--force-with-lease` on rebase failure. |
| `secret-scan.yml` | Gitleaks on push/PR. Reasonable; no `permissions:` block. |

## 9. Tracked generated files and clutter

| Path | Issue |
| --- | --- |
| `catboost_info/catboost_training.json` (76K) | CatBoost training log, generated output |
| `catboost_info/learn_error.tsv`, `test_error.tsv` | training loss curves, generated output |
| `catboost_info/learn/events.out.tfevents`, `test/events.out.tfevents` | TensorBoard event files, generated output |
| `docs/System_Architecture_v5.png` (692K) | Diagram of the **removed** multimodal architecture; unreferenced by any document |
| `docs/assets/architecture_v5.png` (660K) | Near-duplicate of the above; unreferenced |
| `docs/architecture_diagram.png` (232K) | Unreferenced by any document |
| `data/nba_season_schedule_2025_26.json` (96K) | Generated schedule dump, tracked despite `/data/*` being gitignored |
| `Dockerfile`, `docker-compose.yml` | Build fails (`COPY configs/`); compose starts Postgres and Redis, and no tracked source contains any database code |

`docs/System_Architecture_v5.png` was inspected directly. It is titled "NBA WORLD
MODEL v5: TECHNICAL ARCHITECTURE DIAGRAM" and depicts Video Highlights, Vision
CNN, Chemistry GNN, Optical Flow Analysis, Crowd Audio Analytics, Momentum
Transformer, a "Neural Referee" fusion layer and Monte Carlo dropout — none of
which exist in the current source tree.

## 10. Secrets and credentials

**No secrets were found in tracked files.** Scans performed over all tracked
files for `api_key|secret|token|password|bearer|cookie` assignment patterns,
e-mail addresses, and absolute `/Users/` paths returned:

- No API keys, tokens, cookies, or credentials.
- `pyproject.toml:5` — placeholder author e-mail `shaurya@example.com`.
- `.github/workflows/daily-jobs.yml:64` — bot e-mail `bot@nbaintel.com` (not a real address).
- Two hard-coded local absolute paths (§6), in files removed by this cleanup.

The `.gitignore` already excludes `cookies.json`, `cookies.txt`, `credentials.json`,
`token.json`, `.kaggle/` and similar. Untracked local directories `lib/` (frontend
TypeScript) and `supabase/` exist on disk but are **not** tracked and not ignored —
they are one `git add .` away from being committed.

## 11. Ablation material: simulated, not measured

`scripts/ablation_comprehensive.py` (588 lines) is the only ablation code in the
repository. It **cannot run**: it imports four deleted modules (§6). Beyond that,
even if the imports were restored, its "modality contributions" are not
measurements:

- `get_audio_delta()` returns `0.0` unconditionally (`# Placeholder for audio analysis`).
- `get_optical_flow_delta()` returns `0.0` unconditionally (`# Placeholder for optical flow analysis`).
- `get_vision_delta()` does not read any video. Its comment says
  `# Placeholder: would use actual video analysis`, and it computes a delta from
  the tabular columns `home_off_rating`/`away_off_rating`.

Untracked local outputs in `data/ablation_results/` (`ablation_results.json`,
`ablation_table.md`, `ablation_table.tex`) claim a "Stats Only 58.32% → Full World
Model 64.87%, Total Improvement +6.55%" result. Two independent reasons to
distrust them:

1. Their configuration names (`A_Stats_Only` … `E_Full_World_Model`) **do not match**
   the names the tracked script emits (`A_Ensemble_Only` … `L_Full_World_Model`),
   so they were not produced by the code in this repository.
2. In every row, AUC is exactly accuracy + 8.00 (58.32/66.32, 61.04/69.04,
   61.18/69.18, 60.15/68.15, 64.87/72.87). Measured AUC and accuracy do not
   maintain a constant offset to two decimal places across five configurations.

**Conclusion: no formal ablation study was performed.** These files are
gitignored (`/data/*`) and so were never public, but the LaTeX table exists in a
form intended for a write-up. This cleanup deletes the broken script and adds no
ablation claims anywhere.

## 12. Exact composition of the released model

The trained artifacts in the local (gitignored) `artifacts/models/pregame/`
directory settle what the "current model" actually is:

```
ensemble_metadata.json   version: 2
                         architecture: stacking_4base_meta
                         base_models: [XGBoost, LightGBM, CatBoost, ExtraTrees]
                         meta_learner: LogisticRegression
                         feature_names: 80 features
                         timestamp: 2026-02-06T10:56:01
xgb_model.pkl (14 MB)  lgb_model.pkl (17 MB)  cat_model.pkl (7 MB)
et_model.pkl (282 MB)  meta_learner.pkl  meta_scaler.pkl
```

The 80 feature names in that metadata are **exactly** the keys returned by
`RunningWorldState.get_team_features()` in `src/common/features.py`, in the same
order (verified by set and list comparison). So:

- **ExtraTrees is genuinely included** in the trained model.
- **The ensemble is four models plus a logistic-regression meta-learner**, not three.
- **Isotonic calibration is used** — every base model is wrapped in
  `CalibratedClassifierCV(method='isotonic', cv=TimeSeriesSplit(3))` before saving.
- **Momentum is not in the prediction path.** `src/models/momentum/` is a PyTorch
  Transformer imported only by the broken ablation script. The word "momentum" in
  the released feature set refers to two plain tabular columns
  (`home_momentum = win% last 5 − win% last 20`, and its away/diff counterparts).

### Two competing implementations exist

| | v1 — `train_ensemble.py` | v2 — `train_ensemble_v2.py` |
| --- | --- | --- |
| Models | XGB, LGB, Cat (3) | XGB, LGB, Cat, ExtraTrees (4) + LR meta-learner |
| Features | `calculate_elo` + `add_rest_features` + `add_streak_features` + `_add_rolling_features` over a prebuilt parquet | `RunningWorldState` (80 features), one code path |
| Input | `artifacts/features/pregame.parquet` (from `build_pregame_features`) | `data/nba_games_enhanced.csv` (flat game log) |
| Ensemble metric | **in-sample** — `predict_ensemble(X)` is scored on the same `X` it trained on | out-of-fold per model |
| Known defect | `_add_rolling_features` writes the constant `100` for `home/away_pts_allowed_avg_l10` (lines 113–114, `# Placeholder`) | — |
| Loaders | `predictor.EnsemblePredictor` (3 models) | `EnsembleTrainer.load_models()` already prefers the v2 stacking path when `et_model.pkl`/`meta_learner.pkl` are present |

### Decision: **Option B — the four-model ensemble (XGBoost, LightGBM, CatBoost, ExtraTrees) with the stacking meta-learner**

Chosen on code evidence, not on which number is higher (the two headline figures
are within 0.1 percentage point of each other anyway):

1. The only trained artifact that exists is v2, and its feature schema matches
   `RunningWorldState` exactly. v2 *is* the de-facto released model.
2. v2 uses one feature function for training and inference, so there is no
   train/serve skew. v1 builds features one way in `build_pregame_features.py`
   and a different way inside `load_data()`.
3. v2's input is a flat game log a user can assemble from public sources. v1's
   input is `data/processed/games.csv` or `data/raw/nba_stats/scoreboard_*.json`,
   neither of which is in the repository or documented.
4. v1 contains a hard-coded placeholder feature value; v2 does not.
5. Even v1's own loader prefers the v2 artifacts when they are on disk.

No deleted experimental code needs to be restored for Option B.

## 13. Performance claims: what is and is not reproducible

### Claims currently made in the repository

| Claim | Location | Verdict |
| --- | --- | --- |
| "~63-66% baseline (varies by season)" | README line 117 | Vague, and attached to a three-model description that does not match the trained model. |
| "XGBoost (currently hitting 63.83% accuracy)" | `train_ensemble.py` docstring | Not reproducible; no artifact or log in the repository records it. |
| "Goal: Get to 70%+ accuracy" | `train_ensemble.py` docstring | Aspiration stated as a project goal, not a result. |
| "Old (no features): ~58% / New: ~65%+ / Full model (+ modalities): ~71%+ target" | `scripts/train_ensemble_fixed.py` lines 88–90 | Printed to the user as "Expected improvement". Unsupported; the "+ modalities" line refers to removed components. |
| "Full history: 64.92% (from main v2 training)" | `scripts/eval/era_comparison.py` line 107 | Hard-coded print statement, not read from any artifact. |
| "Expected accuracy: 65%+ ... Vegas hits around 67%" | `train_ensemble_v2.py` docstring | Unsourced comparison. |
| "Stats Only 58.32% → Full World Model 64.87% (+6.55%)" | `data/ablation_results/` (untracked) | **Simulated** — see §11. |
| `title={Multi-Modal Deep Learning for NBA Game Prediction}` | README line 153 | Describes a system that is not in this repository. |

### Where 65.86% comes from

`artifacts/models/pregame/ensemble_metadata.json` (local, gitignored) records from
the 2026-02-06 training run:

| Metric in metadata | Value | What it actually measures |
| --- | --- | --- |
| `xgb.accuracy` | 64.43% | mean of 5 `TimeSeriesSplit` out-of-fold folds |
| `lgb.accuracy` | 65.72% | as above |
| `cat.accuracy` | 65.94% | as above |
| `et.accuracy` | 65.88% | as above |
| **`simple_avg.accuracy`** | **65.86%** | accuracy of the plain mean of the four models' out-of-fold predictions |
| `meta.accuracy` | 65.97% | meta-learner scored **on the same out-of-fold rows it was fitted on** — optimistic, not a clean out-of-sample estimate |

So 65.86% is a real number produced by a real training run of the released code —
it is the out-of-fold *simple-average* figure, not a holdout result, and not the
figure for the stacked model that is actually saved.

**It is not reproducible from this repository.** Reproducing it needs
`data/nba_games_enhanced.csv` (~30 years of game logs, not in the repository and
not redistributable here) and the 320 MB of trained artifacts (gitignored). A user
who supplies their own game log will get their own number, not this one.

### A clean holdout number now exists

The cleanup added `scripts/eval/evaluate_holdout.py`, a walk-forward evaluation
that predicts each game before folding its result into team state. Run against the
local artifacts and the local game log, over the 2024-25 season — entirely after
the `2024-10-01` training cutoff, so none of it was trained on:

| | |
| --- | --- |
| Games | 1,383 |
| Accuracy | **65.22%** |
| AUC | 0.7082 |
| Log loss | 0.6214 |
| Brier score | 0.2163 |
| Always-pick-the-home-team baseline | 54.88% |

This is the first genuinely out-of-sample figure the project has produced, and it
is the only performance number the README now quotes. It still depends on
artifacts and a data snapshot that are not in the repository, so it is reproducible
in *method* but not in *value* from a fresh clone.

### Reproducible from the public repository

- That the code compiles, imports, and passes its test suite.
- That the feature schema contains no final-score or outcome columns.
- That chronological splitting never places a training game after its validation game.
- That the predictor rejects a feature frame with missing or leakage columns.
- That feature ordering is deterministic.
- Full training and evaluation, **once the user supplies their own game log** —
  producing their own metrics, which will not match the numbers above.

### Not reproducible from the public repository

- The 65.86% / 65.97% figures (no data, no artifacts).
- Any per-season holdout accuracy (`scripts/eval/evaluate_2024_25.py` needs both).
- Anything about vision, audio, chemistry, momentum-transformer, or fusion —
  that code is not in this release and its measurements were never made.

## 14. A defect the new tests found

`EnsembleTrainerV2.prepare_features_from_games()` called
`games_df.sort_values('date')`. Pandas' default sort is **not stable**, so the ~10
games that share a calendar date came out in different orders depending on how the
frame had been filtered beforehand. Because state is updated game by game, that
changed the features of later same-day games — two runs over the same data could
produce different training matrices.

`tests/test_chronology.py::test_games_after_the_cutoff_never_reach_the_training_matrix`
caught this on its first run: truncating the log before the cutoff and passing the
full log with the same cutoff produced different feature matrices, when they must
be identical. Fixed by `sort_games_chronologically()` in `src/common/features.py`,
which sorts on `(date, game_id)` with a stable sort. Two tests now guard it.

A related caveat remains and is documented rather than silently changed: the game
log has date granularity, not tip-off times, so same-day games are replayed in
sequence and the second game of a day inherits the first's result. See
`docs/ARCHITECTURE.md`.

## 15. What this cleanup changes

Deletions from this branch (all preserved in git history):

- **Simulated ablation** — `scripts/ablation_comprehensive.py` (§11).
- **Video / multimodal** — `scripts/modal_video_analyzer.py`,
  `scripts/data_prep/download_highlights.py`, `scripts/data_prep/prep_fusion_data.py`,
  `src/utils/video_metadata.py`, `src/models/momentum/`.
- **Broken or unreachable model code** — `train_on_real_data.py` (imports a module
  that does not exist), `integrate_rest_risk.py` and `blowout_rest_predictor.py`
  (hard-coded local path, no entry point), `scouting_reports.py`,
  `shap_explainer.py`, `explain.py` (depend on `shap`, never a declared dependency),
  `calibrate.py`, `optimize_hyperparameters.py`, `validate_models.py` (the last
  validates player-prop models that do not exist anywhere).
- **The v1 three-model path** — `train_ensemble.py`, `ensemble_predictor.py`,
  `train_lgbm.py`, `elo.py`, `scripts/train_ensemble_fixed.py`,
  `scripts/eval/evaluate_2024_25.py`. Superseded by Option B (§12).
- **The v1 feature path** — `src/data/preprocess/` in full. It fed only the v1
  trainer and read from `data/processed/` and `data/raw/nba_stats/` layouts that
  are not in the repository or documented anywhere.
- **The data-ingest layer** — `src/data/ingest/`, `src/data/player_stats.py`,
  `src/data/web_scraper.py`. No retained entry point calls any of it, and it
  required four dependencies (`nba_api`, `requests`, `beautifulsoup4`, `redis`)
  that `pyproject.toml` never declared. The one data step the release actually
  uses, `scripts/data_prep/process_kaggle_games.py`, is retained.
- **The service layer** — `src/services/` (FastAPI app, sqlite accuracy tracker),
  `docs/API.md`, `Dockerfile`, `docker-compose.yml`, `.dockerignore`. The Docker
  build fails on a missing `configs/`, compose starts Postgres and Redis for code
  that contains no database access, and the API was built on the v1 predictor and
  a feature parquet this release no longer produces.
- **Config plumbing left with no callers** — `src/common/config.py`, `paths.py`,
  `validators.py`, `hardware.py`.
- **Generated files and stale assets** — `catboost_info/`, the three architecture
  PNGs (all depicting the removed multimodal system), `data/nba_season_schedule_2025_26.json`.
- **`.github/workflows/daily-jobs.yml`** — replaced (§8).

Added: `scripts/predict.py`, `scripts/eval/evaluate_holdout.py`,
`docs/ARCHITECTURE.md`, and a 61-test suite that needs neither data nor artifacts.

Nothing was deleted from history, and no result, test, artifact, or measurement was
invented.
