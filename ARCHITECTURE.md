# NBA Intelligence Platform - Architecture

## Project Overview

A **multi-modal, explainable AI system** for NBA game prediction that combines classical machine learning, deep learning, and real-time data processing.

**Current Accuracy**: 67.7% (Ensemble of XGBoost, LightGBM, CatBoost)

---

## What Makes This Novel

### 1. Multi-Model Ensemble with Calibration
Unlike single-model approaches, we combine 3 gradient boosting algorithms with isotonic calibration for reliable probability estimates.

### 2. Explainable AI (XAI)
Every prediction comes with SHAP-based explanations showing *why* the model made its choice.

### 3. Agentic Scouting Reports
AI-generated game previews in natural language, not just numbers.

### 4. Live Feature Engineering
Real-time feature generation from historical states when live data isn't available.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │Dashboard │ │Predictions│ │Analytics │ │Scouting Reports  │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘   │
└───────┼────────────┼────────────┼────────────────┼─────────────┘
        │            │            │                │
        ▼            ▼            ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI)                          │
│  /predictions  /explain/{id}  /scouting-report/{id}  /health   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Ensemble   │   │    SHAP      │   │   Reports    │
│   Trainer    │   │  Explainer   │   │  Generator   │
│  (XGB/LGB/   │   │              │   │              │
│   CatBoost)  │   │              │   │              │
└──────┬───────┘   └──────────────┘   └──────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FEATURE ENGINEERING                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │  Elo    │ │ Streaks │ │ Form    │ │ B2B     │ │Advanced │  │
│  │ Ratings │ │         │ │ (5/10g) │ │ Flags   │ │ Stats   │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Features Used

| Category | Features |
|----------|----------|
| **Elo** | elo_home, elo_away, elo_diff |
| **Streaks** | home_win_streak, away_win_streak |
| **Form** | recent_form_5, recent_form_10 |
| **Context** | is_b2b, home_rest_days, away_rest_days |
| **Advanced** | off_rating, def_rating, pace |

---

## Comparison to Other NBA Prediction Projects

| Project | Accuracy | Models | XAI | Live |
|---------|----------|--------|-----|------|
| **This Project** | 67.7% | Ensemble (3) | ✅ SHAP | ✅ |
| NBA-Prediction-Modeling | 65.3% | Elo + ML | ❌ | ❌ |
| NBA-ML-Betting | ~69% | Neural Net | ❌ | ❌ |
| cmunch1/nba-prediction | 61.5% | Various | ❌ | ✅ |

---

## Future Improvements

1. **SVM Integration** - Research shows SVM can reach 77%+ accuracy
2. **Rolling Window Features** - 10/20/30 game rolling averages
3. **Player-Level Data** - Individual player Elo and injuries
4. **Graph Neural Networks** - Model player chemistry
5. **AutoML (AutoGluon)** - Automated hyperparameter tuning

---

## File Structure

```
src/
├── api/                    # FastAPI endpoints
│   ├── ensemble_predictions.py
│   ├── live_features.py
│   └── live_odds.py
├── models/
│   ├── pregame/           # Training scripts
│   │   └── train_ensemble.py
│   ├── shap_explainer.py  # XAI
│   ├── scouting_reports.py # Agentic reports
│   └── kelly_criterion.py # Betting strategy
├── data/
│   └── preprocess/        # Feature engineering
└── common/
    ├── config.py          # Environment settings
    └── validators.py      # API key validation
```

---

## Getting Started

```bash
# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Validate setup
poetry run python scripts/validate_keys.py

# Start API
poetry run python src/api/ensemble_predictions.py

# Start frontend
npm run dev
```
