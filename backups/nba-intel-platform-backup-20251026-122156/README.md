# 🏀 NBA Intelligence Platform

A production-quality, full-stack ML system for NBA game predictions, live win probability, player chemistry analysis, and social sentiment integration.

## Features

- **Pregame Predictions**: Elo ratings + LightGBM with calibrated probabilities
- **Live Win Probability**: GRU-based possession-by-possession updates
- **Video Highlights**: Automated detection of dunks, blocks, assists, and foul candidates
- **Player Chemistry**: Graph Neural Network analysis of lineup synergies
- **Social Signals**: Sentiment and stance analysis from Twitter/X, Reddit, YouTube
- **Explainability**: SHAP values for model interpretability

## Architecture

\`\`\`
┌─────────────────┐
│   Next.js Web   │  ← User Interface (http://localhost:3000)
└────────┬────────┘
         │
┌────────▼────────┐
│   FastAPI       │  ← REST API (http://localhost:8000)
└────────┬────────┘
         │
┌────────▼────────────────────────────┐
│  ML Models                          │
│  • LightGBM (pregame)               │
│  • GRU (live)                       │
│  • MobileNetV3 (vision)             │
│  • GraphSAGE (chemistry)            │
│  • DistilBERT (sentiment)           │
└────────┬────────────────────────────┘
         │
┌────────▼────────────────────────────┐
│  Data Layer                         │
│  • PostgreSQL (structured)          │
│  • Redis (cache)                    │
│  • Parquet (features)               │
└─────────────────────────────────────┘
\`\`\`

## Quick Start

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3)
- 24 GB RAM
- Python 3.11+
- Node.js 20+
- Docker Desktop

### Installation

1. **Clone and setup**
   \`\`\`bash
   git clone <repo-url>
   cd nba-intel
   make setup
   \`\`\`

2. **Configure API keys**
   \`\`\`bash
   cp .env.example .env
   # Edit .env and fill in your API keys (see KEYS.md)
   \`\`\`

3. **Verify keys**
   \`\`\`bash
   make key-audit
   \`\`\`

4. **Start services**
   \`\`\`bash
   make up
   \`\`\`

5. **Seed data**
   \`\`\`bash
   make seed
   \`\`\`

6. **Build features**
   \`\`\`bash
   make data
   \`\`\`

7. **Train models**
   \`\`\`bash
   make train-pregame
   make train-live
   make train-chemistry
   \`\`\`

8. **Run the platform**
   \`\`\`bash
   # Terminal 1: API
   make serve

   # Terminal 2: Web (in a new terminal)
   make web
   \`\`\`

9. **Open browser**
   Navigate to `http://localhost:3000`

## Project Structure

\`\`\`
nba-intel/
├── app/                 # Next.js frontend
│   ├── layout.tsx
│   ├── page.tsx
│   ├── schedule/
│   ├── live/
│   └── postgame/
├── src/                 # Python backend
│   ├── common/          # Config, logging, validators
│   ├── data/            # Ingestion & preprocessing
│   ├── models/          # ML models
│   └── services/        # FastAPI
├── configs/             # YAML configurations
├── notebooks/           # Jupyter analysis
├── tests/               # Unit & integration tests
├── data/                # Local data cache (gitignored)
└── artifacts/           # Trained models (gitignored)
\`\`\`

## API Keys Required

See [KEYS.md](KEYS.md) for detailed instructions on obtaining each key:

- ✓ **NBA Stats API** (RapidAPI) - Required
- ✓ **OpenRouteService** (travel/distance) - Required
- ✓ **Twitter/X API v2** (optional, for sentiment)
- ✓ **Reddit API** (optional, for sentiment)
- ✓ **YouTube Data API** (optional, for sentiment)

## Development

### Run tests
\`\`\`bash
make test
\`\`\`

### Evaluate models
\`\`\`bash
make eval
\`\`\`

### Clean artifacts
\`\`\`bash
make clean
\`\`\`

## Configuration

All configuration is in `configs/`:
- `config.yaml` - Main settings
- `params_pregame.yaml` - Pregame model hyperparameters
- `params_live.yaml` - Live model settings
- `params_vision.yaml` - Video model config
- `params_chemistry.yaml` - GNN parameters
- `params_social.yaml` - Social signal settings

## Data Requirements

This system uses **real data only** by default. Mock data is disabled unless `ALLOW_MOCK_DATA=true`.

Required data sources:
- NBA game schedules and box scores (2018-2023)
- Player statistics
- Play-by-play data (for live model)
- Video clips (user-provided for highlight detection)
- Social media posts (if sentiment enabled)

## Model Performance

Target metrics (validation set):
- **Accuracy**: 65-70%
- **Log Loss**: < 0.55
- **Brier Score**: < 0.20
- **ECE**: < 0.05

## Ethical Considerations

- Respect API rate limits and Terms of Service
- Aggregate social data; do not store PII
- Research use only; not for gambling
- See [DATA_USE.md](DATA_USE.md) for full guidelines

## Troubleshooting

### "Missing required API keys"
Run `make key-audit` to see which keys are missing. See KEYS.md for instructions.

### "Model not trained yet"
Run `make train-pregame` to train the pregame model.

### "No games found"
Ensure you've run `make seed` to download game data.

### Docker services not starting
\`\`\`bash
make down
make up
docker-compose ps
\`\`\`

### Frontend not loading
\`\`\`bash
cd nba-intel
npm install
npm run dev
\`\`\`

## Make Targets

\`\`\`bash
make help              # Show all available commands
make setup             # Install dependencies
make up                # Start Docker services
make down              # Stop Docker services
make key-audit         # Verify API keys
make seed              # Download real data
make data              # Build features
make train-pregame     # Train pregame model
make train-live        # Train live model
make train-vision      # Train video model
make train-chemistry   # Train GNN
make social-build      # Build social features
make eval              # Run evaluations
make serve             # Start FastAPI (port 8000)
make web               # Start Next.js (port 3000)
make test              # Run tests
make clean             # Clean artifacts
\`\`\`

## Contributing

1. Install pre-commit hooks: `poetry run pre-commit install`
2. Run tests before committing: `make test`
3. Follow code style: `ruff` + `black` + `mypy`

## License

MIT License - see [LICENSE](LICENSE)

## Support

For issues or questions, open a GitHub issue or consult the documentation in `notebooks/`.

---

**Built with**: Python 3.11 • PyTorch • FastAPI • Next.js • PostgreSQL • Redis
\`\`\`

```makefile file="Makefile"
.PHONY: help setup up down key-audit seed data train-pregame train-live train-vision train-chemistry social-build eval serve web test clean

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
	@echo "  serve            - Start FastAPI"
	@echo "  web              - Start Next.js"
	@echo "  test             - Run pytest suite"
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

clean:
	rm -rf artifacts/*.pkl artifacts/*.json
	rm -rf data/cache/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
