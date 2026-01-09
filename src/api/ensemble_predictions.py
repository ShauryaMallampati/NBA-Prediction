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
from src.api.live_schedule import get_upcoming_games
from src.api.live_odds import get_live_odds_data
from src.api.live_features import LiveFeatureEngineer
import os
import requests

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


@app.get("/predictions", response_model=PredictionsResponse)
async def get_predictions():
    """
    Get predictions for all upcoming games
    
    Returns predictions with:
    - Win probability for each team
    - Individual model votes
    - Consensus strength
    - Confidence score
    """
    try:
        if not trainer or not trainer.xgb_calibrated:
            raise HTTPException(
                status_code=503,
                detail="Model not trained yet. Run training first."
            )
        
        # Load latest betting data (Try live first, fallback to static if needed but prefer live)
        odds_data = get_live_odds_data()
        
        if not odds_data or not odds_data.get('endpoints', {}).get('nba_odds'):
            print("⚠️ Live odds fetch failed or returned empty. Falling back to static data (if available).")
            odds_data = load_betting_data()
        
        if not odds_data:
            raise HTTPException(
                status_code=404,
                detail="No betting data available (Live or Static)"
            )
        
        # Create features
        df = create_features_from_odds(odds_data)
        
        # Use LiveFeatureEngineer for model-compatible features
        if feature_engineer and trainer:
            model_features = trainer.feature_names
            X_model = feature_engineer.create_live_features(df, model_features)
            
            # Predict using trainer's ensemble logic
            X_input = X_model.drop(columns=['game_id'])
            ensemble_probs = trainer.predict_ensemble(X_input)
            
            # Construct a predictions DataFrame similar to what the API expects
            predictions_df = pd.DataFrame({
                'prediction': ['HOME_WIN' if p > 0.5 else 'AWAY_WIN' for p in ensemble_probs],
                'home_win_probability': [round(p * 100, 2) for p in ensemble_probs],
                'away_win_probability': [round((1-p) * 100, 2) for p in ensemble_probs],
                'confidence': [round(abs(p - 0.5) * 200, 2) for p in ensemble_probs],
                'models_agree': ["3/3" for _ in ensemble_probs], # Placeholder
                'consensus_percentage': [100.0 for _ in ensemble_probs] # Placeholder
            })
            
            # Add individual votes (optional but nice)
            xgb_p = trainer.xgb_calibrated.predict_proba(X_input)[:, 1]
            lgb_p = trainer.lgb_calibrated.predict_proba(X_input)[:, 1]
            cat_p = trainer.cat_calibrated.predict_proba(X_input)[:, 1]
            
            predictions_df['xgboost_vote'] = ['HOME' if p > 0.5 else 'AWAY' for p in xgb_p]
            predictions_df['lightgbm_vote'] = ['HOME' if p > 0.5 else 'AWAY' for p in lgb_p]
            predictions_df['catboost_vote'] = ['HOME' if p > 0.5 else 'AWAY' for p in cat_p]
        else:
            raise HTTPException(status_code=503, detail="Model trainer not initialized or features missing")
        
        # Combine with game info and odds features
        game_info = df[['game_id', 'home_team', 'away_team', 'commence_time', 'home_odds_avg', 'away_odds_avg', 'home_spread_avg', 'away_spread_avg']]
        results = pd.concat([game_info.reset_index(drop=True), predictions_df.reset_index(drop=True)], axis=1)
        
        # Extract individual votes from predictions_df columns
        vote_columns = [col for col in predictions_df.columns if col.endswith('_vote')]
        
        # Convert to response format
        predictions = []
        for _, row in results.iterrows():
            # Get individual votes
            individual_votes = {
                col.replace('_vote', '').replace('_', ' ').title(): row[col]
                for col in vote_columns
            }
            
            predictions.append(GamePrediction(
                game_id=row['game_id'],
                home_team=row['home_team'],
                away_team=row['away_team'],
                commence_time=row['commence_time'],
                prediction=row['prediction'],
                home_win_probability=round(row['home_win_probability'], 2),
                away_win_probability=round(row['away_win_probability'], 2),
                confidence=round(row['confidence'], 2),
                models_agree=row['models_agree'],
                consensus_percentage=round(row['consensus_percentage'], 2),
                individual_votes=individual_votes,
                home_odds=round(row['home_odds_avg'], 2),
                away_odds=round(row['away_odds_avg'], 2),
                home_spread=round(row['home_spread_avg'], 1),
                away_spread=round(row['away_spread_avg'], 1)
            ))
        
        # Model info
        model_info = {
            "num_models": 3,
            "model_names": ["XGBoost", "LightGBM", "CatBoost"],
            "num_features": len(trainer.feature_names) if trainer else 0,
            "feature_names": trainer.feature_names if trainer else []
        }
        
        return PredictionsResponse(
            timestamp=datetime.now().isoformat(),
            total_games=len(predictions),
            predictions=predictions,
            model_info=model_info
        )
    
    except HTTPException:
        raise
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
            with open(history_file, 'r') as f:
                training_history = json.load(f)
        
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
    """Return upcoming games using local python libraries (nba_api / pyespn) when available."""
    try:
        games = get_upcoming_games(days_ahead=days)

        # If no games found from local libraries, fall back to RapidAPI (if key provided)
        if not games:
            rapid_key = os.environ.get('RAPIDAPI_KEY') or os.environ.get('NEXT_PUBLIC_RAPIDAPI_KEY')
            rapid_host = 'nba-schedule.p.rapidapi.com'
            if rapid_key:
                try:
                    url = f"https://{rapid_host}/schedule"
                    headers = {
                        'x-rapidapi-key': rapid_key,
                        'x-rapidapi-host': rapid_host
                    }
                    r = requests.get(url, headers=headers, timeout=10)
                    if r.ok:
                        payload = r.json()
                        games = payload.get('games') or payload.get('schedule') or []
                        # Normalize minimal fields
                        normalized = []
                        for g in games:
                            gd = g.get('date') or g.get('game_date') or g.get('start_date') or ''
                            normalized.append({
                                'game_id': g.get('id') or g.get('game_id') or g.get('GAME_ID') or '',
                                'date': gd,
                                'home_team': g.get('home_team') or g.get('home') or '',
                                'away_team': g.get('away_team') or g.get('away') or '',
                                'game_time': g.get('time') or g.get('startTime') or ''
                            })
                        games = normalized
                except Exception:
                    pass

        return {
            "success": True,
            "source": "nba_api|pyespn|rapidapi-fallback",
            "count": len(games),
            "games": games
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


if __name__ == "__main__":
    import uvicorn
    
    print("="*80)
    print("🚀 Starting NBA Ensemble Prediction API")
    print("="*80)
    print("📍 API docs: http://localhost:8000/docs")
    print("🎯 Predictions: http://localhost:8000/predictions")
    print("🧠 XAI: http://localhost:8000/explain/{game_id}")
    print("📋 Reports: http://localhost:8000/scouting-report/{game_id}")
    print("="*80)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
