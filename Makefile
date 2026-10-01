.PHONY: help setup test lint build serve train-pregame up down

help:
	@echo "setup: install dependencies; test: run offline tests; lint: check code"
	@echo "build: build distributions; serve: start the local API"
	@echo "train-pregame GAMES=path/to/games.csv: train on your completed-game snapshot"
	@echo "up/down: start/stop the optional Docker API"

setup:
	poetry install --only main,dev

test:
	poetry run pytest -q

lint:
	poetry run ruff check src scripts tests
	poetry run python -m compileall -q src scripts tests

build:
	poetry build

serve:
	poetry run uvicorn src.services.api.main:app --host 127.0.0.1 --port 8000

train-pregame:
	@test -n "$(GAMES)" || (echo "Set GAMES to a completed-game CSV or Parquet snapshot"; exit 1)
	poetry run python -m src.models.pregame.train_ensemble "$(GAMES)"

up:
	docker compose up --build -d

down:
	docker compose down
