import json
import time
from pathlib import Path
from datetime import datetime
from nba_api.stats.endpoints import leaguegamefinder, leaguedashplayerstats

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SEASON = "2023-24"

def fetch_games():
    print(f"Fetching games for {SEASON}...")
    try:
        finder = leaguegamefinder.LeagueGameFinder(season_nullable=SEASON, league_id_nullable='00')
        games = finder.get_dict()['resultSets'][0]
        headers = games['headers']
        rows = games['rowSet']
        game_list = [dict(zip(headers, row)) for row in rows]
        
        print(f"Found {len(game_list)} games.")
        
        output_file = OUTPUT_DIR / f"games_{SEASON.replace('-', '_')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'season': SEASON,
                'games': game_list,
                'downloaded_at': datetime.now().isoformat()
            }, f, indent=2)
        print(f"Saved games to {output_file}")
        return len(game_list)
    except Exception as e:
        print(f"Error fetching games: {e}")
        return 0

def fetch_players():
    print(f"Fetching player stats for {SEASON}...")
    try:
        stats = leaguedashplayerstats.LeagueDashPlayerStats(season=SEASON)
        data = stats.get_dict()['resultSets'][0]
        headers = data['headers']
        rows = data['rowSet']
        player_list = [dict(zip(headers, row)) for row in rows]
        
        print(f"Found {len(player_list)} players.")
        
        output_file = OUTPUT_DIR / f"player_stats_{SEASON.replace('-', '_')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'season': SEASON,
                'player_stats': player_list,
                'downloaded_at': datetime.now().isoformat()
            }, f, indent=2)
        print(f"Saved player stats to {output_file}")
        return len(player_list)
    except Exception as e:
        print(f"Error fetching players: {e}")
        return 0

if __name__ == "__main__":
    fetch_games()
    time.sleep(1)
    fetch_players()
