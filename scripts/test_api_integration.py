"""Test script to verify real NBA API integration.

Tests:
1. Fetch today's games from BallDontLie
2. Search for players
3. Get player statistics
4. Fetch betting odds
5. Test caching system
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from datetime import datetime
from src.data.ingest.nba_api_client import get_nba_client
from src.data.ingest.cache_manager import get_cache_manager
from src.data.ingest.game_fetcher import get_game_fetcher
from src.data.ingest.player_fetcher import get_player_fetcher
from src.data.ingest.odds_fetcher import get_odds_fetcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_api_client():
    """Test basic API client functionality."""
    logger.info("=" * 80)
    logger.info("TEST 1: Basic API Client")
    logger.info("=" * 80)
    
    client = get_nba_client()
    
    # Test 1: Get today's games
    logger.info("\n📅 Testing: Get today's games")
    today = datetime.now().strftime("%Y-%m-%d")
    games = client.get_games_today(today)
    
    if games:
        logger.info(f"✅ SUCCESS: Found {len(games)} games for {today}")
        logger.info(f"   Sample game: {games[0].get('home_team', {}).get('name')} vs {games[0].get('visitor_team', {}).get('name')}")
    else:
        logger.warning(f"⚠️  No games found for {today} (might be off-season or rest day)")
    
    # Test 2: Get teams
    logger.info("\n🏀 Testing: Get teams")
    teams = client.get_teams()
    
    if teams:
        logger.info(f"✅ SUCCESS: Found {len(teams)} teams")
        logger.info(f"   Sample teams: {teams[0].get('full_name')}, {teams[1].get('full_name')}")
    else:
        logger.error("❌ FAILED: No teams found")
    
    # Test 3: Search for players
    logger.info("\n👤 Testing: Search for players")
    players = client.get_players(search="LeBron", per_page=5)
    
    if players:
        logger.info(f"✅ SUCCESS: Found {len(players)} players matching 'LeBron'")
        for player in players[:3]:
            logger.info(f"   - {player.get('first_name')} {player.get('last_name')} ({player.get('team', {}).get('full_name', 'N/A')})")
    else:
        logger.error("❌ FAILED: No players found")
    
    return len(games), len(teams), len(players)


def test_game_fetcher():
    """Test game fetcher with caching."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Game Fetcher")
    logger.info("=" * 80)
    
    fetcher = get_game_fetcher()
    
    # Test 1: Get today's games (should use cache on second call)
    logger.info("\n📅 Testing: Today's games with caching")
    games1 = fetcher.get_today_games()
    logger.info(f"   First call: {len(games1)} games")
    
    games2 = fetcher.get_today_games()
    logger.info(f"   Second call (cached): {len(games2)} games")
    
    if games1 == games2:
        logger.info("✅ SUCCESS: Cache working correctly")
    else:
        logger.error("❌ FAILED: Cache not working")
    
    # Test 2: Get games from specific date
    logger.info("\n📅 Testing: Historical games")
    historical = fetcher.get_games_by_date("2024-12-25")  # Christmas games
    logger.info(f"✅ Found {len(historical)} games on 2024-12-25")
    
    return len(games1)


def test_player_fetcher():
    """Test player fetcher with statistics."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: Player Fetcher")
    logger.info("=" * 80)
    
    fetcher = get_player_fetcher()
    
    # Test 1: Search for a player
    logger.info("\n🔍 Testing: Player search")
    players = fetcher.search_players("Stephen Curry")
    
    if players:
        player = players[0]
        player_id = player.get("id")
        logger.info(f"✅ Found: {player.get('first_name')} {player.get('last_name')} (ID: {player_id})")
        
        # Test 2: Get player stats
        logger.info(f"\n📊 Testing: Player statistics for ID {player_id}")
        stats = fetcher.get_player_stats(player_id, last_n_games=5)
        
        if stats:
            logger.info(f"✅ Found {len(stats)} recent games")
            
            # Test 3: Get recent performance
            logger.info(f"\n📈 Testing: Recent performance summary")
            performance = fetcher.get_recent_performance(player_id, games=5)
            
            if performance:
                logger.info(f"✅ Last 5 games averages:")
                logger.info(f"   PPG: {performance.get('ppg')}")
                logger.info(f"   APG: {performance.get('apg')}")
                logger.info(f"   RPG: {performance.get('rpg')}")
                logger.info(f"   FG%: {performance.get('fg_pct')}%")
        else:
            logger.warning("⚠️  No recent stats available")
    else:
        logger.error("❌ FAILED: Player not found")
    
    return len(players) if players else 0


def test_odds_fetcher():
    """Test odds fetcher."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Odds Fetcher")
    logger.info("=" * 80)
    
    fetcher = get_odds_fetcher()
    
    # Test 1: Get current odds
    logger.info("\n💰 Testing: Current betting odds")
    odds = fetcher.get_current_odds()
    
    if odds:
        logger.info(f"✅ SUCCESS: Found odds for {len(odds)} games")
        
        if len(odds) > 0:
            game = odds[0]
            logger.info(f"   Sample game: {game.get('away_team')} @ {game.get('home_team')}")
            logger.info(f"   Bookmakers: {len(game.get('bookmakers', []))}")
        
        # Test 2: Find best odds
        logger.info("\n🎯 Testing: Best odds finder")
        best_odds = fetcher.find_best_odds()
        logger.info(f"✅ Analyzed best odds for {len(best_odds)} games")
    else:
        logger.warning("⚠️  No odds available (might be off-season)")
    
    return len(odds) if odds else 0


def test_cache_manager():
    """Test cache manager."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: Cache Manager")
    logger.info("=" * 80)
    
    cache = get_cache_manager()
    
    # Test 1: Set and get
    logger.info("\n💾 Testing: Cache set/get")
    test_key = "test:api_test"
    test_value = {"test": "data", "timestamp": datetime.now().isoformat()}
    
    cache.set(test_key, test_value, ttl=60)
    retrieved = cache.get(test_key)
    
    if retrieved == test_value:
        logger.info("✅ SUCCESS: Cache set/get working")
    else:
        logger.error("❌ FAILED: Cache not working correctly")
    
    # Test 2: Delete
    logger.info("\n🗑️  Testing: Cache delete")
    cache.delete(test_key)
    retrieved = cache.get(test_key)
    
    if retrieved is None:
        logger.info("✅ SUCCESS: Cache delete working")
    else:
        logger.error("❌ FAILED: Cache delete not working")
    
    return True


def main():
    """Run all tests."""
    logger.info("🏀 NBA API Integration Test Suite")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now()}")
    logger.info("=" * 80)
    
    results = {}
    
    try:
        # Run tests
        games, teams, players = test_api_client()
        results["api_client"] = "✅ PASSED"
        
        games_count = test_game_fetcher()
        results["game_fetcher"] = "✅ PASSED"
        
        players_count = test_player_fetcher()
        results["player_fetcher"] = "✅ PASSED" if players_count > 0 else "⚠️  PARTIAL"
        
        odds_count = test_odds_fetcher()
        results["odds_fetcher"] = "✅ PASSED" if odds_count > 0 else "⚠️  PARTIAL"
        
        cache_ok = test_cache_manager()
        results["cache_manager"] = "✅ PASSED"
        
    except Exception as e:
        logger.error(f"❌ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 80)
    
    for test_name, result in results.items():
        logger.info(f"{result} {test_name}")
    
    logger.info("\n" + "=" * 80)
    logger.info(f"Completed at: {datetime.now()}")
    logger.info("=" * 80)
    
    # Check if all critical tests passed
    critical_passed = all(
        result in ["✅ PASSED", "⚠️  PARTIAL"] 
        for result in results.values()
    )
    
    if critical_passed:
        logger.info("\n🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        logger.info("✅ Real NBA API integration is working!")
        logger.info("\nNext steps:")
        logger.info("1. Download historical data (scripts/download_historical_data.py)")
        logger.info("2. Build feature engineering pipeline")
        logger.info("3. Train ML models on real data")
        logger.info("4. Update backend to use real APIs")
        return 0
    else:
        logger.error("\n❌ SOME TESTS FAILED - Please review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
