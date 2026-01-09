"""
Chemistry API Endpoints

Provides player chemistry data via FastAPI.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class DuoInfo(BaseModel):
    players: str
    net_rating: float
    games: int
    team: Optional[str] = None


class ChemistryResponse(BaseModel):
    team: str
    chemistry_score: float
    top_duos: List[DuoInfo]


class MatchupChemistryResponse(BaseModel):
    home_team: str
    away_team: str
    home_chemistry_score: float
    away_chemistry_score: float
    chemistry_differential: float
    win_probability_adjustment: float
    home_top_duos: List[DuoInfo]
    away_top_duos: List[DuoInfo]


class LeagueChemistryResponse(BaseModel):
    total_teams: int
    total_pairs: int
    top_duos: List[DuoInfo]
    team_rankings: List[Dict]


def get_chemistry_model():
    """Import and get chemistry model."""
    try:
        from src.models.chemistry_gnn import get_chemistry_model as _get_model
        return _get_model()
    except Exception as e:
        logger.error(f"Failed to load chemistry model: {e}")
        return None


@router.get("/chemistry/team/{team_abbr}", response_model=ChemistryResponse)
async def get_team_chemistry(team_abbr: str):
    """Get chemistry score and top duos for a specific team."""
    model = get_chemistry_model()
    if not model or not model.loaded:
        raise HTTPException(status_code=503, detail="Chemistry model not available")
    
    score = model.get_team_chemistry_score(team_abbr.upper())
    top_duos = model.get_top_team_duos(team_abbr.upper(), 10)
    
    return ChemistryResponse(
        team=team_abbr.upper(),
        chemistry_score=score,
        top_duos=[DuoInfo(**d) for d in top_duos]
    )


@router.get("/chemistry/matchup/{home_team}/{away_team}", response_model=MatchupChemistryResponse)
async def get_matchup_chemistry(home_team: str, away_team: str):
    """Get chemistry analysis for a specific matchup."""
    model = get_chemistry_model()
    if not model or not model.loaded:
        raise HTTPException(status_code=503, detail="Chemistry model not available")
    
    result = model.predict_chemistry_impact(home_team.upper(), away_team.upper())
    
    return MatchupChemistryResponse(
        home_team=result['home_team'],
        away_team=result['away_team'],
        home_chemistry_score=result['home_chemistry_score'],
        away_chemistry_score=result['away_chemistry_score'],
        chemistry_differential=result['chemistry_differential'],
        win_probability_adjustment=result['win_probability_adjustment'],
        home_top_duos=[DuoInfo(**d) for d in result['home_top_duos']],
        away_top_duos=[DuoInfo(**d) for d in result['away_top_duos']]
    )


@router.get("/chemistry/league", response_model=LeagueChemistryResponse)
async def get_league_chemistry():
    """Get league-wide chemistry data."""
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
    
    return LeagueChemistryResponse(
        total_teams=len(model.team_chemistry),
        total_pairs=len(model.player_pairs),
        top_duos=[DuoInfo(**d) for d in top_duos],
        team_rankings=team_rankings
    )
