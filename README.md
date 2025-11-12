# 🏀 NBA Game Prediction Platform# 🏀 NBA Intelligence Platform



<div align="center">A production-quality, full-stack ML system for NBA game predictions, live win probability, player chemistry analysis, and social sentiment integration.



[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)## Features

[![Poetry](https://img.shields.io/badge/Poetry-1.5+-purple.svg)](https://python-poetry.org/)

[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)- **Pregame Predictions**: Elo ratings + LightGBM with calibrated probabilities

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)- **Live Win Probability**: GRU-based possession-by-possession updates

[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)- **Video Highlights**: Automated detection of dunks, blocks, assists, and foul candidates

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)- **Player Chemistry**: Graph Neural Network analysis of lineup synergies

- **Social Signals**: Sentiment and stance analysis from Twitter/X, Reddit, YouTube

**State-of-the-art NBA game prediction system powered by ensemble machine learning, advanced analytics, and real-time data**- **Explainability**: SHAP values for model interpretability



[Features](#-key-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [API Docs](#-api-documentation) • [Contributing](#-contributing)## Architecture



</div>\`\`\`

┌─────────────────┐

---│   Next.js Web   │  ← User Interface (http://localhost:3000)

└────────┬────────┘

## 🎯 Project Overview         │

┌────────▼────────┐

This platform predicts NBA game outcomes with **68-72% accuracy** using:│   FastAPI       │  ← REST API (http://localhost:8000)

- **165+ advanced features** including offensive/defensive ratings, four factors, clutch stats└────────┬────────┘

- **Ensemble ML models** (XGBoost + LightGBM + CatBoost)         │

- **Real-time data** from NBA.com, ESPN, and live odds┌────────▼────────────────────────────┐

- **News sentiment analysis** powered by NLP│  ML Models                          │

- **Player tracking metrics** (speed, distance, hustle stats)│  • LightGBM (pregame)               │

│  • GRU (live)                       │

### 📊 Model Performance│  • MobileNetV3 (vision)             │

│  • GraphSAGE (chemistry)            │

| Metric | Current | Target |│  • DistilBERT (sentiment)           │

|--------|---------|--------|└────────┬────────────────────────────┘

| **Cross-Validation Accuracy** | 62.6% | 68-72% |         │

| **Training Accuracy** | 81% | 85-88% |┌────────▼────────────────────────────┐

| **AUC-ROC Score** | 0.94 | 0.96-0.97 |│  Data Layer                         │

| **Features** | 27 → **165+** | Comprehensive |│  • PostgreSQL (structured)          │

│  • Redis (cache)                    │

---│  • Parquet (features)               │

└─────────────────────────────────────┘

## ✨ Key Features\`\`\`



### 🤖 Machine Learning## Quick Start

- **Ensemble Models**: Stacked XGBoost, LightGBM, CatBoost with soft voting

- **Advanced Feature Engineering**: 165+ features including:### Prerequisites

  - Offensive/Defensive ratings (per 100 possessions)

  - Four Factors (eFG%, TOV%, OREB%, FT Rate)- macOS with Apple Silicon (M1/M2/M3)

  - Clutch performance (last 5 minutes, close games)- 24 GB RAM

  - Recent form (last 5, 10, 15 games momentum)- Python 3.11+

  - Player tracking (speed, distance, touches, drives)- Node.js 20+

  - News sentiment analysis (team morale indicators)- Docker Desktop

- **Hyperparameter Tuning**: Automated grid search with cross-validation

- **Model Explainability**: SHAP values for prediction interpretability### Installation



### 📈 Data Sources1. **Clone and setup**

- **NBA.com Stats API**: Official advanced metrics (OFF_RATING, DEF_RATING, NET_RATING, PACE, PIE)   \`\`\`bash

- **ESPN**: Team news, injury reports, betting odds   git clone <repo-url>

- **nba_api**: Live scores, schedules, player stats   cd nba-intel

- **The Odds API**: Real-time betting lines and movements   make setup

   \`\`\`

### 🎨 User Interface

- **Next.js 14 Frontend**: Modern, responsive React application2. **Configure API keys**

- **Real-time Predictions**: Live game predictions updated every 15 minutes   \`\`\`bash

- **Interactive Dashboard**: Charts, confidence meters, feature importance   cp .env.example .env

- **Team Comparison**: Head-to-head analytics with advanced metrics   # Edit .env and fill in your API keys (see KEYS.md)

- **Historical Performance**: Track model accuracy over time   \`\`\`



### ⚡ Backend3. **Verify keys**

- **FastAPI**: High-performance async API (8000 req/s)   \`\`\`bash

- **PostgreSQL**: Robust data storage with indexing   make key-audit

- **Redis Caching**: Sub-100ms response times   \`\`\`

- **Docker**: Containerized deployment

4. **Start services**

---   \`\`\`bash

   make up

## 🚀 Quick Start   \`\`\`



### Prerequisites5. **Seed data**

- Python 3.10+   \`\`\`bash

- Poetry 1.5+   make seed

- Node.js 18+   \`\`\`

- Docker (optional)

6. **Build features**

### Installation   \`\`\`bash

   make data

```bash   \`\`\`

# Clone repository

git clone https://github.com/ShauryaMallampati/NBA-Prediction.git7. **Train models**

cd NBA-Prediction   \`\`\`bash

   make train-pregame

# Install Python dependencies   make train-live

poetry install   make train-chemistry

   \`\`\`

# Install Node dependencies

npm install8. **Run the platform**

   \`\`\`bash

# Set up environment variables   # Terminal 1: API

cp .env.example .env   make serve

# Edit .env with your API keys

```   # Terminal 2: Web (in a new terminal)

   make web

### Running the Application   \`\`\`



```bash9. **Open browser**

# Start backend API   Navigate to `http://localhost:3000`

poetry run uvicorn src.api.main:app --reload --port 8000

## Project Structure

# Start frontend (in another terminal)

npm run dev\`\`\`

nba-intel/

# Visit http://localhost:3000├── app/                 # Next.js frontend

```│   ├── layout.tsx

│   ├── page.tsx

### Docker Deployment│   ├── schedule/

│   ├── live/

```bash│   └── postgame/

# Build and run with Docker Compose├── src/                 # Python backend

docker-compose up -d│   ├── common/          # Config, logging, validators

│   ├── data/            # Ingestion & preprocessing

# Application available at http://localhost:3000│   ├── models/          # ML models

# API documentation at http://localhost:8000/docs│   └── services/        # FastAPI

```├── configs/             # YAML configurations

├── notebooks/           # Jupyter analysis

---├── tests/               # Unit & integration tests

├── data/                # Local data cache (gitignored)

## 📁 Project Structure└── artifacts/           # Trained models (gitignored)

\`\`\`

```

NBA-Prediction/## API Keys Required

├── app/                          # Next.js frontend

│   ├── api/                     # API routesSee [KEYS.md](KEYS.md) for detailed instructions on obtaining each key:

│   ├── components/              # React components

│   ├── predictions/             # Prediction pages- ✓ **NBA Stats API** (RapidAPI) - Required

│   └── analytics/               # Analytics dashboard- ✓ **OpenRouteService** (travel/distance) - Required

│- ✓ **Twitter/X API v2** (optional, for sentiment)

├── src/                         # Python backend- ✓ **Reddit API** (optional, for sentiment)

│   ├── models/                  # ML models- ✓ **YouTube Data API** (optional, for sentiment)

│   │   ├── pregame/            # Pre-game prediction models

│   │   └── live/               # In-game prediction models## Development

│   ├── features/               # Feature engineering

│   ├── data/                   # Data processing### Run tests

│   └── api/                    # FastAPI endpoints\`\`\`bash

│make test

├── scripts/                     # Data collection scripts\`\`\`

│   ├── scrape_advanced_stats.py       # NBA.com advanced metrics (150+)

│   ├── scrape_news_sentiment.py       # ESPN/NBA.com news + NLP### Evaluate models

│   ├── scrape_player_tracking.py      # Player tracking & hustle stats\`\`\`bash

│   ├── scrape_live_nba_schedule.py    # Daily game schedulemake eval

│   └── generate_todays_predictions.py # Daily prediction pipeline\`\`\`

│

├── data/                        # Data storage### Clean artifacts

│   ├── advanced_stats/         # 150+ advanced metrics\`\`\`bash

│   ├── news/                   # News sentiment datamake clean

│   ├── tracking/               # Player tracking data\`\`\`

│   └── processed/              # Engineered features

│## Configuration

├── artifacts/                   # Model artifacts

│   ├── models/                 # Trained model filesAll configuration is in `configs/`:

│   ├── features/               # Feature importance- `config.yaml` - Main settings

│   └── plots/                  # Visualizations- `params_pregame.yaml` - Pregame model hyperparameters

│- `params_live.yaml` - Live model settings

├── tests/                       # Test suite- `params_vision.yaml` - Video model config

│   ├── test_models/            # Model tests- `params_chemistry.yaml` - GNN parameters

│   ├── test_features/          # Feature engineering tests- `params_social.yaml` - Social signal settings

│   └── test_api/               # API endpoint tests

│## Data Requirements

├── docs/                        # Documentation

│   ├── API.md                  # API documentationThis system uses **real data only** by default. Mock data is disabled unless `ALLOW_MOCK_DATA=true`.

│   ├── MODEL_CARD.md           # Model specifications

│   ├── FEATURES.md             # Feature descriptionsRequired data sources:

│   └── DEPLOYMENT.md           # Deployment guide- NBA game schedules and box scores (2018-2023)

│- Player statistics

├── .github/                     # GitHub Actions- Play-by-play data (for live model)

│   └── workflows/- Video clips (user-provided for highlight detection)

│       ├── ci.yml              # Continuous integration- Social media posts (if sentiment enabled)

│       ├── train-model.yml     # Automated retraining

│       └── deploy.yml          # Automated deployment## Model Performance

│

├── docker-compose.yml           # Docker orchestrationTarget metrics (validation set):

├── Dockerfile                   # Container definition- **Accuracy**: 65-70%

├── pyproject.toml              # Python dependencies- **Log Loss**: < 0.55

├── package.json                # Node dependencies- **Brier Score**: < 0.20

└── README.md                   # This file- **ECE**: < 0.05

```

## Ethical Considerations

---

- Respect API rate limits and Terms of Service

## 🏗️ Architecture- Aggregate social data; do not store PII

- Research use only; not for gambling

### Data Pipeline- See [DATA_USE.md](DATA_USE.md) for full guidelines



```## Troubleshooting

NBA.com API → Feature Engineering → ML Models → Predictions API → Next.js Frontend

ESPN Scraper ↗                                        ↓### "Missing required API keys"

News Sentiment ↗                                  DatabaseRun `make key-audit` to see which keys are missing. See KEYS.md for instructions.

```

### "Model not trained yet"

### Model ArchitectureRun `make train-pregame` to train the pregame model.



```### "No games found"

Ensemble Stacking ClassifierEnsure you've run `make seed` to download game data.

├── Level 1: Base Models

│   ├── XGBoost (boosted trees)### Docker services not starting

│   ├── LightGBM (gradient boosting)\`\`\`bash

│   └── CatBoost (categorical boosting)make down

│make up

└── Level 2: Meta-Learnerdocker-compose ps

    └── Logistic Regression (soft voting)\`\`\`

```

### Frontend not loading

### Feature Categories (165+ total)\`\`\`bash

cd nba-intel

1. **Base Stats** (20): W%, PTS, REB, AST, etc.npm install

2. **Injuries** (7): Injured stars, injury impactnpm run dev

3. **Advanced Stats** (30+): OFF_RATING, DEF_RATING, NET_RATING, PACE, PIE\`\`\`

4. **Four Factors** (12): eFG%, TOV%, OREB%, FT Rate

5. **Opponent Stats** (25+): Defensive metrics## Make Targets

6. **Clutch Stats** (20+): Close game performance

7. **Recent Form** (60+): Last 5/10/15 games momentum\`\`\`bash

8. **Player Tracking** (20+): Speed, distance, hustle statsmake help              # Show all available commands

9. **News Sentiment** (8): Team morale indicatorsmake setup             # Install dependencies

make up                # Start Docker services

---make down              # Stop Docker services

make key-audit         # Verify API keys

## 📡 API Documentationmake seed              # Download real data

make data              # Build features

### Endpointsmake train-pregame     # Train pregame model

make train-live        # Train live model

#### Get Today's Predictionsmake train-vision      # Train video model

```bashmake train-chemistry   # Train GNN

GET /predictionsmake social-build      # Build social features

```make eval              # Run evaluations

make serve             # Start FastAPI (port 8000)

**Response:**make web               # Start Next.js (port 3000)

```jsonmake test              # Run tests

{make clean             # Clean artifacts

  "date": "2024-11-12",\`\`\`

  "predictions": [

    {## Contributing

      "game_id": "0022400123",

      "home_team": "BOS",1. Install pre-commit hooks: `poetry run pre-commit install`

      "away_team": "LAL",2. Run tests before committing: `make test`

      "predicted_winner": "BOS",3. Follow code style: `ruff` + `black` + `mypy`

      "win_probability": 0.73,

      "confidence": "high",## License

      "key_factors": [

        "BOS offensive rating: 118.5 (league-leading)",MIT License - see [LICENSE](LICENSE)

        "LAL on 3-game road trip (fatigue factor)",

        "Recent form: BOS 8-2 L10, LAL 5-5 L10"## Support

      ]

    }For issues or questions, open a GitHub issue or consult the documentation in `notebooks/`.

  ]

}---

```

**Built with**: Python 3.11 • PyTorch • FastAPI • Next.js • PostgreSQL • Redis

**Full API docs:** http://localhost:8000/docs (when running)\`\`\`



---```makefile file="Makefile"

.PHONY: help setup up down key-audit seed data train-pregame train-live train-vision train-chemistry social-build eval serve web test clean

## 🧪 Testing

help:

```bash	@echo "NBA Intelligence Platform - Make targets:"

# Run all tests	@echo "  setup            - Install Python/Node deps; install pre-commit"

poetry run pytest	@echo "  up               - Start Postgres + Redis via Docker"

	@echo "  down             - Stop services"

# Run with coverage	@echo "  key-audit        - Print which required keys are present; ping providers"

poetry run pytest --cov=src --cov-report=html	@echo "  seed             - Download real data; write parquet caches; validate"

	@echo "  data             - Build all features (tabular/seq/graph/social) from real data"

# View coverage report	@echo "  train-pregame    - Train GBM + calibration; save artifacts"

open htmlcov/index.html	@echo "  train-live       - Train GRU sequence model"

```	@echo "  train-vision     - Train clip classifier"

	@echo "  train-chemistry  - Train GNN; export lineup embeddings"

---	@echo "  social-build     - Run social ETL + aggregates + social graph edges"

	@echo "  eval             - Run ablations, calibration, notebooks → artifacts/"

## 📊 Model Training	@echo "  serve            - Start FastAPI"

	@echo "  web              - Start Next.js"

```bash	@echo "  test             - Run pytest suite"

# Collect data	@echo "  clean            - Remove artifacts and caches"

poetry run python scripts/scrape_advanced_stats.py

poetry run python scripts/scrape_news_sentiment.pysetup:

	@echo "Installing Python dependencies..."

# Engineer features	poetry install

poetry run python src/features/engineer_features.py	@echo "Installing pre-commit hooks..."

	poetry run pre-commit install

# Train ensemble model	@echo "Installing Node dependencies..."

poetry run python src/models/pregame/train_ensemble.py	npm install

```	@echo "Setup complete!"



---up:

	docker-compose up -d

## 🔧 Configuration	@echo "Waiting for services to be healthy..."

	@sleep 5

### Environment Variables	docker-compose ps



```bashdown:

# API Keys	docker-compose down

NBA_API_KEY=your_nba_api_key

ODDS_API_KEY=your_odds_api_keykey-audit:

	poetry run python -m src.common.key_audit

# Database

DATABASE_URL=postgresql://user:pass@localhost:5432/nba_predictionsseed:

	poetry run python -m src.data.ingest.seed_all

# Redis Cache

REDIS_URL=redis://localhost:6379data:

	poetry run python -m src.data.preprocess.build_pregame_features

# Model Settings	poetry run python -m src.data.preprocess.build_live_sequences

MODEL_VERSION=v2.0	poetry run python -m src.data.preprocess.build_lineup_graph

CONFIDENCE_THRESHOLD=0.65	@if [ "$$ENABLE_SENTIMENT" = "true" ]; then \

FEATURE_COUNT=165		poetry run python -m src.data.preprocess.build_social_aggregates; \

```	fi



---train-pregame:

	poetry run python -m src.models.pregame.train_lgbm

## 🤝 Contributing

train-live:

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.	poetry run python -m src.models.live.train_gru



### Development Setuptrain-vision:

	poetry run python -m src.models.vision.train_classifier

```bash

# Fork and clone repositorytrain-chemistry:

git clone https://github.com/YOUR_USERNAME/NBA-Prediction.git	poetry run python -m src.models.chemistry.train_gnn

cd NBA-Prediction

social-build:

# Create virtual environment	poetry run python -m src.models.sentiment.stance_and_sentiment

poetry install	poetry run python -m src.data.preprocess.join_social_to_graph



# Create feature brancheval:

git checkout -b feature/amazing-feature	poetry run python -m src.models.pregame.evaluate

	poetry run jupyter nbconvert --execute --to html notebooks/*.ipynb

# Make changes and test

poetry run pytestserve:

	poetry run uvicorn src.services.api.main:app --reload --host 0.0.0.0 --port 8000

# Commit and push

git commit -m "Add amazing feature"web:

git push origin feature/amazing-feature	npm run dev



# Open Pull Requesttest:

```	poetry run pytest tests/ -v --cov=src --cov-report=html



---clean:

	rm -rf artifacts/*.pkl artifacts/*.json

## 📝 License	rm -rf data/cache/*

	find . -type d -name __pycache__ -exec rm -rf {} +

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.	find . -type f -name "*.pyc" -delete


---

## 🙏 Acknowledgments

- **NBA.com** for official statistics API
- **ESPN** for news and injury data
- **The Odds API** for betting line data
- **nba_api** Python library
- **Dean Oliver** for Four Factors methodology

---

## 📮 Contact

**Shaurya Mallampati**
- GitHub: [@ShauryaMallampati](https://github.com/ShauryaMallampati)
- Project: [NBA-Prediction](https://github.com/ShauryaMallampati/NBA-Prediction)

---

## 🗺️ Roadmap

### Phase 1: Core Features ✅
- [x] Basic prediction model (81% training accuracy)
- [x] Real NBA data integration
- [x] Frontend dashboard
- [x] API endpoints

### Phase 2: Advanced Analytics ✅
- [x] 165+ advanced features
- [x] News sentiment analysis
- [x] Player tracking stats
- [x] Ensemble stacking model

### Phase 3: Production Ready 🚧
- [ ] SHAP explainability
- [ ] Automated retraining pipeline
- [ ] Performance monitoring
- [ ] Docker deployment

### Phase 4: Enhanced Features 📋
- [ ] Live in-game predictions
- [ ] Lineup optimization
- [ ] Player prop predictions
- [ ] Mobile app

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ by [Shaurya Mallampati](https://github.com/ShauryaMallampati)

</div>
