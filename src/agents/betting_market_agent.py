"""
Betting Market Agent - Scrapes line movement and sharp money
"""
import requests
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

class BettingMarketAgent:
    """Track line movements and market sentiment"""
    
    def __init__(self):
        self.cache_dir = Path("data/betting_market")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def analyze_line_movement(self, game_odds: Dict) -> Dict:
        """
        Analyze how odds have moved (indicates sharp money)
        If opening line was Lakers -3.5 and now -5.5, sharp money on Lakers
        """
        try:
            if 'bookmakers' not in game_odds:
                return {}
            
            all_spreads = []
            all_moneylines = []
            
            for bookmaker in game_odds['bookmakers']:
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            if outcome['name'] == game_odds['home_team']:
                                all_spreads.append(outcome['point'])
                    elif market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            if outcome['name'] == game_odds['home_team']:
                                all_moneylines.append(outcome['price'])
            
            if all_spreads:
                return {
                    'spread_variance': np.std(all_spreads),
                    'spread_range': max(all_spreads) - min(all_spreads),
                    'avg_spread': np.mean(all_spreads),
                    'bookmaker_agreement': 1.0 / (1.0 + np.std(all_spreads))  # High = consensus
                }
            
            return {}
            
        except Exception as e:
            logger.warning(f"Failed to analyze line movement: {e}")
            return {}
    
    def detect_sharp_action(self, game_odds: Dict) -> Dict:
        """
        Detect sharp money (professional bettors)
        Sharp action: Line moves against public betting percentage
        """
        # Placeholder - would need betting percentages from a paid source
        # For now, use spread variance as proxy
        line_analysis = self.analyze_line_movement(game_odds)
        
        return {
            'sharp_indicator': line_analysis.get('spread_variance', 0) > 1.0,
            'market_efficiency': line_analysis.get('bookmaker_agreement', 0.5)
        }

betting_market_agent = BettingMarketAgent()
