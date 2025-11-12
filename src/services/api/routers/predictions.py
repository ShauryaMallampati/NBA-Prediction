from __future__ import annotations
import pathlib
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
import sys

# Add src to path
sys.path.insert(0, str(pathlib.Path(__file__).parents[3]))
from src.models.pregame.predictor import EnsemblePredictor

router = APIRouter()

# Global predictor instance (loaded once at startup)
predictor = None

def get_predictor():
    """Lazy load predictor"""
    global predictor
    if predictor is None:
        try:
            predictor = EnsemblePredictor("artifacts/models/pregame")
        except Exception as e:
            raise HTTPException(500, f"Failed to load models: {str(e)}")
    return predictor

@router.get("/predictions")
def get_predictions(date: str = Query(..., description="Date in YYYY-MM-DD format", pattern=r"\d{4}-\d{2}-\d{2}")):
    """
    Get predictions for all games on a specific date
    
    Args:
        date: Date in YYYY-MM-DD format
    
    Returns:
        JSON with predictions including win probabilities and feature importance
    """
    feats_path = pathlib.Path("artifacts/features/pregame.parquet")
    
    if not feats_path.exists():
        raise HTTPException(400, "Feature data not found. Run feature engineering first.")
    
    # Load predictor
    pred = get_predictor()
    
    # Load features for the date
    df = pd.read_parquet(feats_path)
    
    # Filter by date if date column exists
    if "date" in df.columns:
        df_date = df[df["date"] == date]
    else:
        df_date = df
    
    if df_date.empty:
        return {"date": date, "games": [], "message": "No games found for this date"}
    
    # Get predictions with feature importance
    try:
        predictions = pred.predict_with_features(df_date, top_n=5)
    except Exception as e:
        raise HTTPException(500, f"Prediction failed: {str(e)}")
    
    # Build response
    games = []
    for i, (_, row) in enumerate(df_date.iterrows()):
        pred_data = predictions[i]
        games.append({
            "game_id": row.get("game_id", f"game_{i}"),
            "home_team": row.get("home_team", row.get("home", "Unknown")),
            "away_team": row.get("away_team", row.get("away", "Unknown")),
            "home_win_prob": pred_data["prediction"],
            "away_win_prob": 1 - pred_data["prediction"],
            "confidence": abs(pred_data["prediction"] - 0.5) * 2,  # 0-1 scale
            "top_features": pred_data["top_features"],
            "predicted_winner": row.get("home_team", row.get("home", "Unknown")) if pred_data["prediction"] > 0.5 else row.get("away_team", row.get("away", "Unknown"))
        })
    
    # Get model info
    model_info = pred.get_model_info()
    
    return {
        "date": date,
        "games": games,
        "model_info": {
            "accuracy": model_info["metrics"]["ensemble"]["accuracy"],
            "auc": model_info["metrics"]["ensemble"]["auc"],
            "timestamp": model_info["timestamp"]
        }
    }

@router.get("/model-info")
def get_model_info():
    """Get information about the loaded model"""
    pred = get_predictor()
    return pred.get_model_info()

