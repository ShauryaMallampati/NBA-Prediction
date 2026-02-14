# Reproducibility Guide

This project supports end‑to‑end reproduction of data ingestion, feature building,
model training, and evaluation. The exact numbers depend on data snapshots and API
availability, so record the date/time and data source versions you used.

## Environment

- Python 3.10+ with `poetry.lock`

```bash
poetry install
```

## Data snapshots

Most pipelines read from `data/`. To make runs reproducible:

1. Snapshot raw data (or store a hash + timestamp).
2. Record the exact schedule window and provider used.
3. Avoid mixing live and historical data in the same run.

## Full pipeline (recommended order)

```bash
make data
make train-pregame
```

Artifacts typically land in `artifacts/` or `data/metrics/` depending on the script.
If you change output paths, note them in your experiment log.

## Suggested experiment log

Capture this for any paper-ready run:

- Git commit hash
- Data snapshot date range
- Key hyperparameters (model + training)
- Hardware (GPU/CPU/RAM)
- Metrics + plots produced
