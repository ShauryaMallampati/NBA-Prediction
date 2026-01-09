"""
Scrape Full NBA Season Schedule

Fetches the complete 2024-25 NBA season schedule from NBA API.
This is a one-time scrape since the schedule doesn't change.
"""

import json
from pathlib import Path
from datetime import datetime
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Output path
OUTPUT_FILE = Path("data/nba_season_schedule_2024_25.json")


def scrape_season_schedule():
    """Scrape full 2024-25 NBA season schedule."""
    from nba_api.stats.endpoints import leaguegamefinder
    from nba_api.stats.static import teams
    
    logger.info("🏀 Fetching NBA 2024-25 season schedule...")
    
    # Get all NBA teams
    all_teams = teams.get_teams()
    team_lookup = {t['id']: t for t in all_teams}
    
    # Fetch games for current season
    try:
        finder = leaguegamefinder.LeagueGameFinder(
            season_nullable='2024-25',
            league_id_nullable='00',
            season_type_nullable='Regular Season'
        )
        games_data = finder.get_data_frames()[0]
        
        logger.info(f"   Found {len(games_data)} game records")
        
        # Group by game ID to get both teams
        games_by_id = {}
        
        for _, row in games_data.iterrows():
            game_id = row['GAME_ID']
            team_id = row['TEAM_ID']
            team_abbr = row['TEAM_ABBREVIATION']
            matchup = row['MATCHUP']
            game_date = row['GAME_DATE']
            
            # Determine home/away from matchup string
            is_home = '@' not in matchup
            
            if game_id not in games_by_id:
                games_by_id[game_id] = {
                    'game_id': game_id,
                    'date': game_date,
                    'home_team': None,
                    'away_team': None,
                    'home_team_id': None,
                    'away_team_id': None,
                }
            
            if is_home:
                games_by_id[game_id]['home_team'] = team_abbr
                games_by_id[game_id]['home_team_id'] = team_id
            else:
                games_by_id[game_id]['away_team'] = team_abbr
                games_by_id[game_id]['away_team_id'] = team_id
        
        # Convert to list and filter complete games
        games_list = [
            g for g in games_by_id.values() 
            if g['home_team'] and g['away_team']
        ]
        
        # Sort by date
        games_list.sort(key=lambda x: x['date'])
        
        logger.info(f"   Processed {len(games_list)} unique games")
        
        # Group by month for easier frontend consumption
        games_by_month = {}
        for game in games_list:
            date = datetime.strptime(game['date'], '%Y-%m-%d')
            month_key = date.strftime('%Y-%m')
            
            if month_key not in games_by_month:
                games_by_month[month_key] = []
            
            games_by_month[month_key].append({
                'game_id': game['game_id'],
                'date': game['date'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'time': '7:00 PM ET',  # Default time, can be enhanced
            })
        
        # Save to file
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        output = {
            'season': '2024-25',
            'total_games': len(games_list),
            'scraped_at': datetime.now().isoformat(),
            'months': games_by_month,
            'all_games': games_list
        }
        
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"✅ Saved schedule to {OUTPUT_FILE}")
        logger.info(f"   Months covered: {list(games_by_month.keys())}")
        
        return output
        
    except Exception as e:
        logger.error(f"❌ Error fetching schedule: {e}")
        return None


def get_upcoming_games_from_schedule(days_ahead=14):
    """Get upcoming games from the scraped schedule."""
    if not OUTPUT_FILE.exists():
        logger.warning("Schedule file not found, run scrape_season_schedule() first")
        return []
    
    with open(OUTPUT_FILE, 'r') as f:
        data = json.load(f)
    
    today = datetime.now().date()
    end_date = today + timedelta(days=days_ahead)
    
    upcoming = []
    for game in data.get('all_games', []):
        game_date = datetime.strptime(game['date'], '%Y-%m-%d').date()
        if today <= game_date <= end_date:
            upcoming.append(game)
    
    return upcoming


if __name__ == "__main__":
    scrape_season_schedule()
