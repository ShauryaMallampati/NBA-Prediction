"""
Live schedule fetcher using available libraries (nba_api, pyespn) with safe fallbacks.

The functions here try to import and use `nba_api` first (preferred), then `pyespn` as a fallback.
If neither library is installed or fails, the module returns an empty list and logs the issue —
the FastAPI route that consumes this will fall back to RapidAPI or the existing data pipeline.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import asyncio

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


async def get_upcoming_games_async(days_ahead: int = 14) -> List[Dict[str, Any]]:
    """Async: Return upcoming NBA games for the next `days_ahead` days.
    
    Optimized to use a single range API call.
    """
    all_games = []
    
    # 1. Try nba_api (mostly for today)
    # Since nba_api is sync, run in thread
    todays_games = await asyncio.to_thread(_try_nba_api, days_ahead)
    if todays_games:
        all_games.extend(todays_games)
        
    existing_game_ids = set(g['game_id'] for g in all_games)
    
    # 2. Single call for future dates using RapidAPI range fetch
    try:
        from src.api.live_odds import get_live_odds_data_async
        
        start_date = datetime.utcnow().date()
        end_date = start_date + timedelta(days=min(days_ahead, 14))
        
        # Optimized: Fetch ALL days at once
        odds_data = await get_live_odds_data_async(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        nba_odds = odds_data.get('endpoints', {}).get('nba_odds', [])
        
        for g in nba_odds:
            game_id = g.get('id', '')
            if game_id and game_id in existing_game_ids:
                continue
                
            start = g.get('commence_time', '')
            date_str = start.split('T')[0] if 'T' in start else ''
            
            all_games.append({
                'game_id': game_id,
                'date': date_str,
                'home_team': g.get('home_team', ''),
                'away_team': g.get('away_team', ''),
                'game_time': start
            })
            if game_id:
                existing_game_ids.add(game_id)
                
    except Exception as e:
        logger.error(f"Error fetching future games via RapidAPI: {e}")

    # Fallback to pyespn
    if not all_games:
        py_games = await asyncio.to_thread(_try_pyespn, days_ahead)
        if py_games:
            all_games.extend(py_games)

    return all_games


def get_upcoming_games(days_ahead: int = 14) -> List[Dict[str, Any]]:
    """Sync version of get_upcoming_games.
    
    Warning: This still uses the old N+1 loop for compatibility 
    if not called from an async context, but it's better to use the async version.
    """
    # Try to run async version if possible
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # In an event loop, we can't use asyncio.run
            # Use the old logic as fallback or ideally callers should use the async version
            pass
        else:
            return asyncio.run(get_upcoming_games_async(days_ahead))
    except Exception:
        pass

    # Original logic (N+1 fallback)
    all_games = []
    todays_games = _try_nba_api(days_ahead)
    if todays_games:
        all_games.extend(todays_games)
        
    existing_dates = set(g['date'] for g in all_games)
    
    try:
        from src.api.live_odds import get_live_odds_data
        start_date = datetime.utcnow().date()
        scan_days = min(days_ahead, 7)
        
        for i in range(0, scan_days + 1):
            target_date = start_date + timedelta(days=i)
            date_str = target_date.isoformat()
            if date_str in existing_dates: continue
            
            odds_data = get_live_odds_data(date_str=date_str)
            nba_odds = odds_data.get('endpoints', {}).get('nba_odds', [])
            for g in nba_odds:
                all_games.append({
                    'game_id': g.get('id', ''),
                    'date': date_str,
                    'home_team': g.get('home_team', ''),
                    'away_team': g.get('away_team', ''),
                    'game_time': g.get('commence_time', '')
                })
            existing_dates.add(date_str)
    except Exception:
        pass
        
    if not all_games:
        all_games.extend(_try_pyespn(days_ahead))
        
    return all_games
