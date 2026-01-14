"""
Live Odds Comparison & Betting Recommendation Engine (Task #16)

THE CRITICAL MONETIZATION LAYER:
  Model predictions without odds comparison = useless
  Model predictions + odds comparison = profitable edge detection

Flow:
  1. Fetch live odds from FanDuel/DraftKings (ODDS_API_KEY)
  2. Load model predictions from LightGBM (Task #15)
  3. Calculate edge: (model_prob - market_prob)
  4. Generate recommendations for +EV opportunities

Edge Calculation:
  Model says: 55% chance PTS > 25
  Market line: 25.5 at -110 odds
  Market implies: ~52% chance (american odds → probability)
  Edge: 55% - 52% = +3%
  
  If edge > 5% → RECOMMEND BET 💰
"""

from __future__ import annotations
import os
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
import pandas as pd
import numpy as np
from dataclasses import dataclass
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MarketLine:
    """Represents a sportsbook line for a player prop."""
    player_name: str
    stat_type: str  # PTS, AST, REB, STL, BLK
    line: float  # e.g., 25.5
    over_odds: int  # American odds e.g., -110
    under_odds: int  # American odds e.g., -110
    sportsbook: str  # e.g., "fanduel", "draftkings"
    timestamp: datetime
    home_team: Optional[str] = None
    away_team: Optional[str] = None


@dataclass
class BettingRecommendation:
    """Represents a +EV betting opportunity."""
    player_name: str
    stat_type: str
    model_prob: float  # 0.55 = 55% chance
    market_line: float  # 25.5
    market_prob: float  # 0.52 = 52% implied probability
    edge: float  # 0.03 = 3% edge
    bet_direction: str  # "OVER" or "UNDER"
    odds: int  # American odds
    sportsbook: str
    confidence: str  # "HIGH", "MEDIUM", "LOW"
    shap_explanation: Optional[Dict] = None


class OddsComparisonEngine:
    """
    Compares LightGBM predictions vs live sportsbook odds.
    Generates betting recommendations for +EV opportunities.
    """
    
    def __init__(self, odds_api_key: Optional[str] = None):
        """
        Initialize odds comparison engine.
        
        Args:
            odds_api_key: The Odds API key (defaults to env var)
        """
        self.odds_api_key = odds_api_key or os.getenv("ODDS_API_KEY")
        if not self.odds_api_key:
            raise ValueError("ODDS_API_KEY not found in environment")
        
        self.base_url = "https://api.the-odds-api.com/v4"
        
        # Minimum edge thresholds for recommendations
        self.edge_thresholds = {
            "HIGH": 0.08,    # 8%+ edge
            "MEDIUM": 0.05,  # 5-8% edge
            "LOW": 0.03,     # 3-5% edge
        }
        
    def fetch_player_props(
        self,
        sport: str = "basketball_nba",
        markets: str = "player_points,player_assists,player_rebounds",
        regions: str = "us",
        bookmakers: str = "fanduel,draftkings",
    ) -> List[MarketLine]:
        """
        Fetch live player props from sportsbooks.
        
        Args:
            sport: Sport key (default: basketball_nba)
            markets: Comma-separated markets (player_points, player_assists, etc.)
            regions: Regions to fetch odds from
            bookmakers: Comma-separated bookmaker keys
        
        Returns:
            List of MarketLine objects
        """
        logger.info(f"Fetching player props from {bookmakers}...")
        
        # First, get available events (games)
        events_url = f"{self.base_url}/sports/{sport}/events"
        params = {
            "apiKey": self.odds_api_key,
            "regions": regions,
        }
        
        try:
            response = requests.get(events_url, params=params, timeout=10)
            response.raise_for_status()
            events = response.json()
            
            if not events:
                logger.warning("No upcoming games found")
                return []
            
            logger.info(f"Found {len(events)} upcoming games")
            
            # Fetch odds for each event
            all_lines = []
            for event in events[:5]:  # Limit to first 5 games for now
                event_id = event.get("id")
                
                odds_url = f"{self.base_url}/sports/{sport}/events/{event_id}/odds"
                odds_params = {
                    "apiKey": self.odds_api_key,
                    "regions": regions,
                    "markets": markets,
                    "bookmakers": bookmakers,
                }
                
                odds_response = requests.get(odds_url, params=odds_params, timeout=10)
                if odds_response.status_code == 200:
                    odds_data = odds_response.json()
                    # Add team info to odds data from event info
                    odds_data["home_team"] = event.get("home_team")
                    odds_data["away_team"] = event.get("away_team")
                    lines = self._parse_odds_response(odds_data)
                    all_lines.extend(lines)
            
            logger.info(f"✅ Fetched {len(all_lines)} market lines")
            return all_lines
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error fetching odds: {e}")
            return []
    
    def _parse_odds_response(self, odds_data: Dict) -> List[MarketLine]:
        """Parse API response into MarketLine objects."""
        lines = []
        
        bookmakers = odds_data.get("bookmakers", [])
        home_team = odds_data.get("home_team")
        away_team = odds_data.get("away_team")
        
        for bookmaker in bookmakers:
            sportsbook = bookmaker.get("key", "unknown")
            markets = bookmaker.get("markets", [])
            
            for market in markets:
                market_key = market.get("key", "")
                outcomes = market.get("outcomes", [])
                
                # Map market key to stat type
                stat_type = self._map_market_to_stat(market_key)
                if not stat_type:
                    continue
                
                # Group outcomes by player (Over/Under pairs)
                player_outcomes = {}
                for outcome in outcomes:
                    player_name = outcome.get("description", "")
                    point = outcome.get("point", 0)
                    price = outcome.get("price", 0)
                    name = outcome.get("name", "")
                    
                    if player_name not in player_outcomes:
                        player_outcomes[player_name] = {}
                    
                    player_outcomes[player_name][name] = {
                        "point": point,
                        "price": price,
                    }
                
                # Create MarketLine for each player
                for player_name, outcomes_dict in player_outcomes.items():
                    over = outcomes_dict.get("Over", {})
                    under = outcomes_dict.get("Under", {})
                    
                    if over and under:
                        lines.append(MarketLine(
                            player_name=player_name,
                            stat_type=stat_type,
                            line=over.get("point", 0),
                            over_odds=over.get("price", 0),
                            under_odds=under.get("price", 0),
                            sportsbook=sportsbook,
                            timestamp=datetime.now(),
                            home_team=home_team,
                            away_team=away_team,
                        ))
        
        return lines
    
    def _map_market_to_stat(self, market_key: str) -> Optional[str]:
        """Map odds API market key to our stat type."""
        mapping = {
            "player_points": "PTS",
            "player_assists": "AST",
            "player_rebounds": "REB",
            "player_steals": "STL",
            "player_blocks": "BLK",
            "player_threes": "3PM",
        }
        return mapping.get(market_key)
    
    def american_to_probability(self, american_odds: int) -> float:
        """
        Convert American odds to implied probability.
        
        Args:
            american_odds: e.g., -110, +150
        
        Returns:
            Implied probability (0-1)
        
        Examples:
            -110 → 0.524 (52.4%)
            +150 → 0.400 (40%)
        """
        if american_odds < 0:
            # Favorite: -110 → 110/(110+100) = 0.524
            return abs(american_odds) / (abs(american_odds) + 100)
        else:
            # Underdog: +150 → 100/(150+100) = 0.400
            return 100 / (american_odds + 100)
    
    def calculate_edge(
        self,
        model_prob: float,
        market_prob: float,
    ) -> float:
        """
        Calculate betting edge.
        
        Args:
            model_prob: Model's probability (0-1)
            market_prob: Market's implied probability (0-1)
        
        Returns:
            Edge (0-1), positive = +EV
        
        Example:
            Model: 55% (0.55)
            Market: 52% (0.52)
            Edge: 3% (0.03)
        """
        return model_prob - market_prob
    
    def generate_recommendations(
        self,
        model_predictions: pd.DataFrame,
        market_lines: List[MarketLine],
        min_edge: float = 0.03,
    ) -> List[BettingRecommendation]:
        """
        Compare model predictions vs market lines.
        Generate betting recommendations for +EV opportunities.
        
        Args:
            model_predictions: DataFrame with columns:
                - player_name
                - stat_type (PTS, AST, etc.)
                - predicted_prob (0-1)
                - shap_values (optional, for explanations)
            market_lines: List of current sportsbook lines
            min_edge: Minimum edge to recommend (default 3%)
        
        Returns:
            List of BettingRecommendation objects, sorted by edge
        """
        recommendations = []
        
        logger.info(f"Comparing {len(model_predictions)} predictions vs {len(market_lines)} lines...")
        
        for _, pred_row in model_predictions.iterrows():
            player = pred_row["player_name"]
            stat = pred_row["stat_type"]
            model_prob = pred_row["predicted_prob"]
            
            # Find matching market lines
            matching_lines = [
                line for line in market_lines
                if line.player_name.lower() == player.lower()
                and line.stat_type == stat
            ]
            
            for line in matching_lines:
                # Check OVER edge
                over_market_prob = self.american_to_probability(line.over_odds)
                over_edge = self.calculate_edge(model_prob, over_market_prob)
                
                if over_edge >= min_edge:
                    confidence = self._classify_confidence(over_edge)
                    recommendations.append(BettingRecommendation(
                        player_name=player,
                        stat_type=stat,
                        model_prob=model_prob,
                        market_line=line.line,
                        market_prob=over_market_prob,
                        edge=over_edge,
                        bet_direction="OVER",
                        odds=line.over_odds,
                        sportsbook=line.sportsbook,
                        confidence=confidence,
                        shap_explanation=pred_row.get("shap_values"),
                    ))
                
                # Check UNDER edge
                under_market_prob = self.american_to_probability(line.under_odds)
                model_under_prob = 1 - model_prob  # Inverse for UNDER
                under_edge = self.calculate_edge(model_under_prob, under_market_prob)
                
                if under_edge >= min_edge:
                    confidence = self._classify_confidence(under_edge)
                    recommendations.append(BettingRecommendation(
                        player_name=player,
                        stat_type=stat,
                        model_prob=model_under_prob,
                        market_line=line.line,
                        market_prob=under_market_prob,
                        edge=under_edge,
                        bet_direction="UNDER",
                        odds=line.under_odds,
                        sportsbook=line.sportsbook,
                        confidence=confidence,
                        shap_explanation=pred_row.get("shap_values"),
                    ))
        
        # Sort by edge (highest first)
        recommendations.sort(key=lambda x: x.edge, reverse=True)
        
        logger.info(f"✅ Generated {len(recommendations)} recommendations (edge >= {min_edge:.1%})")
        return recommendations
    
    def _classify_confidence(self, edge: float) -> str:
        """Classify confidence level based on edge."""
        if edge >= self.edge_thresholds["HIGH"]:
            return "HIGH"
        elif edge >= self.edge_thresholds["MEDIUM"]:
            return "MEDIUM"
        else:
            return "LOW"
    
    def print_recommendations(self, recommendations: List[BettingRecommendation]):
        """Pretty print betting recommendations."""
        if not recommendations:
            print("\n❌ No +EV opportunities found")
            return
        
        print("\n" + "="*80)
        print("🎯 BETTING RECOMMENDATIONS (Sorted by Edge)")
        print("="*80)
        
        for i, rec in enumerate(recommendations[:10], 1):  # Top 10
            print(f"\n#{i} [{rec.confidence}] {rec.player_name} - {rec.stat_type}")
            print(f"   Direction: {rec.bet_direction} {rec.market_line}")
            print(f"   Model Prob: {rec.model_prob:.1%}  |  Market Prob: {rec.market_prob:.1%}")
            print(f"   Edge: +{rec.edge:.1%}  |  Odds: {rec.odds:+d}")
            print(f"   Sportsbook: {rec.sportsbook.upper()}")
        
        print("\n" + "="*80)
        print(f"Total opportunities: {len(recommendations)}")
        high = sum(1 for r in recommendations if r.confidence == "HIGH")
        medium = sum(1 for r in recommendations if r.confidence == "MEDIUM")
        low = sum(1 for r in recommendations if r.confidence == "LOW")
        print(f"Confidence: HIGH={high}, MEDIUM={medium}, LOW={low}")
        print("="*80)


def main():
    """Example usage."""
    engine = OddsComparisonEngine()
    
    # Fetch live odds
    logger.info("Fetching live player props odds...")
    market_lines = engine.fetch_player_props()
    
    if not market_lines:
        logger.error("No odds data available")
        return
    
    # Example: Create dummy model predictions
    # In production, this comes from LightGBM (Task #15)
    dummy_predictions = pd.DataFrame([
        {"player_name": "LeBron James", "stat_type": "PTS", "predicted_prob": 0.58},
        {"player_name": "Stephen Curry", "stat_type": "PTS", "predicted_prob": 0.62},
        {"player_name": "Nikola Jokic", "stat_type": "AST", "predicted_prob": 0.55},
    ])
    
    # Generate recommendations
    recommendations = engine.generate_recommendations(
        dummy_predictions,
        market_lines,
        min_edge=0.03,
    )
    
    # Display results
    engine.print_recommendations(recommendations)


if __name__ == "__main__":
    main()
