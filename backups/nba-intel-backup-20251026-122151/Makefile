PY?=python3.11
API_HOST?=0.0.0.0
API_PORT?=8000
WEB_PORT?=3000

.PHONY: setup up down key-audit seed data train-pregame train-live train-vision train-chemistry social-build eval serve web fmt lint typecheck

setup:
	@if command -v uv >/dev/null 2>&1; then echo "Using uv"; uv pip install -r <(uv pip compile -q pyproject.toml) || true; else echo "Using poetry"; poetry install; fi
	npm -C web install || true
	pre-commit install || true

up:
	docker compose up -d

down:
	docker compose down

key-audit:
	$(PY) -m src.data.validators.key_audit

seed:
	$(PY) -m src.data.ingest.nba_stats_client --seed
	$(PY) -m src.data.ingest.br_loader --seed
	$(PY) -m src.data.ingest.travel_ors --seed

data:
	$(PY) -m src.data.preprocess.build_pregame_features
	$(PY) -m src.data.preprocess.build_live_sequences
	$(PY) -m src.data.preprocess.build_lineup_graph
	$(PY) -m src.data.preprocess.build_vision_index
	$(PY) -m src.data.preprocess.build_social_aggregates
	$(PY) -m src.data.preprocess.join_social_to_graph

train-pregame:
	$(PY) -m src.models.pregame.train_lgbm

train-live:
	$(PY) -m src.models.live.train_gru

train-vision:
	$(PY) -m src.models.vision.train_classifier

train-chemistry:
	$(PY) -m src.models.chemistry.train_gnn

social-build:
	$(PY) -m src.models.sentiment.stance_and_sentiment

eval:
	$(PY) -m src.models.pregame.calibrate

serve:
	uvicorn src.services.api.main:app --host $(API_HOST) --port $(API_PORT) --reload

web:
	npm -C web run dev -- --port $(WEB_PORT)

fmt:
	ruff check --fix . && black .

lint:
	ruff check .

typecheck:
	mypy src
