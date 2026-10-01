"""Local HTTP API for predictions from trusted, prepared ensemble artifacts."""

import asyncio
import logging
import pickle
from datetime import date as calendar_date
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.common.config import settings
from src.common.paths import Paths
from src.models.pregame.predictor import EnsemblePredictor
from src.services.prediction_service import prediction_records

logger = logging.getLogger(__name__)
app = FastAPI(title="NBA Game Predictor", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


class PredictionResponse(BaseModel):
    game_id: str
    date: str
    home_team: str
    away_team: str
    home_win_prob: float = Field(ge=0, le=1)
    away_win_prob: float = Field(ge=0, le=1)
    top_features: dict | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    models_loaded: bool


@lru_cache(maxsize=1)
def _get_predictor(model_dir: Path) -> EnsemblePredictor:
    # Artifacts are immutable while serving; restart the process after replacing them.
    return EnsemblePredictor(model_dir)


def _predict(target_date, home_team, away_team):
    predictor = _get_predictor(Paths.MODELS / "pregame")
    return prediction_records(
        predictor, Paths.ARTIFACTS / "features" / "pregame.parquet",
        target_date, home_team, away_team,
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Report process liveness and actual cached model state, not file existence."""
    return HealthResponse(
        status="running", version="0.1.0",
        models_loaded=_get_predictor.cache_info().currsize > 0,
    )


@app.get("/predictions", response_model=list[PredictionResponse])
async def get_predictions(
    date: calendar_date | None = None,
    home_team: str | None = Query(default=None, min_length=1, max_length=80, pattern=r".*\S.*"),
    away_team: str | None = Query(default=None, min_length=1, max_length=80, pattern=r".*\S.*"),
):
    """Return matching prepared predictions; this endpoint does not fetch live data."""
    try:
        return await asyncio.to_thread(_predict, date or calendar_date.today(), home_team, away_team)
    except FileNotFoundError as exc:
        logger.warning("Prediction artifacts unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="Models or prepared features are missing.") from exc
    except (ValueError, ImportError, pickle.UnpicklingError, EOFError) as exc:
        logger.warning("Prediction artifacts invalid or incompatible: %s", exc)
        raise HTTPException(
            status_code=503, detail="Prediction artifacts are invalid or incompatible; see server logs."
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Prediction request failed")
        raise HTTPException(status_code=500, detail="Prediction failed; see server logs.") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
