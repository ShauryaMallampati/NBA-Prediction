# NBA Game Predictor

Pregame NBA outcome modeling with a calibrated XGBoost, LightGBM, and CatBoost ensemble.

## What it does

- Builds 27 pregame features from chronological game history: Elo, rest, streaks, and rolling scoring/win rates.
- Calibrates the three base classifiers with time-series splits and combines their probabilities with saved weights.
- Loads a saved feature schema, validates model outputs, and serves predictions through a local FastAPI service or JSONL command-line workflow.
- Evaluates frozen models on later games with accuracy, ROC-AUC, Brier score, log loss, baselines, and input/model hashes.

## How it works

```text
Completed game history -> pregame features -> three calibrated classifiers
                                             -> weighted home-win probability
                                             -> local API / JSONL / evaluation
```

Features are recorded before each game's result updates the history. The supported trainer selects an explicit feature list instead of admitting arbitrary box-score columns. Cross-validation diagnostics and training-set ensemble metrics are labeled separately; they are not interchangeable.

The supported path is `src/models/pregame/train_ensemble.py` -> `predictor.py` -> `src/services/prediction_service.py`. Older momentum, player-prop, video, and alternate-ensemble experiments are not part of this verified path. Their optional dependencies are separated into Poetry's `legacy` group; installing that group does not imply those experiments have been validated.

## Quick start

Requires **Python 3.10–3.13** and **Poetry 2.2.1**. A GPU is not required. Run commands from the repository root:

```bash
git clone https://github.com/ShauryaMallampati/NBA-Prediction.git
cd NBA-Prediction
poetry install --only main,dev
poetry run pytest -q
poetry run ruff check src scripts tests
poetry build
```

The tests require no live NBA service, credentials, or downloaded model weights. They include a small real-estimator training/serialization/CLI round trip using explicitly synthetic data. This verifies software behavior, **not NBA prediction accuracy**.

## Train and evaluate with your data

No trained model or scored held-out NBA dataset is bundled, so this repository does not claim a held-out accuracy number. The old approximate accuracy claim has been removed because its frozen inputs and model provenance were not available in the release tree.

Prepare a local CSV or Parquet snapshot with `game_id`, `date`, `home`, `away`, and completed-game `home_pts`/`away_pts` (or binary `home_win`). Use consistent team identifiers and include chronological history before the evaluation period. The supported trainer keeps the existing exclusive training cutoff of **2024-10-01**.

```bash
poetry run python -m src.models.pregame.train_ensemble data/raw/games.csv
poetry run python scripts/evaluate_release.py \
  --games data/raw/games.csv \
  --model-dir artifacts/models/pregame \
  --start 2024-10-01 --end 2025-06-30 \
  --output artifacts/evaluation.json
```

These commands require your real snapshot; they do not download it or manufacture a benchmark. See [reproducibility](REPRODUCIBILITY.md) for the schema, provenance requirements, and interpretation of the evaluation. Data sources referenced by the original ingestion scripts are listed in [dataset acknowledgments](DATASET_ACKNOWLEDGMENTS.md).

## Serve prepared predictions

Place trusted model artifacts under `artifacts/models/pregame/` and a prepared feature table at `artifacts/features/pregame.parquet`. The table must contain `game_id`, `date`, `home_team`/`away_team` (or `home`/`away`), and every feature in the saved model metadata.

```bash
poetry run uvicorn src.services.api.main:app --host 127.0.0.1 --port 8000
# In another terminal:
poetry run python scripts/run_daily_predictions.py --date 2025-01-15
```

The CLI also accepts `--features`, `--model-dir`, and `--output-dir`. Paths default to the working directory; `NBA_PROJECT_ROOT` can select another data workspace. Neither serving command fetches live data or builds tomorrow's feature snapshot. Restart the API after replacing model artifacts.

`GET /health` reports liveness and actual model-load state. `GET /predictions?date=YYYY-MM-DD` returns only matching prepared games; missing or incompatible artifacts return HTTP 503. Interactive API documentation is available at `/docs`. See [API details](docs/API.md).

The optional Docker setup runs only the API, with read-only artifact access; PostgreSQL and Redis are not required:

```bash
docker compose up --build
```

## Limitations

This is an experimental modeling project, not a live forecasting service. A schedule alone is insufficient to reproduce a scored evaluation. Training provenance, held-out data, provider permissions, and consistent feature snapshots remain the user's responsibility. The evaluation updates feature history with completed prior games but never retrains the frozen models.

Displayed LightGBM importance is **global feature importance**, not a per-game causal explanation or SHAP attribution. Pickle model files can execute code: load only artifacts you created or otherwise trust. The local API has no authentication and should not be exposed directly to the public internet.

Prediction jobs are local and explicit. No scheduled workflow commits generated data into the repository.

## License

Code is released under the [MIT License](LICENSE). Dataset permissions and licenses are separate.
