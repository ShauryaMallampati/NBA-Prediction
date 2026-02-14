.PHONY: help setup up down data train-pregame serve test clean

help:
	@echo "NBA Intelligence Platform - Make targets:"
	@echo "  setup            - Install Python deps; install pre-commit"
	@echo "  up               - Start Postgres + Redis via Docker"
	@echo "  down             - Stop services"
	@echo "  data             - Build pregame features from raw data"
	@echo "  train-pregame    - Train ensemble + calibration; save artifacts"
	@echo "  serve            - Start FastAPI"
	@echo "  test             - Run pytest suite"
	@echo "  clean            - Remove artifacts and caches"

setup:
	@echo "Installing Python dependencies..."
	poetry install
	@echo "Installing pre-commit hooks..."
	poetry run pre-commit install
	@echo "Setup complete!"

up:
	docker-compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	docker-compose ps

down:
	docker-compose down

data:
	poetry run python -m src.data.preprocess.build_pregame_features

train-pregame:
	poetry run python -m src.models.pregame.train_ensemble


serve:
	poetry run uvicorn src.services.api.main:app --reload --host 0.0.0.0 --port 8000

test:
	poetry run pytest -v

clean:
	rm -rf artifacts/*.pkl artifacts/*.json
	rm -rf data/cache/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete