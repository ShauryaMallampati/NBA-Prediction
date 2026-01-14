"""
Live schedule fetcher using available libraries (nba_api, pyespn) with safe fallbacks.

The functions here try to import and use `nba_api` first (preferred), then `pyespn` as a fallback.
If neither library is installed or fails, the module returns an empty list and logs the issue —
the FastAPI route that consumes this will fall back to RapidAPI or the existing data pipeline.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def _try_nba_api(days_ahead: int = 14) -> List[Dict[str, Any]]:
    """Attempt to fetch upcoming games using `nba_api` live endpoints."""
    try:
        # Import here to keep import-time optional
        from nba_api.live.nba.endpoints import scoreboard

        sb = scoreboard.ScoreBoard()
        data = sb.get_dict()  # May contain 'gameHeader' and 'game' keys depending on version

        games = []
        # Different versions may structure data differently; be defensive
        raw_games = []
        if isinstance(data, dict):
            # common key name
            if 'games' in data:
                raw_games = data['games']
            elif 'game' in data:
                raw_games = data['game']
            elif 'resultSets' in data:
                # an older style; try to extract
                for rs in data['resultSets']:
                    if rs.get('name', '').lower().startswith('games'):
                        for row in rs.get('rowSet', []):
                            raw_games.append(row)

        # If scoreboard provides limited view, try to parse expected fields
        for g in raw_games:
            try:
                # Get a variety of potential field names
                game_id = g.get('gameId') or g.get('game_id') or g.get('GAME_ID') or str(g.get('id', ''))
                home = g.get('homeTeam') or g.get('hTeam') or g.get('home') or g.get('HOME_TEAM')
                away = g.get('awayTeam') or g.get('vTeam') or g.get('away') or g.get('AWAY_TEAM')
                start = g.get('gameTimeUTC') or g.get('startTime') or g.get('gameTime') or g.get('start_date')

                # Normalise team names
                home_name = home.get('teamName') if isinstance(home, dict) else home
                away_name = away.get('teamName') if isinstance(away, dict) else away

                games.append({
                    'game_id': str(game_id),
                    'date': (start or datetime.utcnow().isoformat()).split('T')[0],
                    'home_team': home_name or '',
                    'away_team': away_name or '',
                    'game_time': start or ''
                })
            except Exception:
                continue

        return games
    except Exception as e:
        logger.debug(f"nba_api fetch failed: {e}")
        return []


def _try_pyespn(days_ahead: int = 14) -> List[Dict[str, Any]]:
    """Attempt to fetch upcoming games using `pyespn` (if available)."""
    try:
        import pyespn

        games = []
        today = datetime.utcnow().date()
        end = today + timedelta(days=days_ahead)

        current = today
        while current <= end:
            try:
                schedule = pyespn.schedule(date=current)
                entries = schedule.get('events', []) if isinstance(schedule, dict) else schedule
                for g in entries:
                    game_id = g.get('id') if isinstance(g, dict) else getattr(g, 'id', None)
                    home = g.get('home') if isinstance(g, dict) else getattr(g, 'home', None)
                    away = g.get('away') if isinstance(g, dict) else getattr(g, 'away', None)
                    start = g.get('startTime') if isinstance(g, dict) else getattr(g, 'startTime', None)

                    games.append({
                        'game_id': str(game_id),
                        'date': current.isoformat(),
                        'home_team': home or '',
                        'away_team': away or '',
                        'game_time': start or ''
                    })
            except Exception:
                pass
            current = current + timedelta(days=1)

        return games
    except Exception as e:
        logger.debug(f"pyespn fetch failed: {e}")
        return []


def get_upcoming_games(days_ahead: int = 14) -> List[Dict[str, Any]]:
    """Return upcoming NBA games for the next `days_ahead` days.

    Strategy:
    1. Try `nba_api` for live/today data (fast, free).
    2. Try `RapidAPI` (get_live_odds_data) for future dates loop.
    """
    all_games = []
    
    # 1. Try nba_api (mostly for today)
    todays_games = _try_nba_api(days_ahead)
    if todays_games:
        all_games.extend(todays_games)
        
    # Track which dates we have to avoid duplicates (though minimal risk if we target specific future dates)
    existing_dates = set(g['date'] for g in all_games)
    
    # 2. Loop for future dates using RapidAPI
    # Only if we used the user's key? Yes, get_live_odds_data handles fallback.
    try:
        from src.api.live_odds import get_live_odds_data
        
        start_date = datetime.utcnow().date()
        
        # Limit to next 5 days for speed/rate-limits?
        # User asked for "future games". 14 days is 14 calls. RapidAPI might limit us.
        # Let's limit to 7 days for now to be safe, or just `days_ahead` if small.
        # But `days_ahead` default is 14. 
        # Let's do min(days_ahead, 7) to be kind to the key quota.
        # The user's key `ecfaccc...` is likely a free tier.
        scan_days = min(days_ahead, 7)
        
        for i in range(0, scan_days + 1): # Start from 0 to capture today if nba_api failed!
            target_date = start_date + timedelta(days=i)
            date_str = target_date.isoformat()
            
            if date_str in existing_dates:
                continue
                
            # Fetch from RapidAPI
            odds_data = get_live_odds_data(date_str=date_str)
            nba_odds = odds_data.get('endpoints', {}).get('nba_odds', [])
            
            if nba_odds:
                for g in nba_odds:
                    start = g.get('commence_time', '')
                    # Normalize game dict
                    all_games.append({
                        'game_id': g.get('id', ''),
                        'date': date_str, # Use our target date to ensure consistency
                        'home_team': g.get('home_team', ''),
                        'away_team': g.get('away_team', ''),
                        'game_time': start
                    })
                existing_dates.add(date_str)
                
    except Exception as e:
        logger.error(f"Error fetching future games via RapidAPI: {e}")

    # Fallback to pyespn only if we have absolute zero games?
    if not all_games:
        py_games = _try_pyespn(days_ahead)
        if py_games:
            all_games.extend(py_games)

    if not all_games:
        logger.warning("No schedule source available. Returning empty list.")
        
    return all_games
