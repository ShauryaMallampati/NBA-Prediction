"""FastAPI main application."""

import pickle
from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.common.config import settings
from src.common.logger import setup_logger
from src.common.paths import Paths
from src.data.ingest.live_feature_extractor import LiveFeatureExtractor
from src.services.live_prediction_service import LivePredictionService
from src.models.kelly_criterion import KellyCriterion

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


class PlayerPropPredictionRequest(BaseModel):
    """Request model for player prop predictions."""
    player_name: str
    is_home: bool = True
    rest_days: int = 1
    is_back_to_back: bool = False
    FG_pct: float = 0.44
    FG3_pct: float = 0.35
    FT_pct: float = 0.75
    usage_pct: float = 0.24
    games_played: int = 10
    consistency_score: float = 0.7
    recent_stats: Dict[str, Any] = {}
    season_stats: Dict[str, Any] = {}
    opponent_defense: Dict[str, Any] = {}


class PlayerPropPredictionResponse(BaseModel):
    """Response model for player prop predictions."""
    player_name: str
    predictions: Dict[str, Any]
    ready_for_production: bool
    error: Optional[str] = None


class KellyRecommendationRequest(BaseModel):
    """Request model for Kelly Criterion betting recommendation."""
    bankroll: float = 10000.0
    kelly_fraction: float = 0.25
    min_edge: float = 0.05
    predictions: Dict[str, Any]  # {stat: {calibrated: float, confidence: float}}
    odds_dict: Optional[Dict[str, float]] = None


class BetRecommendation(BaseModel):
    """Individual bet recommendation."""
    stat: str
    prediction: str
    bet_size: float
    confidence: float
    expected_value: float
    kelly_pct: float
    prob: float


class KellyRecommendationResponse(BaseModel):
    """Response model for Kelly Criterion recommendation."""
    recommendations: List[BetRecommendation] = []
    total_allocation: float = 0.0
    conservative_allocation: float = 0.0
    portfolio_metrics: Dict[str, Any] = {}
    error: Optional[str] = None


# Global service cache
_prediction_service = None


def get_prediction_service():
    """Get live prediction service (lazy load)."""
    global _prediction_service
    if _prediction_service is None:
        _prediction_service = LivePredictionService()
        logger.info("Initialized LivePredictionService")
    return _prediction_service


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


@app.post("/predict", response_model=PlayerPropPredictionResponse)
async def predict_player_prop(request: PlayerPropPredictionRequest) -> PlayerPropPredictionResponse:
    """Get live player prop predictions."""
    try:
        service = get_prediction_service()
        
        # Convert request to dict for service
        player_data = {
            'player_name': request.player_name,
            'is_home': request.is_home,
            'rest_days': request.rest_days,
            'is_back_to_back': request.is_back_to_back,
            'FG_pct': request.FG_pct,
            'FG3_pct': request.FG3_pct,
            'FT_pct': request.FT_pct,
            'usage_pct': request.usage_pct,
            'games_played': request.games_played,
            'consistency_score': request.consistency_score,
            'recent_stats': request.recent_stats or {},
            'season_stats': request.season_stats or {},
            'opponent_defense': request.opponent_defense or {},
        }
        
        result = service.predict_player_prop(player_data)
        
        return PlayerPropPredictionResponse(
            player_name=result['player_name'],
            predictions=result['predictions'],
            ready_for_production=result['ready_for_production'],
            error=result.get('error')
        )
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return PlayerPropPredictionResponse(
            player_name=request.player_name,
            predictions={},
            ready_for_production=False,
            error=str(e)
        )


@app.post("/kelly", response_model=KellyRecommendationResponse)
async def get_kelly_recommendation(request: KellyRecommendationRequest) -> KellyRecommendationResponse:
    """Get Kelly Criterion betting recommendation."""
    try:
        kelly = KellyCriterion(
            bankroll=request.bankroll,
            kelly_fraction=request.kelly_fraction,
            min_edge=request.min_edge,
        )
        
        recommendation = kelly.get_kelly_recommendation(
            predictions=request.predictions,
            odds_dict=request.odds_dict,
            use_conservative=True,
        )
        
        # Convert to response format
        recommendations = []
        for rec in recommendation.get("recommendations", []):
            recommendations.append(BetRecommendation(
                stat=rec["stat"],
                prediction=rec["prediction"],
                bet_size=rec["bet_size"],
                confidence=rec["confidence"],
                expected_value=rec["expected_value"],
                kelly_pct=rec["kelly_pct"],
                prob=rec["prob"],
            ))
        
        return KellyRecommendationResponse(
            recommendations=recommendations,
            total_allocation=recommendation.get("total_allocation", 0),
            conservative_allocation=recommendation.get("conservative_allocation", 0),
            portfolio_metrics=recommendation.get("portfolio_metrics", {}),
        )
    except Exception as e:
        logger.error(f"Kelly recommendation error: {e}")
        return KellyRecommendationResponse(
            error=str(e)
        )


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


# ============================================================================
# REAL DATA ENDPOINTS (NEW)
# ============================================================================

@app.get("/api/teams")
async def get_teams():
    """Get all NBA teams (REAL DATA)."""
    from src.data.ingest.nba_api_client import get_nba_client
    
    try:
        client = get_nba_client()
        teams = client.get_teams()
        return {"success": True, "count": len(teams), "teams": teams}
    except Exception as e:
        logger.error(f"Failed to fetch teams: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/games")
async def get_games(date: Optional[str] = None):
    """Get games for a specific date (REAL DATA)."""
    from src.data.ingest.game_fetcher import get_game_fetcher
    
    try:
        fetcher = get_game_fetcher()
        
        if date:
            games = fetcher.get_games_by_date(date)
        else:
            games = fetcher.get_today_games()
        
        return {"success": True, "count": len(games), "games": games}
    except Exception as e:
        logger.error(f"Failed to fetch games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/games/live")
async def get_live_games():
    """Get live game scores (REAL DATA)."""
    from src.data.ingest.game_fetcher import get_game_fetcher
    
    try:
        fetcher = get_game_fetcher()
        live_games = fetcher.get_live_scores()
        return {"success": True, "count": len(live_games), "games": live_games}
    except Exception as e:
        logger.error(f"Failed to fetch live games: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players/search")
async def search_players(name: str, limit: int = 10):
    """Search for players by name (REAL DATA)."""
    from src.data.ingest.player_fetcher import get_player_fetcher
    
    try:
        fetcher = get_player_fetcher()
        players = fetcher.search_players(name)
        return {"success": True, "count": len(players), "players": players[:limit]}
    except Exception as e:
        logger.error(f"Failed to search players: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players/{player_id}/stats")
async def get_player_stats(player_id: int, games: int = 10):
    """Get player statistics (REAL DATA)."""
    from src.data.ingest.player_fetcher import get_player_fetcher
    
    try:
        fetcher = get_player_fetcher()
        stats = fetcher.get_player_stats(player_id, last_n_games=games)
        return {"success": True, "player_id": player_id, "games": len(stats), "stats": stats}
    except Exception as e:
        logger.error(f"Failed to fetch player stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/players/{player_id}/performance")
async def get_player_performance(player_id: int, games: int = 5):
    """Get player recent performance summary (REAL DATA)."""
    from src.data.ingest.player_fetcher import get_player_fetcher
    
    try:
        fetcher = get_player_fetcher()
        performance = fetcher.get_recent_performance(player_id, games=games)
        return {"success": True, "player_id": player_id, **performance}
    except Exception as e:
        logger.error(f"Failed to fetch player performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/odds")
async def get_betting_odds():
    """Get current betting odds (REAL DATA)."""
    from src.data.ingest.odds_fetcher import get_odds_fetcher
    
    try:
        fetcher = get_odds_fetcher()
        odds = fetcher.get_current_odds()
        return {"success": True, "count": len(odds), "odds": odds}
    except Exception as e:
        logger.error(f"Failed to fetch odds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
