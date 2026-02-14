# NBA Game Predictor

**Machine learning system that predicts NBA game outcomes**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What This Does

This system predicts who'll win NBA games before they happen. It uses three different machine learning models (XGBoost, LightGBM, and CatBoost) and combines their predictions for better accuracy.

## What Makes It Work

- **Three Models Working Together**: XGBoost, LightGBM, and CatBoost vote on each game
- **Smart Features**: Elo ratings, rest days, recent form, winning streaks
- **Fast Predictions**: Processes all games in a day in seconds

## How It's Built

The system is focused on pregame predictions. It looks at historical game results and team performance patterns to make predictions.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full technical breakdown.

## Project Structure

```
NBA-Prediction/
├── src/
│   ├── models/          # Model code
│   │   └── pregame/     # Ensemble models
│   ├── data/            # Data ingestion & preprocessing
│   └── services/        # API services
├── scripts/             # Training & evaluation scripts
└── docs/                # Documentation
```

## Installation

### Prerequisites

- Python 3.10+
- Poetry (Python package manager)
- CUDA-capable GPU (recommended)

### Setup

```bash
# Clone repository
git clone https://github.com/ShauryaMallampati/NBA-Prediction.git
cd NBA-Prediction

# Install Python dependencies
poetry install

# Set any required environment variables for optional data providers
```

Security tip: Never commit API keys or secrets. If you accidentally expose one, rotate it immediately through the provider's dashboard.

### Documentation & Citation

- Want to reproduce our results? Check `REPRODUCIBILITY.md`
- Using this in a paper? See `CITATION.cff` for how to cite us
- Found a security issue? Open a GitHub issue (no public exploits please)

## Getting Started

### Train the Models

```bash
# Train base ensemble
poetry run python scripts/train_ensemble_fixed.py

# Train ensemble v2 (alt)
poetry run python scripts/training/train_ensemble_v2.py

# Build pregame features
poetry run python -m src.data.preprocess.build_pregame_features

# Train ensemble
poetry run python -m src.models.pregame.train_ensemble
```

### Make Predictions

```bash
# Get today's predictions
poetry run python scripts/run_daily_predictions.py
```

### Run Tests

If you add tests, place them under `tests/` and run:

```bash
poetry run pytest -v
```

## Using It in Your Code

### Python API

```python
from src.models.pregame.predictor import EnsemblePredictor

# Load trained ensemble
predictor = EnsemblePredictor("artifacts/models/pregame")

# Predict on a pre-built feature set
df = ...  # pandas DataFrame aligned to feature schema
probs = predictor.predict(df)
print(probs)
```

## Model Performance

- **Game Winner Accuracy**: ~63-66% baseline (varies by season)
- **Calibration**: Isotonic regression on ensemble outputs

## Data Sources

- NBA Stats API (official stats)
- Basketball Reference (historical data)

See [DATASET_ACKNOWLEDGMENTS.md](DATASET_ACKNOWLEDGMENTS.md) for full attribution.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- NBA Stats API for official game data
- Basketball Reference for historical statistics
- scikit-learn, XGBoost, LightGBM, CatBoost communities

## Citation

If you use this code in your research, please cite:

```bibtex
@software{mallampati2025nba,
  title={Multi-Modal Deep Learning for NBA Game Prediction},
  author={Mallampati, Shaurya},
  year={2025},
  url={https://github.com/ShauryaMallampati/NBA-Prediction}
}
```

## Contact

For questions or collaboration: [GitHub Issues](https://github.com/ShauryaMallampati/NBA-Prediction/issues)
