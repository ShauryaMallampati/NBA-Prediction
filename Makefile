.PHONY: help setup up down key-audit seed data train-pregame train-live train-vision train-chemistry social-build eval serve web test lint typecheck clean setup-gdrive stream-gdrive

help:
	@echo "NBA Intelligence Platform - Make targets:"
	@echo "  setup            - Install Python/Node deps; install pre-commit"
	@echo "  up               - Start Postgres + Redis via Docker"
	@echo "  down             - Stop services"
	@echo "  key-audit        - Print which required keys are present; ping providers"
	@echo "  seed             - Download real data; write parquet caches; validate"
	@echo "  data             - Build all features (tabular/seq/graph/social) from real data"
	@echo "  train-pregame    - Train GBM + calibration; save artifacts"
	@echo "  train-live       - Train GRU sequence model"
	@echo "  train-vision     - Train clip classifier"
	@echo "  train-chemistry  - Train GNN; export lineup embeddings"
	@echo "  social-build     - Run social ETL + aggregates + social graph edges"
	@echo "  eval             - Run ablations, calibration, notebooks → artifacts/"
	@echo "  setup-gdrive     - Set up Google Drive integration (rclone or API)"
	@echo "  stream-gdrive    - Run streaming model with Google Drive videos"
	@echo "  serve            - Start FastAPI"
	@echo "  web              - Start Next.js"
	@echo "  test             - Run pytest suite"
	@echo "  lint             - Run Next.js lint"
	@echo "  typecheck        - Run TypeScript typecheck"
	@echo "  clean            - Remove artifacts and caches"

setup:
	@echo "Installing Python dependencies..."
	poetry install
	@echo "Installing pre-commit hooks..."
	poetry run pre-commit install
	@echo "Installing Node dependencies..."
	npm install
	@echo "Setup complete!"

up:
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	docker-compose ps

down:
	docker-compose down

key-audit:
	poetry run python -m src.common.key_audit

seed:
	poetry run python -m src.data.ingest.seed_all

data:
	poetry run python -m src.data.preprocess.build_pregame_features
	poetry run python -m src.data.preprocess.build_live_sequences
	poetry run python -m src.data.preprocess.build_lineup_graph
	@if [ "$$ENABLE_SENTIMENT" = "true" ]; then \
		poetry run python -m src.data.preprocess.build_social_aggregates; \
	fi

train-pregame:
	poetry run python -m src.models.pregame.train_lgbm

train-live:
	poetry run python -m src.models.live.train_gru

train-vision:
	poetry run python -m src.models.vision.train_classifier

train-chemistry:
	poetry run python -m src.models.chemistry.train_gnn

social-build:
	poetry run python -m src.models.sentiment.stance_and_sentiment
	poetry run python -m src.data.preprocess.join_social_to_graph

eval:
	poetry run python -m src.models.pregame.evaluate
	poetry run jupyter nbconvert --execute --to html notebooks/*.ipynb

serve:
	poetry run uvicorn src.services.api.main:app --reload --host 0.0.0.0 --port 8000

web:
	npm run dev

test:
	poetry run pytest tests/ -v --cov=src --cov-report=html

lint:
	npm run lint

typecheck:
	npm run typecheck

clean:
	rm -rf artifacts/*.pkl artifacts/*.json
	rm -rf data/cache/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
setup-gdrive:
	@echo "Setting up Google Drive integration..."
	poetry install
	poetry run python scripts/eval/setup_gdrive_integration.py

stream-gdrive:
	@echo "Starting streaming world model (Google Drive edition)..."
	poetry run python scripts/eval/streaming_world_model_gdrive.py --season 2025-26