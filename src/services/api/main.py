"""FastAPI main application."""

import pickle
from datetime import date
from typing import List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.common.config import settings
from src.common.logger import setup_logger
from src.common.paths import Paths

logger = setup_logger(__name__)

app = FastAPI(
    title="NBA Intelligence Platform API",
    description="ML-powered NBA predictions and analytics",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# DTOs
class PredictionResponse(BaseModel):
    game_id: str
    date: str
    home_team: str
    away_team: str
    home_win_prob: float
    away_win_prob: float
    top_features: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    models_loaded: bool


# Global model cache
_model_cache = {}


def load_model(model_name: str):
    """Load model from disk (cached)."""
    if model_name not in _model_cache:
        model_path = Paths.MODELS / f"{model_name}.pkl"
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        with open(model_path, "rb") as f:
            _model_cache[model_name] = pickle.load(f)
        logger.info(f"Loaded model: {model_name}")
    return _model_cache[model_name]


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    models_exist = (Paths.MODELS / "pregame_lgbm.pkl").exists()
    return HealthResponse(status="healthy", version="0.1.0", models_loaded=models_exist)


@app.get("/predictions", response_model=List[PredictionResponse])
async def get_predictions(date: Optional[str] = None):
    """Get pregame predictions for a date."""
    if date is None:
        date = str(date.today())

    logger.info(f"Fetching predictions for {date}")

    # Load games for date (simplified - would query DB in production)
    games_df = pd.read_parquet(Paths.RAW / "games.parquet")
    games_df = games_df[games_df["date"] == date]

    if games_df.empty:
        return []

    # Load model
    try:
        model = load_model("pregame_lgbm")
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Model not trained yet. Run 'make train-pregame'")

    # Generate predictions (simplified - would use full feature pipeline)
    predictions = []
    for _, game in games_df.iterrows():
        # Mock features for demo
        features = pd.DataFrame(
            [
                {
                    "is_home": 1,
                    "days_rest": 2,
                    "is_back_to_back": 0,
                    "pts_last_3": 110,
                    "pts_last_5": 108,
                    "pts_last_10": 107,
                    "margin_last_3": 5,
                    "margin_last_5": 3,
                    "margin_last_10": 2,
                }
            ]
        )

        home_win_prob = float(model.predict_proba(features)[0][1])

        predictions.append(
            PredictionResponse(
                game_id=str(game["game_id"]),
                date=date,
                home_team=game["home_team_name"],
                away_team=game["away_team_name"],
                home_win_prob=home_win_prob,
                away_win_prob=1 - home_win_prob,
            )
        )

    logger.info(f"Generated {len(predictions)} predictions")
    return predictions


@app.get("/game/{game_id}/live")
async def get_live_win_prob(game_id: str):
    """Get live win probability for a game."""
    # Placeholder - would integrate with live data stream
    return {
        "game_id": game_id,
        "current_quarter": 3,
        "time_remaining": "5:23",
        "home_win_prob": 0.68,
        "possession_history": [],
    }


@app.get("/explain/{game_id}")
async def explain_prediction(game_id: str):
    """Get SHAP explanation for a prediction."""
    # Placeholder - would compute SHAP values
    return {
        "game_id": game_id,
        "top_features": {
            "home_advantage": 0.15,
            "rest_differential": 0.08,
            "recent_form": 0.12,
            "lineup_chemistry": 0.06,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
