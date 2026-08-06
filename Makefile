.PHONY: help install data train predict eval test check clean

help:
	@echo "NBA Game Predictor - make targets:"
	@echo "  install  - Install Python dependencies with Poetry"
	@echo "  data     - Build data/nba_games_enhanced.csv from the Kaggle dataset"
	@echo "  train    - Train the ensemble and save artifacts/models/pregame/"
	@echo "  predict  - Predict one example game (see scripts/predict.py --help)"
	@echo "  eval     - Walk-forward holdout evaluation of the trained ensemble"
	@echo "  test     - Run the test suite"
	@echo "  check    - Byte-compile everything, then run the test suite"
	@echo "  clean    - Remove __pycache__ and build caches"

install:
	poetry install

data:
	poetry run python scripts/data_prep/process_kaggle_games.py

train:
	poetry run python scripts/training/train_ensemble_v2.py

predict:
	poetry run python scripts/predict.py --home Lakers --away Celtics --date 2025-01-15

eval:
	poetry run python scripts/eval/evaluate_holdout.py

test:
	poetry run pytest -q

check:
	poetry run python -m compileall -q src scripts
	poetry run pytest -q

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
