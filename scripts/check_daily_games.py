"""
Script to check daily games and odds.
Run this to verify what games are detected by the system for the upcoming days.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.live_schedule import get_upcoming_games
from src.api.live_odds import get_live_odds_data

def main():
    print("="*60)
    print(f"🏀 NBA DAILY GAMES CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # 1. Fetch Schedule
    print("\n📅 Fetching Schedule (next 7 days)...")
    try:
        games = get_upcoming_games(days_ahead=7)
        if not games:
            print("❌ No upcoming games found in schedule source.")
        else:
            print(f"✅ Found {len(games)} games.")
            
            # Group by date
            games_by_date = {}
            for g in games:
                d = g.get('date', 'Unknown')
                if d not in games_by_date:
                    games_by_date[d] = []
                games_by_date[d].append(g)
            
            # Print by date
            for d in sorted(games_by_date.keys()):
                print(f"\n  Date: {d}")
                for g in games_by_date[d]:
                    print(f"    - {g.get('away_team')} @ {g.get('home_team')} ({g.get('game_time')})")

    except Exception as e:
        print(f"❌ Error fetching schedule: {e}")

    # 2. Fetch Live Odds
    print("\n💰 Fetching Live Odds...")
    try:
        odds_data = get_live_odds_data()
        nba_odds = odds_data.get('endpoints', {}).get('nba_odds', [])
        
        if not nba_odds:
            print("❌ No live odds data found.")
        else:
            print(f"✅ Found odds for {len(nba_odds)} games.")
            
            for game in nba_odds:
                home = game.get('home_team')
                away = game.get('away_team')
                start = game.get('commence_time')
                
                # Extract best odds (simplified)
                bookmakers = game.get('bookmakers', [])
                home_price = "N/A"
                away_price = "N/A"
                
                if bookmakers:
                    # Just take the first bookmaker for display
                    bm = bookmakers[0]
                    markets = bm.get('markets', [])
                    for m in markets:
                        if m.get('key') == 'h2h':
                            for outcome in m.get('outcomes', []):
                                if outcome.get('name') == home:
                                    home_price = outcome.get('price')
                                elif outcome.get('name') == away:
                                    away_price = outcome.get('price')
                
                print(f"    - {away} ({away_price}) @ {home} ({home_price}) [{start}]")

    except Exception as e:
        print(f"❌ Error fetching odds: {e}")

    print("\n" + "="*60)

if __name__ == "__main__":
    main()
