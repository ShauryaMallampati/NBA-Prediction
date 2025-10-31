"""Demo script showing real NBA data integration.

Demonstrates:
1. Fetching all NBA teams
2. Searching for star players
3. Getting recent player statistics
4. Formatted output showing the data is real
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from datetime import datetime
from src.data.ingest.nba_api_client import get_nba_client
from src.data.ingest.player_fetcher import get_player_fetcher

# Set up logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings/errors for cleaner output
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def demo_teams():
    """Demo: Fetch and display all NBA teams."""
    print_header("🏀 NBA TEAMS (Real Data from stats.nba.com)")
    
    client = get_nba_client()
    teams = client.get_teams()
    
    print(f"\n📊 Total Teams: {len(teams)}\n")
    
    # Display teams in columns
    for i, team in enumerate(teams, 1):
        name = team.get('full_name', 'Unknown')
        abbr = team.get('abbreviation', 'N/A')
        print(f"  {i:2d}. {name:30s} ({abbr})")
    
    print(f"\n✅ Successfully retrieved {len(teams)} NBA teams from real API")


def demo_player_search():
    """Demo: Search for star players."""
    print_header("👤 PLAYER SEARCH (Real Data)")
    
    star_players = ["LeBron James", "Stephen Curry", "Kevin Durant", "Giannis Antetokounmpo", "Luka Doncic"]
    
    fetcher = get_player_fetcher()
    
    print("\n🔍 Searching for NBA superstars...\n")
    
    found_players = []
    
    for player_name in star_players:
        players = fetcher.search_players(player_name)
        
        if players:
            player = players[0]
            found_players.append(player)
            
            print(f"  ✅ {player.get('full_name', 'Unknown'):25s} | ID: {player.get('id'):6d} | Active: {player.get('is_active', False)}")
        else:
            print(f"  ❌ {player_name:25s} | Not found")
    
    print(f"\n✅ Found {len(found_players)} star players from real API")
    return found_players


def demo_player_stats(players: list):
    """Demo: Get recent stats for players."""
    print_header("📊 RECENT PLAYER STATISTICS (Last 5 Games)")
    
    fetcher = get_player_fetcher()
    
    print("\n🏀 Fetching recent performance data...\n")
    print(f"{'Player':<25s} {'PPG':>6s} {'APG':>6s} {'RPG':>6s} {'FG%':>6s} {'Games':>6s}")
    print("-" * 80)
    
    for player in players[:5]:  # Limit to 5 players to avoid rate limits
        player_id = player.get('id')
        player_name = player.get('full_name', 'Unknown')
        
        # Get recent performance
        performance = fetcher.get_recent_performance(player_id, games=5)
        
        if performance:
            ppg = performance.get('ppg', 0)
            apg = performance.get('apg', 0)
            rpg = performance.get('rpg', 0)
            fg_pct = performance.get('fg_pct', 0)
            games = performance.get('games_analyzed', 0)
            
            print(f"{player_name:<25s} {ppg:6.1f} {apg:6.1f} {rpg:6.1f} {fg_pct:5.1f}% {games:6d}")
        else:
            print(f"{player_name:<25s} {'No recent stats available':>30s}")
    
    print("\n✅ Retrieved real player statistics from stats.nba.com")


def demo_cache_info():
    """Demo: Show cache information."""
    print_header("💾 CACHE SYSTEM")
    
    from src.data.ingest.cache_manager import get_cache_manager, CACHE_DIR
    
    cache = get_cache_manager()
    
    print(f"\n📁 Cache Directory: {CACHE_DIR}")
    print(f"📊 Redis Available: {cache.redis_available}")
    print(f"📂 Using File Cache: {not cache.redis_available}")
    
    # Count cached files
    cache_files = list(CACHE_DIR.glob("*.json"))
    print(f"💾 Cached Files: {len(cache_files)}")
    
    if cache_files:
        print("\nRecent cache files:")
        for cache_file in sorted(cache_files, key=lambda f: f.stat().st_mtime, reverse=True)[:5]:
            size = cache_file.stat().st_size / 1024  # KB
            print(f"  📄 {cache_file.name[:50]:<50s} ({size:.1f} KB)")
    
    print("\n✅ Cache system operational (file-based storage)")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("  🏀 NBA INTEL - REAL API INTEGRATION DEMO")
    print("  Powered by stats.nba.com via nba_api package")
    print("=" * 80)
    print(f"\n⏰ Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Demo 1: Teams
        demo_teams()
        
        # Demo 2: Player Search
        players = demo_player_search()
        
        # Demo 3: Player Stats
        if players:
            demo_player_stats(players)
        
        # Demo 4: Cache Info
        demo_cache_info()
        
        # Summary
        print_header("📈 DEMO SUMMARY")
        print("\n✅ All demos completed successfully!")
        print("\n🎯 What we demonstrated:")
        print("  1. ✅ Real NBA team data (30 teams)")
        print("  2. ✅ Real player search (superstar lookup)")
        print("  3. ✅ Real player statistics (recent performance)")
        print("  4. ✅ Caching system (file-based with Redis fallback)")
        
        print("\n🚀 Next Steps:")
        print("  • Download historical data (2015-2025 seasons)")
        print("  • Build feature engineering pipeline (53 features)")
        print("  • Train ML models on real data (5 LightGBM models)")
        print("  • Update backend API endpoints to use real data")
        print("  • Update frontend to display real live data")
        
        print("\n" + "=" * 80)
        print(f"⏰ Demo completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
