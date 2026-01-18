# NBA Prediction System

**Multi-Modal Deep Learning for NBA Game Prediction**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Advanced NBA prediction system combining multiple deep learning modalities through a learnable fusion architecture. The system processes pregame stats, player chemistry graphs, momentum sequences, video highlights, and audio commentary to generate accurate game predictions.

## Key Features

- **Multi-Modal World Model**: Combines 6+ data sources for comprehensive game analysis
- **Learnable Fusion**: Gated attention mechanism dynamically weights each modality
- **Real-Time Predictions**: Live game predictions with uncertainty quantification
- **Chemistry Analysis**: GNN-based team chemistry and lineup synergy modeling
- **Momentum Tracking**: Transformer-based temporal momentum analysis
- **Vision Processing**: CNN analysis of game highlights and player movements
- **Interactive Dashboard**: Next.js web app with real-time updates

## Architecture

The system uses a hierarchical World Model architecture:

1. **Base Ensemble**: XGBoost + LightGBM on pregame features
2. **Modality Modules**:
   - Vision CNN: Video highlight analysis
   - Audio Transformer: Commentary sentiment
   - Optical Flow: Player movement patterns
   - Chemistry GNN: Team synergy graphs
   - Momentum Transformer: Temporal sequences
3. **Learnable Fusion**: Gated attention combines all modalities
4. **Uncertainty Quantification**: Bayesian MC Dropout

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed system design.

## Project Structure

```
NBA-Prediction/
├── src/
│   ├── models/          # Deep learning models
│   │   ├── fusion/      # Learnable fusion module
│   │   ├── chemistry/   # GNN models
│   │   ├── momentum/    # Transformer models
│   │   ├── vision/      # CNN models
│   │   └── pregame/     # Ensemble models
│   ├── data/            # Data ingestion & preprocessing
│   ├── services/        # API services
│   └── api/             # FastAPI endpoints
├── app/                 # Next.js frontend
├── scripts/             # Training & evaluation scripts
├── tests/               # Unit tests
└── docs/                # Documentation
```

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- Poetry (Python package manager)
- CUDA-capable GPU (recommended)

### Setup

```bash
# Clone repository
git clone https://github.com/ShauryaMallampati/NBA-Prediction.git
cd NBA-Prediction

# Install Python dependencies
poetry install

# Install Node.js dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

Create a `.env` file with:

```bash
# API Keys
RAPID_API_KEY=your_key_here
SUPABASE_URL=your_url_here
SUPABASE_KEY=your_key_here

# Model Paths
MODEL_DIR=artifacts/models
DATA_DIR=data
```

## Quick Start

### Train Models

```bash
# Train base ensemble
poetry run python scripts/train/train_ensemble.py

# Train chemistry GNN
poetry run python scripts/train/train_chemistry.py

# Train momentum transformer
poetry run python scripts/train/train_momentum.py

# Train fusion module
poetry run python scripts/train/train_fusion.py
```

### Run Predictions

```bash
# Get today's predictions
poetry run python scripts/predict/daily_predictions.py

# Run web dashboard
npm run dev
```

### Run Tests

```bash
# Python tests
poetry run pytest tests/ -v

# Check code quality
poetry run black src/
poetry run isort src/
```

## Usage

### Python API

```python
from src.models.fusion.learnable_fusion import FusionModule
from src.services.prediction_service import PredictionService

# Initialize prediction service
service = PredictionService()

# Get predictions for today's games
predictions = service.get_daily_predictions()

for pred in predictions:
    print(f"{pred.away_team} @ {pred.home_team}")
    print(f"Winner: {pred.predicted_winner} ({pred.probability:.1%})")
    print(f"Confidence: {pred.confidence}")
```

### Web Dashboard

```bash
# Start development server
npm run dev

# Open browser to http://localhost:3000
```

Features:
- Live game predictions
- Team chemistry analysis
- Historical accuracy metrics
- Momentum tracking

## Model Performance

- **Game Winner Accuracy**: ~68% (2024-25 season)
- **Against Spread**: ~55% (2024-25 season)
- **Calibration Error**: < 3% (well-calibrated probabilities)

## Data Sources

- NBA Stats API (official stats)
- Basketball Reference (historical data)
- RapidAPI Sports (live odds)
- YouTube (highlight videos)
- Custom scrapers (commentary, social media)

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
- PyTorch and scikit-learn communities
- Next.js and React ecosystems

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
