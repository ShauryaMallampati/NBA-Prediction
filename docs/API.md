# Local prediction API

Start with `poetry run uvicorn src.services.api.main:app --host 127.0.0.1 --port 8000`. Interactive OpenAPI documentation is at `/docs`.

## GET /health

Reports process liveness and whether an ensemble has actually been loaded into the process cache. Before the first successful model load:

```json
{"status": "running", "version": "0.1.0", "models_loaded": false}
```

Liveness does not imply that prepared features are available. Restart the server after replacing model files.

## GET /predictions

Optional query parameters are `date` (`YYYY-MM-DD`, defaulting to the server's current date), `home_team`, and `away_team`. Team filters are independent and case-insensitive. The response is a list of matching rows from the configured prepared feature snapshot; no matching games produces `[]`, not predictions from another date.

Each row contains `game_id`, `date`, `home_team`, `away_team`, complementary `home_win_prob`/`away_win_prob`, and `top_features`. The latter reports global LightGBM feature importance and the input values used for that game. It is not a local causal explanation.

The service requires these trusted local files:

```text
artifacts/models/pregame/ensemble_metadata.json
artifacts/models/pregame/xgb_model.pkl
artifacts/models/pregame/lgb_model.pkl
artifacts/models/pregame/cat_model.pkl
artifacts/features/pregame.parquet
```

The feature table must contain game identifiers, date, team columns, and every numeric feature listed in the model metadata. `home`/`away` are accepted aliases for `home_team`/`away_team`. Additional columns are ignored by inference; missing feature columns are errors. The model's original missing-value policy fills numeric NaNs with zero.

| Status | Meaning |
|---|---|
| 200 | Predictions, or an empty list when there are no matching prepared games |
| 422 | Invalid request date or team filter |
| 503 | Missing, invalid, or incompatible model/feature artifacts |
| 500 | Unexpected server error; details remain in server logs |

Artifact paths are relative to the working directory, or `NBA_PROJECT_ROOT` when set. The service does not fetch live data, compute a future feature snapshot, retrain models, or authenticate users. Keep it bound to localhost unless a separate authenticated deployment layer is provided. Never load untrusted pickle files.
