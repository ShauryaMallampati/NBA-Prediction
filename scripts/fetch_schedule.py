"""
Fetch and cache NBA schedule for the next 14 days.

This script is designed to run in GitHub Actions daily.
It fetches schedule data from multiple sources and caches it locally.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("FetchSchedule")

SCHEDULE_DIR = Path("data/schedules")


def fetch_from_nba_api(days_ahead: int = 14) -> List[Dict[str, Any]]:
    """Fetch schedule using nba_api."""
    try:
        from nba_api.stats.endpoints import LeagueGameFinder
        from nba_api.live.nba.endpoints import scoreboard
        
        games = []
        today = datetime.now().date()
        
        # Try live scoreboard for today
        try:
            sb = scoreboard.ScoreBoard()
            data = sb.get_dict()
            raw_games = data.get('games', [])
            
            for g in raw_games:
                games.append({
                    'game_id': g.get('gameId', ''),
                    'date': today.isoformat(),
                    'home_team': g.get('homeTeam', {}).get('teamName', ''),
                    'away_team': g.get('awayTeam', {}).get('teamName', ''),
                    'game_time': g.get('gameTimeUTC', ''),
                })
        except Exception as e:
            logger.warning(f"Live scoreboard failed: {e}")
        
        return games
    except Exception as e:
        logger.warning(f"nba_api failed: {e}")
        return []


def fetch_from_odds_api(days_ahead: int = 14) -> List[Dict[str, Any]]:
    """Fetch upcoming games from Odds API."""
    import os
    import requests
    
    api_key = os.getenv("ODDS_API_KEY")
    if not api_key or api_key == "your_key_here":
        logger.warning("ODDS_API_KEY not set")
        return []
    
    try:
        url = "https://api.the-odds-api.com/v4/sports/basketball_nba/events"
        params = {
            "apiKey": api_key,
            "dateFormat": "iso",
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        events = response.json()
        games = []
        
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        for event in events:
            commence_time = event.get("commence_time", "")
            if commence_time:
                event_date = datetime.fromisoformat(commence_time.replace("Z", "+00:00")).date()
                if today <= event_date <= end_date:
                    games.append({
                        'game_id': event.get('id', ''),
                        'date': event_date.isoformat(),
                        'home_team': event.get('home_team', ''),
                        'away_team': event.get('away_team', ''),
                        'game_time': commence_time,
                    })
        
        logger.info(f"Fetched {len(games)} games from Odds API")
        return games
    except Exception as e:
        logger.error(f"Odds API failed: {e}")
        return []


def merge_and_deduplicate(all_games: List[List[Dict]]) -> List[Dict[str, Any]]:
    """Merge games from multiple sources and remove duplicates."""
    seen = set()
    merged = []
    
    for games in all_games:
        for game in games:
            # Create a unique key based on date and teams
            key = f"{game['date']}_{game['home_team']}_{game['away_team']}"
            if key not in seen:
                seen.add(key)
                merged.append(game)
    
    # Sort by date
    merged.sort(key=lambda x: x['date'])
    return merged


def save_schedule(games: List[Dict[str, Any]], filename: str = "upcoming_14_days.json"):
    """Save schedule to JSON file."""
    SCHEDULE_DIR.mkdir(parents=True, exist_ok=True)
    
    output = {
        "fetched_at": datetime.now().isoformat(),
        "days_covered": 14,
        "total_games": len(games),
        "games": games,
    }
    
    output_path = SCHEDULE_DIR / filename
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"✅ Saved {len(games)} games to {output_path}")
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch NBA schedule")
    parser.add_argument("--days", type=int, default=14, help="Days ahead to fetch")
    args = parser.parse_args()
    
    logger.info(f"📅 Fetching schedule for next {args.days} days...")
    
    # Fetch from multiple sources
    nba_games = fetch_from_nba_api(args.days)
    odds_games = fetch_from_odds_api(args.days)
    
    # Merge and deduplicate
    all_games = merge_and_deduplicate([nba_games, odds_games])
    
    if all_games:
        save_schedule(all_games)
    else:
        logger.warning("No games fetched from any source")
    
    # Also update today's specific file
    today = datetime.now().strftime("%Y-%m-%d")
    today_games = [g for g in all_games if g['date'] == today]
    if today_games:
        save_schedule(today_games, f"{today}_schedule.json")
    
    logger.info("✅ Schedule fetch complete!")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    main()
