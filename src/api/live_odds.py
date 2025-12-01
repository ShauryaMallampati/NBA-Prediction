"""
Live odds fetcher using RapidAPI (The Odds API).
Fetches real-time betting odds to replace static JSON files.
"""
import os
import requests
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Fallback key from project context if env var is missing
DEFAULT_RAPID_KEY = "1a7881ea8amsh9de79b369cd34f7p19587ajsn99e9a80c4881"

def get_live_odds_data() -> Dict[str, Any]:
    """
    Fetch live NBA odds from RapidAPI and return in the structure 
    expected by create_features_from_odds.
    """
    api_key = os.environ.get('RAPIDAPI_KEY') or os.environ.get('NBA_STATS_API_KEY') or DEFAULT_RAPID_KEY
    host = "odds.p.rapidapi.com"
    
    url = f"https://{host}/v4/sports/basketball_nba/odds"
    
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": host
    }
    
    params = {
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal", # create_features_from_odds expects decimal/american? 
                                 # It uses 1/odds for implied prob, so decimal is likely expected.
                                 # Let's check create_features_from_odds logic.
                                 # 'home_implied_prob': 1 / np.mean(home_odds)
                                 # This implies Decimal odds (e.g. 1.90). 
                                 # If American (-110), the formula would be different.
                                 # So I'll request decimal.
        "dateFormat": "iso"
    }
    
    try:
        logger.info(f"Fetching live odds from {url}...")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch odds: {response.status_code} {response.text}")
            return {}
            
        data = response.json()
        
        # The Odds API returns a list of games.
        # We need to wrap it to match the structure expected by create_features_from_odds:
        # { 'endpoints': { 'nba_odds': [ ... ] } }
        
        return {
            'endpoints': {
                'nba_odds': data
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching live odds: {e}")
        return {}
