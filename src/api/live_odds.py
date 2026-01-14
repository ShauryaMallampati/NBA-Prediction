"""
Live odds fetcher using RapidAPI (The Odds API).
Fetches real-time betting odds to replace static JSON files.
"""
import os
import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Fallback key from project context if env var is missing
DEFAULT_RAPID_KEY = "ecfaccc609msh0c3aa0fa4b8e802p12f41fjsn38bee5c39743"

async def get_live_odds_data(date_str: Optional[str] = None, client: Optional[httpx.AsyncClient] = None) -> Dict[str, Any]:
    """
    Fetch live NBA odds from RapidAPI and return in the structure 
    expected by create_features_from_odds.
    
    Args:
        date_str: Optional YYYY-MM-DD string to filter games by date.
        client: Optional httpx.AsyncClient to reuse connection.
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
        "dateFormat": "iso"
    }
    
    if date_str:
        try:
            # Create UTC range for the given date
            # Assuming date_str is YYYY-MM-DD
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            # Start of day UTC
            start_time = dt.strftime("%Y-%m-%dT00:00:00Z")
            # End of day UTC + buffer? RapidAPI commmenceTimeFrom is inclusive.
            end_time = (dt + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
            
            params["commenceTimeFrom"] = start_time
            params["commenceTimeTo"] = end_time
            logger.info(f"Fetching odds for date: {date_str} ({start_time} to {end_time})")
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}. Ignoring date filter.")
    
    try:
        logger.info(f"Fetching live odds from {url}...")
        if client:
            response = await client.get(url, headers=headers, params=params, timeout=10)
        else:
            async with httpx.AsyncClient() as new_client:
                response = await new_client.get(url, headers=headers, params=params, timeout=10)
        
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
