"""
FastAPI endpoints for NBA betting predictions (Task #23)

Endpoints:
  • GET /player-props?date=2024-10-26 → Return predictions + live odds
  • GET /bet-opportunities?min_edge=0.05 → Filter by confidence  
  • GET /performance → ROI dashboard data
  • POST /log-bet → Log actual outcomes

Integrates:
  • Task #15: LightGBM models
  • Task #16: Live odds API
  • Task #17: Rest risk prediction
  • Task #18: Performance tracking
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
import logging

# Import our components
from src.models.pregame.train_props_model import PlayerPropsLightGBMTrainer
from src.services.odds_comparison import OddsComparisonEngine, BettingRecommendation
from src.models.pregame.blowout_rest_predictor import BlowoutRestPredictor, GameContext
from src.services.betting_tracker import BettingTracker, BetRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NBA Betting Predictions API",
    description="LightGBM-powered player props predictions with live odds comparison",
    version="1.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MODELS (Request/Response schemas)
# ============================================================

class PlayerPropPrediction(BaseModel):
    """Single player prop prediction."""
    player_name: str
    stat_type: str  # PTS, AST, REB, STL, BLK
    predicted_prob: float = Field(..., ge=0, le=1)
    market_line: Optional[float] = None
    market_odds: Optional[int] = None
    market_prob: Optional[float] = None
    edge: Optional[float] = None
    confidence: Optional[str] = None  # HIGH, MEDIUM, LOW
    rest_risk: Optional[float] = None
    adjusted_prob: Optional[float] = None
    sportsbook: Optional[str] = None


class BetOpportunity(BaseModel):
    """Betting opportunity with +EV."""
    player_name: str
    stat_type: str
    bet_direction: str  # OVER or UNDER
    market_line: float
    odds: int
    edge: float
    confidence: str
    predicted_prob: float
    market_prob: float
    rest_risk: float
    adjusted_prob: float
    sportsbook: str


class LogBetRequest(BaseModel):
    """Request to log a bet."""
    date: date
    player_name: str
    stat_type: str
    bet_direction: str
    market_line: float
    odds: int
    predicted_prob: float
    market_prob: float
    edge: float
    sportsbook: str
    confidence: str


class UpdateBetRequest(BaseModel):
    """Request to update bet outcome."""
    bet_id: int
    actual_value: float
    stake: float = 100


class PerformanceResponse(BaseModel):
    """Performance dashboard response."""
    total_bets: int
    wins: int
    losses: int
    pushes: int
    pending: int
    decided_bets: int
    win_rate: float
    total_profit: float
    total_wagered: float
    roi: float


# ============================================================
# INITIALIZE SERVICES
# ============================================================

# NOTE: In production, these would be initialized once and reused
# For now, we'll create them per-request (not ideal but works for demo)

def get_model():
    """Get LightGBM model (lazy load)."""
    # TODO: Load pre-trained models from artifacts/
    # For now, return uninitialized trainer (would need training first)
    return PlayerPropsLightGBMTrainer()


def get_odds_engine():
    """Get odds comparison engine."""
    return OddsComparisonEngine()


def get_rest_predictor():
    """Get rest risk predictor."""
    return BlowoutRestPredictor()


def get_tracker():
    """Get betting tracker."""
    return BettingTracker(db_path="betting_performance.db")


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "NBA Betting Predictions API",
        "version": "1.0.0",
    }


@app.get("/player-props", response_model=List[PlayerPropPrediction], tags=["Predictions"])
async def get_player_props(
    game_date: date = Query(..., description="Game date (YYYY-MM-DD)"),
    min_prob: float = Query(0.5, description="Minimum predicted probability"),
):
    """
    Get player prop predictions for a specific date.
    
    Returns predictions with live odds comparison.
    """
    try:
        # TODO: In production, fetch actual player data for this date
        # For now, return dummy predictions
        
        logger.info(f"Fetching player props for {game_date}")
        
        # Get live odds
        odds_engine = get_odds_engine()
        market_lines = odds_engine.fetch_player_props()
        
        logger.info(f"Found {len(market_lines)} market lines")
        
        # TODO: Generate predictions using trained model
        # For now, create dummy predictions that match some market lines
        predictions = []
        
        for line in market_lines[:10]:  # Sample first 10
            predictions.append(PlayerPropPrediction(
                player_name=line.player_name,
                stat_type=line.stat_type,
                predicted_prob=0.55,  # Dummy
                market_line=line.line,
                market_odds=int(line.over_odds),  # Convert to int
                market_prob=0.524,  # Dummy
                edge=0.03,  # Dummy
                confidence="MEDIUM",
                rest_risk=0.0,
                adjusted_prob=0.55,
                sportsbook=line.sportsbook,
            ))
        
        return predictions
    
    except Exception as e:
        logger.error(f"Error fetching player props: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bet-opportunities", response_model=List[BetOpportunity], tags=["Predictions"])
async def get_bet_opportunities(
    min_edge: float = Query(0.03, description="Minimum edge (e.g., 0.05 = 5%)"),
    confidence: Optional[str] = Query(None, description="Filter by confidence (HIGH, MEDIUM, LOW)"),
):
    """
    Get +EV betting opportunities.
    
    Returns only bets with predicted edge above threshold.
    """
    try:
        logger.info(f"Finding bet opportunities with min_edge={min_edge}")
        
        odds_engine = get_odds_engine()
        market_lines = odds_engine.fetch_player_props()
        
        # TODO: Get actual predictions from model
        # For now, create dummy predictions matching market lines
        opportunities = []
        
        for line in market_lines[:20]:  # Sample first 20
            # Calculate dummy edge
            dummy_prob = 0.55
            # Convert odds to probability
            market_prob = odds_engine.american_to_probability(line.over_odds)
            edge = dummy_prob - market_prob
            
            if edge >= min_edge:
                # Determine confidence
                if edge >= 0.08:
                    conf = "HIGH"
                elif edge >= 0.05:
                    conf = "MEDIUM"
                else:
                    conf = "LOW"
                
                # Filter by confidence if requested
                if confidence is None or conf == confidence:
                    opportunities.append(BetOpportunity(
                        player_name=line.player_name,
                        stat_type=line.stat_type,
                        bet_direction="OVER",  # Simplified
                        market_line=line.line,
                        odds=line.over_odds,
                        edge=edge,
                        confidence=conf,
                        predicted_prob=dummy_prob,
                        market_prob=market_prob,
                        rest_risk=0.0,  # TODO: Calculate rest risk
                        adjusted_prob=dummy_prob,
                        sportsbook=line.sportsbook,
                    ))
        
        logger.info(f"Found {len(opportunities)} opportunities")
        
        return opportunities
    
    except Exception as e:
        logger.error(f"Error finding bet opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/performance", response_model=PerformanceResponse, tags=["Tracking"])
async def get_performance(
    start_date: Optional[date] = Query(None, description="Filter from this date"),
):
    """
    Get betting performance dashboard.
    
    Returns win rate, ROI, and profit/loss metrics.
    """
    try:
        tracker = get_tracker()
        summary = tracker.get_performance_summary(start_date=start_date)
        tracker.close()
        
        # Handle None values
        for key in ['wins', 'losses', 'pushes', 'pending']:
            if summary.get(key) is None:
                summary[key] = 0
        
        return PerformanceResponse(**summary)
    
    except Exception as e:
        logger.error(f"Error fetching performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/log-bet", tags=["Tracking"])
async def log_bet(request: LogBetRequest):
    """
    Log a new bet to tracking database.
    
    Returns the generated bet ID.
    """
    try:
        tracker = get_tracker()
        
        bet = BetRecord(
            bet_id=None,
            date=request.date,
            player_name=request.player_name,
            stat_type=request.stat_type,
            bet_direction=request.bet_direction,
            market_line=request.market_line,
            odds=request.odds,
            predicted_prob=request.predicted_prob,
            market_prob=request.market_prob,
            edge=request.edge,
            actual_value=None,
            outcome=None,
            profit_loss=None,
            sportsbook=request.sportsbook,
            confidence=request.confidence,
            created_at=datetime.now(),
        )
        
        bet_id = tracker.log_bet(bet)
        tracker.close()
        
        return {"bet_id": bet_id, "status": "logged"}
    
    except Exception as e:
        logger.error(f"Error logging bet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-bet", tags=["Tracking"])
async def update_bet(request: UpdateBetRequest):
    """
    Update bet with actual outcome.
    
    Calculates win/loss and updates profit/loss.
    """
    try:
        tracker = get_tracker()
        
        tracker.update_bet_outcome(
            bet_id=request.bet_id,
            actual_value=request.actual_value,
            stake=request.stake,
        )
        
        tracker.close()
        
        return {"bet_id": request.bet_id, "status": "updated"}
    
    except Exception as e:
        logger.error(f"Error updating bet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# MAIN (for testing)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*80)
    print("🚀 Starting NBA Betting Predictions API")
    print("="*80)
    print("Endpoints:")
    print("  • GET  /player-props?date=2024-10-26")
    print("  • GET  /bet-opportunities?min_edge=0.05")
    print("  • GET  /performance")
    print("  • POST /log-bet")
    print("  • POST /update-bet")
    print("\nDocs: http://localhost:8000/docs")
    print("="*80 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
