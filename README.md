# NBA Prediction Platform 🏀

An **ML-powered prediction system** for NBA games with multi-modal AI, explainable predictions, and automated accuracy tracking.

## Features

- **Ensemble Model**: XGBoost + LightGBM + CatBoost (67.7% accuracy)
- **Vision CNN**: VideoMAE-based video analysis for game footage understanding
- **Player Chemistry**: Graph-based player synergy analysis
- **Explainable AI**: SHAP-based feature importance for every prediction
- **Daily Automation**: GitHub Actions auto-fetches results and tracks accuracy
- **Modern Frontend**: Next.js dark-mode dashboard with real-time predictions
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

Visit: http://localhost:3000

## AI Agent Workflow

### 1. Vision CNN Training
Train the 3D CNN on your local dataset:
```bash
poetry run python scripts/train_vision_cnn.py
```

### 2. Daily Vision Agent
Find yesterday's highlights and "watch" them for self-supervised learning:
```bash
poetry run python scripts/daily_vision_agent.py
```

### 3. Post-Game Analysis
Generate AI reasoning for why predictions were wrong using Qwen2.5-3B + Web Scraping:
```bash
poetry run python scripts/analyze_wrong_predictions.py
```
*Note: These insights are automatically displayed on the `/analysis` page.*

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    World Model Ensemble                      │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   XGBoost    │   LightGBM   │   CatBoost   │  Vision CNN    │
│ (stats-based)│ (stats-based)│ (stats-based)│ (video-based)  │
└──────────────┴──────────────┴──────────────┴────────────────┘
```

## Datasets Used

| Dataset | Description | Source |
|---------|-------------|--------|
| **BASKET** (CVPR 2025) | 4,477 hours of basketball video, 32K players | [HuggingFace](https://huggingface.co/datasets/yulupan/BASKET) |
| **Basketball-51** | 51 basketball activity classes | [Kaggle](https://www.kaggle.com/datasets/sarbagyashakya/basketball-51-dataset) |
| **NBA Stats API** | Live game statistics | [nba_api](https://github.com/swar/nba_api) |
| **The Odds API** | Real-time betting odds | [The Odds API](https://the-odds-api.com/) |

## Project Structure

```
├── app/                 # Next.js frontend
├── src/
│   ├── api/             # FastAPI endpoints
│   ├── models/          # ML models
│   │   ├── vision/      # Vision CNN (VideoMAE)
│   │   └── chemistry_gnn.py  # Player chemistry
│   └── common/          # Shared utilities
├── scripts/             # Automation scripts
├── colab/               # Cloud training notebooks
│   └── train_vision_cnn.ipynb
└── .github/workflows/   # GitHub Actions
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/predictions` | Today's game predictions |
| `/accuracy` | Dynamic accuracy stats |
| `/live_schedule` | 14-day game schedule |
| `/explain/{game_id}` | SHAP explanation |
| `/chemistry/league` | Team chemistry rankings |

## Tech Stack

- **Backend**: Python, FastAPI, XGBoost, LightGBM, CatBoost
- **Vision**: VideoMAE, TimeSformer (HuggingFace Transformers)
- **Frontend**: Next.js, TypeScript
- **Data**: NBA API, Odds API, Supabase
- **ML**: Ensemble learning, SHAP, Platt scaling

## License

MIT

