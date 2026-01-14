"""
Live odds fetcher using RapidAPI (The Odds API).
Fetches real-time betting odds to replace static JSON files.

Provides both async and sync interfaces for flexibility.
"""
import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Use httpx for async HTTP requests
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    import requests

logger = logging.getLogger(__name__)

# Fallback key from project context if env var is missing
DEFAULT_RAPID_KEY = "ecfaccc609msh0c3aa0fa4b8e802p12f41fjsn38bee5c39743"


async def get_live_odds_data_async(
    date_str: Optional[str] = None, 
    start_date: Optional[str] = None, 
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Async version: Fetch live NBA odds from RapidAPI.
    
    Args:
        date_str: Optional YYYY-MM-DD string to filter games by date (1-day range).
        start_date: Optional YYYY-MM-DD start date for range.
        end_date: Optional YYYY-MM-DD end date for range.
    
    Returns:
        Dict with structure: {'endpoints': {'nba_odds': [...]}}
    """
    if not HTTPX_AVAILABLE:
        # Fall back to sync version in thread pool
        return await asyncio.to_thread(get_live_odds_data, date_str, start_date, end_date)
    
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
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    
    if date_str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            start_time = dt.strftime("%Y-%m-%dT00:00:00Z")
            end_time = (dt + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
            params["commenceTimeFrom"] = start_time
            params["commenceTimeTo"] = end_time
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}. Ignoring date filter.")
    elif start_date:
        try:
            params["commenceTimeFrom"] = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00Z")
            if end_date:
                params["commenceTimeTo"] = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y-%m-%dT23:59:59Z")
            else:
                params["commenceTimeTo"] = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%dT23:59:59Z")
        except ValueError as e:
            logger.warning(f"Invalid range date format: {e}. Ignoring filter.")
    
    try:
        logger.info(f"Fetching live odds from {url}...")
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params, timeout=10.0)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch odds: {response.status_code} {response.text}")
            return {}
            
        data = response.json()
        
        return {
            'endpoints': {
                'nba_odds': data
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching live odds: {e}")
        return {}


def get_live_odds_data(
    date_str: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sync version: Fetch live NBA odds from RapidAPI.
    
    This is the original synchronous interface for backward compatibility.
    Use get_live_odds_data_async for async contexts.
    
    Args:
        date_str: Optional YYYY-MM-DD string to filter games by date (1-day range).
        start_date: Optional YYYY-MM-DD start date for range.
        end_date: Optional YYYY-MM-DD end date for range.
    
    Returns:
        Dict with structure: {'endpoints': {'nba_odds': [...]}}
    """
    # If httpx is available and we're in an async context, use async version
    if HTTPX_AVAILABLE:
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, but called synchronously - use sync requests
        except RuntimeError:
            # No running loop - safe to use asyncio.run
            pass
    
    # Use requests for sync calls (original behavior)
    try:
        import requests
    except ImportError:
        logger.error("Neither httpx nor requests available")
        return {}
    
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
        "oddsFormat": "decimal",
        "dateFormat": "iso"
    }
    
    if date_str:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            start_time = dt.strftime("%Y-%m-%dT00:00:00Z")
            end_time = (dt + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
            params["commenceTimeFrom"] = start_time
            params["commenceTimeTo"] = end_time
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}. Ignoring date filter.")
    elif start_date:
        try:
            params["commenceTimeFrom"] = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00Z")
            if end_date:
                params["commenceTimeTo"] = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y-%m-%dT23:59:59Z")
            else:
                params["commenceTimeTo"] = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%dT23:59:59Z")
        except ValueError as e:
            logger.warning(f"Invalid range date format: {e}. Ignoring filter.")
    
    try:
        logger.info(f"Fetching live odds from {url}...")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch odds: {response.status_code} {response.text}")
            return {}
            
        data = response.json()
        
        return {
            'endpoints': {
                'nba_odds': data
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching live odds: {e}")
        return {}
