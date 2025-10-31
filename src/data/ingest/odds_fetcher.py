"""Odds data fetcher with caching and comparison.

Fetches:
- Current betting odds
- Odds comparison across books
- Line movement tracking
- Best odds finder
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

from .nba_api_client import get_nba_client
from .cache_manager import get_cache_manager, cached

logger = logging.getLogger(__name__)

# Data storage paths
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


class OddsFetcher:
    """Fetch NBA betting odds with caching."""
    
    def __init__(self):
        """Initialize odds fetcher."""
        self.client = get_nba_client()
        self.cache = get_cache_manager()
        logger.info("💰 Odds fetcher initialized")
    
    @cached(cache_type="odds", ttl=1800)  # 30 minutes
    def get_current_odds(self) -> List[Dict]:
        """
        Get current betting odds for NBA games.
        
        Returns:
            List of odds dictionaries with multiple bookmakers
        """
        logger.info("💰 Fetching current odds")
        
        odds = self.client.get_odds("basketball_nba")
        logger.info(f"✅ Found odds for {len(odds)} games")
        
        return odds
    
    def find_best_odds(self, game_id: Optional[str] = None) -> List[Dict]:
        """
        Find best odds across all bookmakers.
        
        Args:
            game_id: Specific game ID (None for all games)
        
        Returns:
            List of best odds per market
        """
        logger.info(f"🔍 Finding best odds{f' for game {game_id}' if game_id else ''}")
        
        all_odds = self.get_current_odds()
        
        if game_id:
            all_odds = [o for o in all_odds if o.get("id") == game_id]
        
        best_odds = []
        
        for game in all_odds:
            game_best = {
                "game_id": game.get("id"),
                "home_team": game.get("home_team"),
                "away_team": game.get("away_team"),
                "commence_time": game.get("commence_time"),
                "markets": {}
            }
            
            # Process each market (h2h, spreads, totals)
            for bookmaker in game.get("bookmakers", []):
                bookmaker_name = bookmaker.get("key")
                
                for market in bookmaker.get("markets", []):
                    market_key = market.get("key")
                    
                    if market_key not in game_best["markets"]:
                        game_best["markets"][market_key] = {}
                    
                    # Find best odds for each outcome
                    for outcome in market.get("outcomes", []):
                        outcome_name = outcome.get("name")
                        price = outcome.get("price")
                        point = outcome.get("point")
                        
                        key = f"{outcome_name}_{point}" if point else outcome_name
                        
                        if key not in game_best["markets"][market_key] or \
                           price > game_best["markets"][market_key][key]["price"]:
                            game_best["markets"][market_key][key] = {
                                "bookmaker": bookmaker_name,
                                "price": price,
                                "point": point,
                                "name": outcome_name
                            }
            
            best_odds.append(game_best)
        
        logger.info(f"✅ Found best odds for {len(best_odds)} games")
        return best_odds
    
    def get_odds_for_team(self, team_name: str) -> List[Dict]:
        """
        Get odds for games involving a specific team.
        
        Args:
            team_name: Team name
        
        Returns:
            List of odds for team's games
        """
        logger.info(f"🏀 Fetching odds for {team_name}")
        
        all_odds = self.get_current_odds()
        
        team_odds = [
            o for o in all_odds
            if team_name.lower() in o.get("home_team", "").lower() or
               team_name.lower() in o.get("away_team", "").lower()
        ]
        
        logger.info(f"✅ Found odds for {len(team_odds)} {team_name} games")
        return team_odds
    
    def compare_bookmakers(self, game_id: str) -> Dict:
        """
        Compare odds across all bookmakers for a game.
        
        Args:
            game_id: Game ID
        
        Returns:
            Comparison dictionary with all bookmaker odds
        """
        logger.info(f"📊 Comparing bookmakers for game {game_id}")
        
        all_odds = self.get_current_odds()
        game = next((o for o in all_odds if o.get("id") == game_id), None)
        
        if not game:
            logger.warning(f"Game {game_id} not found")
            return {}
        
        comparison = {
            "game_id": game_id,
            "home_team": game.get("home_team"),
            "away_team": game.get("away_team"),
            "bookmakers": []
        }
        
        for bookmaker in game.get("bookmakers", []):
            bookmaker_data = {
                "name": bookmaker.get("title"),
                "key": bookmaker.get("key"),
                "markets": {}
            }
            
            for market in bookmaker.get("markets", []):
                market_key = market.get("key")
                bookmaker_data["markets"][market_key] = []
                
                for outcome in market.get("outcomes", []):
                    bookmaker_data["markets"][market_key].append({
                        "name": outcome.get("name"),
                        "price": outcome.get("price"),
                        "point": outcome.get("point")
                    })
            
            comparison["bookmakers"].append(bookmaker_data)
        
        logger.info(f"✅ Compared {len(comparison['bookmakers'])} bookmakers")
        return comparison
    
    def calculate_implied_probability(self, american_odds: int) -> float:
        """
        Convert American odds to implied probability.
        
        Args:
            american_odds: American odds format (e.g., -110, +150)
        
        Returns:
            Implied probability (0-1)
        """
        if american_odds > 0:
            # Positive odds (underdog)
            prob = 100 / (american_odds + 100)
        else:
            # Negative odds (favorite)
            prob = abs(american_odds) / (abs(american_odds) + 100)
        
        return round(prob, 4)
    
    def find_value_bets(self, model_probabilities: Dict[str, float]) -> List[Dict]:
        """
        Find value bets by comparing model probabilities to odds.
        
        Args:
            model_probabilities: Dict of {team_name: win_probability}
        
        Returns:
            List of value bet opportunities
        """
        logger.info("🎯 Finding value bets")
        
        current_odds = self.get_current_odds()
        value_bets = []
        
        for game in current_odds:
            home_team = game.get("home_team")
            away_team = game.get("away_team")
            
            # Get model probabilities
            home_prob = model_probabilities.get(home_team)
            away_prob = model_probabilities.get(away_team)
            
            if not home_prob or not away_prob:
                continue
            
            # Check each bookmaker for value
            for bookmaker in game.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market.get("key") != "h2h":  # Head-to-head market
                        continue
                    
                    for outcome in market.get("outcomes", []):
                        team = outcome.get("name")
                        price = outcome.get("price")
                        
                        # Calculate implied probability from odds
                        implied_prob = self.calculate_implied_probability(price)
                        
                        # Check if our model sees value
                        model_prob = home_prob if team == home_team else away_prob
                        edge = model_prob - implied_prob
                        
                        if edge > 0.05:  # 5% edge threshold
                            value_bets.append({
                                "game": f"{away_team} @ {home_team}",
                                "team": team,
                                "bookmaker": bookmaker.get("title"),
                                "odds": price,
                                "implied_prob": round(implied_prob * 100, 1),
                                "model_prob": round(model_prob * 100, 1),
                                "edge": round(edge * 100, 1),
                                "commence_time": game.get("commence_time")
                            })
        
        # Sort by edge descending
        value_bets.sort(key=lambda x: x["edge"], reverse=True)
        
        logger.info(f"✅ Found {len(value_bets)} value bets")
        return value_bets
    
    def save_odds_to_file(self, odds: List[Dict], filename: str):
        """
        Save odds to JSON file.
        
        Args:
            odds: List of odds dictionaries
            filename: Output filename
        """
        import json
        
        output_path = RAW_DIR / filename
        output_path.write_text(json.dumps(odds, indent=2))
        logger.info(f"💾 Saved odds for {len(odds)} games to {output_path}")


# Singleton instance
_odds_fetcher: Optional[OddsFetcher] = None


def get_odds_fetcher() -> OddsFetcher:
    """Get or create odds fetcher instance."""
    global _odds_fetcher
    if _odds_fetcher is None:
        _odds_fetcher = OddsFetcher()
    return _odds_fetcher
