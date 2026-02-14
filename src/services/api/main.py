"""Main FastAPI server for pregame NBA predictions."""

import asyncio
from typing import List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.common.config import settings
from src.common.logger import setup_logger
from src.common.paths import Paths
from src.data.ingest.cache_manager import get_cache_manager

logger = setup_logger(__name__)

app = FastAPI(
    title="NBA Intelligence Platform API",
    description="Pregame NBA predictions API",
    version="0.1.0",
)

# Allow cross-origin requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response models for type safety
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




@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Quick health check - just confirms the API is running."""
    models_exist = (Paths.MODELS / "pregame" / "ensemble_metadata.json").exists()
    return HealthResponse(status="healthy", version="0.1.0", models_loaded=models_exist)


@app.get("/predictions", response_model=List[PredictionResponse])
async def get_predictions(date: Optional[str] = None, home_team: Optional[str] = None, away_team: Optional[str] = None):
    """Get game predictions from our ensemble model.
    
    We're using XGBoost, LightGBM, and CatBoost together for better accuracy.
    
    Args:
        date: Optional date in YYYY-MM-DD format (defaults to today)
        home_team: Optional home team abbreviation for specific game prediction
        away_team: Optional away team abbreviation for specific game prediction
    
    Returns:
        List of predictions with probabilities and feature importance
    """
    try:
        cache = get_cache_manager()
        cache_key = cache._make_key("api_predictions", date or "today", home_team or "", away_team or "")
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        # Load ensemble predictor
        from src.models.pregame.predictor import EnsemblePredictor
        predictor = EnsemblePredictor(str(Paths.MODELS / "pregame"))
        
        # Load features
        features_path = Paths.ARTIFACTS / "features" / "pregame.parquet"
        if not features_path.exists():
            raise HTTPException(
                status_code=503,
                detail="Features not found. Run feature engineering first."
            )
        
        # Use asyncio.to_thread to avoid blocking the event loop
        df = await asyncio.to_thread(pd.read_parquet, features_path)
        
        # Convert dates to string format for comparison (handle both ISO and simple date formats)
        if 'date' in df.columns:
            df['date_str'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
        
        # Filter by date if provided
        if date:
            df = df[df['date_str'] == date] if 'date_str' in df.columns else df
        else:
            # Get today's games or latest games
            if 'date_str' in df.columns:
                from datetime import date as date_obj
                today_str = str(date_obj.today())
                df = df[df['date_str'] == today_str]
        
        # Filter by teams if provided
        if home_team and away_team:
            df = df[
                (df['home_team'] == home_team) & (df['away_team'] == away_team)
            ]
        
        if df.empty:
            logger.warning(f"No games found for {date or 'today'}")
            return []
        
        # Get predictions with feature importance
        predictions = predictor.predict_with_features(df, top_n=5)
        
        # Build response using zip instead of iterrows() for ~10x faster iteration
        result = []
        df_records = df.to_dict('records')
        for i, row in enumerate(df_records):
            pred_data = predictions[i]
            
            # Format top features as dict
            top_features = {
                feat['feature']: {
                    'importance': feat['importance'],
                    'value': feat['value']
                }
                for feat in pred_data['top_features']
            }
            
            result.append(PredictionResponse(
                game_id=row.get('game_id', f"game_{i}"),
                date=row.get('date', date or str(date_obj.today())),
                home_team=row.get('home_team', row.get('home', 'Unknown')),
                away_team=row.get('away_team', row.get('away', 'Unknown')),
                home_win_prob=float(pred_data['prediction']),
                away_win_prob=float(1 - pred_data['prediction']),
                top_features=top_features,
            ))
        
        cache_value = [r.dict() for r in result]
        cache.set(cache_key, cache_value, ttl=300, cache_type="predictions")
        logger.info(f"Generated {len(result)} predictions using ensemble model")
        return result
    
    except Exception as e:
        logger.error(f"Error in /predictions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
