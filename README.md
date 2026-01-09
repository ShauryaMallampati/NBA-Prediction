# NBA Prediction Platform �

An **ML-powered prediction system** for NBA games with explainable AI and automated accuracy tracking.

## Features

- **Ensemble Model**: XGBoost + LightGBM + CatBoost (67.7% accuracy)
- **Explainable AI**: SHAP-based feature importance for every prediction
- **Daily Automation**: Auto-fetches results and tracks prediction accuracy
- **Modern Frontend**: Next.js dashboard with real-time predictions
- **Betting Strategy**: Kelly Criterion for optimal bet sizing

## Quick Start

```bash
# Install dependencies
poetry install
npm install

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Start API server
poetry run python src/api/ensemble_predictions.py

# Start frontend (separate terminal)
npm run dev
```

Visit: http://localhost:3000/ensemble-predictions

## Daily Predictions

Run automatically each morning:
```bash
poetry run python scripts/daily_runner.py
```

This script:
1. Fetches yesterday's actual results
2. Compares predictions vs actuals
3. Logs accuracy to database
4. Generates new predictions for today

## Project Structure

```
├── app/                 # Next.js frontend
├── src/
│   ├── api/             # FastAPI endpoints
│   ├── models/          # ML models & training
│   └── common/          # Shared utilities
├── scripts/             # Automation scripts
├── artifacts/           # Model artifacts & data
└── tests/               # Test suite
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/predictions` | Today's game predictions |
| `/explain/{game_id}` | SHAP explanation |
| `/scouting-report/{game_id}` | AI-generated report |
| `/health` | Service health check |

## Tech Stack

- **Backend**: Python, FastAPI, scikit-learn, XGBoost
- **Frontend**: Next.js, TypeScript, Tailwind CSS
- **Data**: NBA API, Odds API
- **ML**: Ensemble learning, SHAP, calibrated classifiers

## License

MIT
