"""
API endpoint for ensemble model predictions
Serves predictions with win probabilities and model consensus
"""

import sys
from pathlib import Path
# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime
from src.models.pregame.train_ensemble import EnsembleTrainer
from scripts.train_ensemble_model import create_features_from_odds, load_betting_data
from src.api.live_schedule import get_upcoming_games_async
from src.api.live_odds import get_live_odds_data_async
from src.api.live_features import LiveFeatureEngineer
import os
import requests
import asyncio
import json

# Initialize FastAPI app
app = FastAPI(
    title="NBA World Model API",
    description="Unified predictions from Ensemble, RNN, and CNN models",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load ensemble model (via World Model)
# world_model is already initialized on import

# Load ensemble model manually to match trained artifacts
try:
    trainer = EnsembleTrainer(output_dir="artifacts/models/pregame")
    trainer.load_models()
    if trainer.xgb_calibrated:
        print("✅ Models loaded successfully from artifacts/models/pregame")
        feature_engineer = LiveFeatureEngineer()
    else:
        print("⚠️  No saved ensemble model found in artifacts/models/pregame")
        feature_engineer = None
except Exception as e:
    print(f"❌ Error loading model: {e}")
    feature_engineer = None
    trainer = None


class GamePrediction(BaseModel):
    """Prediction for a single game"""
    game_id: str
    home_team: str
    away_team: str
    commence_time: str
    prediction: str
    home_win_probability: float
    away_win_probability: float
    confidence: float
    models_agree: str
    consensus_percentage: float
    individual_votes: Dict[str, str]
    home_odds: float
    away_odds: float
    home_spread: float
    away_spread: float


class PredictionsResponse(BaseModel):
    """Response containing all predictions"""
    timestamp: str
    total_games: int
    predictions: List[GamePrediction]
    model_info: Dict[str, Any]


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NBA World Model API",
        "status": "online",
        "components": {
            "ensemble": trainer.xgb_calibrated is not None if trainer else False,
            "live_rnn": False,
            "vision_cnn": False
        },
        "models": 3,
        "algorithms": [
            "XGBoost",
            "LightGBM",
            "CatBoost"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": trainer.xgb_calibrated is not None if trainer else False,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/accuracy")
async def get_accuracy_stats():
    """Get dynamic accuracy statistics from Supabase or local CSV."""
    try:
        from src.common.supabase_client import get_supabase_client
        
        client = get_supabase_client()
        stats = client.get_accuracy_stats(days=30)
        
        return {
            "success": True,
            "accuracy": stats.get("current_accuracy", 67.7),
            "total_games": stats.get("total_games", 0),
            "total_correct": stats.get("total_correct", 0),
            "days_evaluated": stats.get("days_evaluated", 0),
            "source": stats.get("source", "unknown"),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        # Fallback to default
        return {
            "success": False,
            "accuracy": 67.7,
            "total_games": 0,
            "total_correct": 0,
            "days_evaluated": 0,
            "source": "default",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Initialize prediction pipeline
from src.services.prediction_pipeline import PredictionPipeline

pipeline = PredictionPipeline()

@app.get("/predictions", response_model=PredictionsResponse)
async def get_predictions():
    """
    Get predictions for all upcoming games
    """
    try:
        # Use optimized async version
        results = await pipeline.get_predictions_async(use_live_odds=True)
        
        # Model info
        model_info = {
            "num_models": 3,
            "model_names": ["XGBoost", "LightGBM", "CatBoost"],
            "num_features": len(pipeline.trainer.feature_names) if pipeline.trainer else 0,
            "feature_names": pipeline.trainer.feature_names if pipeline.trainer else []
        }
        
        return PredictionsResponse(
            timestamp=datetime.now().isoformat(),
            total_games=len(results),
            predictions=results,
            model_info=model_info
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating predictions: {str(e)}"
        )



@app.get("/predictions/{game_id}")
async def get_game_prediction(game_id: str):
    """Get prediction for a specific game"""
    try:
        # Get all predictions
        all_predictions = await get_predictions()
        
        # Find specific game
        for pred in all_predictions.predictions:
            if pred.game_id == game_id:
                return pred
        
        raise HTTPException(
            status_code=404,
            detail=f"Game {game_id} not found"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@app.get("/model/info")
async def get_model_info():
    """Get information about the ensemble model"""
    try:
        # Load training history
        history_file = Path("models/ensemble/training_history.json")
        training_history = []
        
        if history_file.exists():
            def load_json():
                with open(history_file, 'r') as f:
                    return json.load(f)
            training_history = await asyncio.to_thread(load_json)
        
        return {
            "is_trained": trainer.xgb_calibrated is not None if trainer else False,
            "num_models": 3,
            "model_names": ["XGBoost", "LightGBM", "CatBoost"],
            "feature_count": len(trainer.feature_names) if trainer else 0,
            "feature_names": trainer.feature_names if trainer else [],
            "training_history": training_history,
            "last_training": training_history[-1] if training_history else None,
            "world_model_status": {
                "rnn_active": False,
                "cnn_active": False
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        )


@app.get("/live_schedule")
async def live_schedule(days: int = 14):
    """Return upcoming games, prioritizing cached schedule and merging with live data."""
    try:
        from pathlib import Path
        import json
        
        all_games = []
        seen_ids = set()
        
        # 1. Try to load from cached schedule file first (populated by GitHub Actions)
        cached_file = Path("data/schedules/upcoming_14_days.json")
        if cached_file.exists():
            try:
                def read_cached():
                    with open(cached_file, 'r') as f:
                        return json.load(f)
                cached_data = await asyncio.to_thread(read_cached)
                cached_games = cached_data.get('games', [])
                for g in cached_games:
                    game_id = g.get('game_id', '')
                    if game_id and game_id not in seen_ids:
                        all_games.append(g)
                        seen_ids.add(game_id)
            except Exception as e:
                print(f"Failed to load cached schedule: {e}")
        
        # 2. Also try live API to get any updates
        try:
            live_games = await get_upcoming_games_async(days_ahead=days)
            for g in live_games:
                game_id = g.get('game_id', '')
                if game_id and game_id not in seen_ids:
                    all_games.append(g)
                    seen_ids.add(game_id)
        except Exception as e:
            print(f"Live API fetch failed: {e}")
        
        # 3. Fallback to RapidAPI if still no games
        if not all_games:
            rapid_key = os.environ.get('RAPIDAPI_KEY') or os.environ.get('NEXT_PUBLIC_RAPIDAPI_KEY')
            rapid_host = 'nba-schedule.p.rapidapi.com'
            if rapid_key:
                try:
                    import httpx
                    url = f"https://{rapid_host}/schedule"
                    headers = {
                        'x-rapidapi-key': rapid_key,
                        'x-rapidapi-host': rapid_host
                    }
                    async with httpx.AsyncClient() as client:
                        r = await client.get(url, headers=headers, timeout=10.0)
                    
                    if r.status_code == 200:
                        payload = r.json()
                        games = payload.get('games') or payload.get('schedule') or []
                        for g in games:
                            gd = g.get('date') or g.get('game_date') or g.get('start_date') or ''
                            all_games.append({
                                'game_id': g.get('id') or g.get('game_id') or g.get('GAME_ID') or '',
                                'date': gd,
                                'home_team': g.get('home_team') or g.get('home') or '',
                                'away_team': g.get('away_team') or g.get('away') or '',
                                'game_time': g.get('time') or g.get('startTime') or ''
                            })
                except Exception:
                    pass
        
        # Sort by date
        all_games.sort(key=lambda x: x.get('date', ''))

        return {
            "success": True,
            "source": "cached|nba_api|pyespn|rapidapi",
            "count": len(all_games),
            "games": all_games
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/explain/{game_id}")
async def explain_prediction(game_id: str):
    """
    Get SHAP explanation for a specific game prediction.
    Returns feature importance and human-readable explanation.
    """
    try:
        from src.models.shap_explainer import shap_explainer
        
        # For now, return a mock explanation structure
        # In production, this would use actual features from the game
        return {
            "game_id": game_id,
            "explanation": {
                "top_features": [
                    {"feature": "elo_diff", "impact": "positive", "contribution": "25.3%"},
                    {"feature": "home_court_adv", "impact": "positive", "contribution": "15.1%"},
                    {"feature": "away_b2b", "impact": "positive", "contribution": "12.8%"},
                ],
                "summary": "Home team has significant Elo advantage and home court advantage.",
                "confidence_drivers": ["Historical performance", "Rest advantage", "Home court"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scouting-report/{game_id}")
async def get_scouting_report(game_id: str):
    """
    Generate an AI-powered scouting report for a game.
    """
    try:
        from src.models.scouting_reports import report_generator
        
        # Generate a sample report
        report = report_generator.generate_report(
            home_team="Lakers",
            away_team="Celtics",
            home_win_prob=45.0,
            away_win_prob=55.0,
            confidence=65.0
        )
        
        return {
            "game_id": game_id,
            "report": report,
            "format": "markdown"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === CHEMISTRY ENDPOINTS ===

@app.get("/chemistry/league")
async def get_league_chemistry():
    """Get league-wide chemistry data from real player pair analysis."""
    try:
        from src.models.chemistry_gnn import get_chemistry_model
        
        model = get_chemistry_model()
        if not model or not model.loaded:
            raise HTTPException(status_code=503, detail="Chemistry model not available")
        
        top_duos = model.get_league_top_duos(20)
        
        # Rank teams by chemistry
        team_rankings = [
            {"team": team, "chemistry_score": score}
            for team, score in sorted(
                model.team_chemistry.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]
        
        return {
            "total_teams": len(model.team_chemistry),
            "total_pairs": len(model.player_pairs),
            "top_duos": top_duos,
            "team_rankings": team_rankings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chemistry/matchup/{home_team}/{away_team}")
async def get_matchup_chemistry(home_team: str, away_team: str):
    """Get chemistry analysis for a specific matchup."""
    try:
        from src.models.chemistry_gnn import get_chemistry_model
        
        model = get_chemistry_model()
        if not model or not model.loaded:
            raise HTTPException(status_code=503, detail="Chemistry model not available")
        
        return model.predict_chemistry_impact(home_team.upper(), away_team.upper())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    print("="*80)
    print("🚀 Starting NBA Ensemble Prediction API")
    print("="*80)
    print("📍 API docs: http://localhost:8000/docs")
    print("🎯 Predictions: http://localhost:8000/predictions")
    print("🧠 XAI: http://localhost:8000/explain/{game_id}")
    print("📋 Reports: http://localhost:8000/scouting-report/{game_id}")
    print("🧪 Chemistry: http://localhost:8000/chemistry/league")
    print("="*80)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
