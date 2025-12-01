"""
Test RapidAPI Integration
Verifies all NBA API endpoints are working correctly
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.api.rapid_api_client import rapid_api_client
from src.common.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_endpoint(name: str, func, *args, **kwargs) -> bool:
    """Test a single API endpoint"""
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing: {name}")
        logger.info(f"{'='*60}")
        
        result = func(*args, **kwargs)
        
        if result:
            logger.info(f"✅ SUCCESS: {name}")
            logger.info(f"Response type: {type(result)}")
            if isinstance(result, dict):
                logger.info(f"Keys: {list(result.keys())[:10]}")  # Show first 10 keys
            return True
        else:
            logger.warning(f"⚠️  NO DATA: {name}")
            return False
    except Exception as e:
        logger.error(f"❌ FAILED: {name}")
        logger.error(f"Error: {e}")
        return False


def main():
    """Test all RapidAPI endpoints"""
    
    print("\n" + "="*80)
    print("NBA RAPIDAPI INTEGRATION TEST")
    print("="*80)
    
    # Verify API key is set
    if not settings.nba_stats_api_key or settings.nba_stats_api_key == "test_key_for_now":
        print("\n❌ ERROR: NBA_STATS_API_KEY is not set in .env file")
        print("Please update .env with your RapidAPI key")
        return
    
    print(f"\n🔑 API Key configured: {settings.nba_stats_api_key[:10]}...")
    
    results = {}
    
    # Test NBA API Free Data endpoints
    print("\n\n" + "="*80)
    print("🏀 TESTING NBA API FREE DATA")
    print("="*80)
    
    results["league_info"] = test_endpoint(
        "NBA League Info",
        rapid_api_client.get_nba_league_info
    )
    
    results["sport_info"] = test_endpoint(
        "NBA Sport Info",
        rapid_api_client.get_nba_sport_info
    )
    
    results["teams"] = test_endpoint(
        "NBA Teams",
        rapid_api_client.get_nba_teams
    )
    
    results["scoreboard"] = test_endpoint(
        "NBA Scoreboard",
        rapid_api_client.get_nba_scoreboard
    )
    
    results["schedule"] = test_endpoint(
        "NBA Schedule",
        rapid_api_client.get_nba_schedule
    )
    
    results["standings"] = test_endpoint(
        "NBA Standings",
        rapid_api_client.get_nba_standings
    )
    
    results["players"] = test_endpoint(
        "NBA Players",
        rapid_api_client.get_nba_players
    )
    
    results["statistics"] = test_endpoint(
        "NBA Statistics",
        rapid_api_client.get_nba_statistics
    )
    
    # Test Player Props endpoints
    print("\n\n" + "="*80)
    print("🎯 TESTING PLAYER PROPS ODDS")
    print("="*80)
    
    results["events_today"] = test_endpoint(
        "Events For Today",
        rapid_api_client.get_events_for_today
    )
    
    results["all_markets"] = test_endpoint(
        "All Markets",
        rapid_api_client.get_all_markets
    )
    
    results["all_bookies"] = test_endpoint(
        "All Bookies",
        rapid_api_client.get_all_bookies
    )
    
    # Test Injury Data
    print("\n\n" + "="*80)
    print("🏥 TESTING INJURY DATA")
    print("="*80)
    
    results["injury_reports"] = test_endpoint(
        "Injury Reports",
        rapid_api_client.get_injury_reports
    )
    
    # Test Live Sports Odds
    print("\n\n" + "="*80)
    print("💰 TESTING LIVE SPORTS ODDS")
    print("="*80)
    
    results["sports_list"] = test_endpoint(
        "Sports List",
        rapid_api_client.get_sports_list
    )
    
    results["nba_odds"] = test_endpoint(
        "NBA Odds",
        rapid_api_client.get_nba_odds
    )
    
    results["nba_scores"] = test_endpoint(
        "NBA Scores",
        rapid_api_client.get_nba_scores
    )
    
    # Test Schedule API
    print("\n\n" + "="*80)
    print("📅 TESTING SCHEDULE API")
    print("="*80)
    
    results["schedule_data"] = test_endpoint(
        "Schedule Data",
        rapid_api_client.get_schedule_data
    )
    
    # Test Daily Leaders
    print("\n\n" + "="*80)
    print("📊 TESTING DAILY LEADERS")
    print("="*80)
    
    results["daily_leaders"] = test_endpoint(
        "Daily Leaders",
        rapid_api_client.get_daily_leaders
    )
    
    # Test Latest News
    print("\n\n" + "="*80)
    print("📰 TESTING LATEST NEWS")
    print("="*80)
    
    results["latest_news"] = test_endpoint(
        "Latest News",
        rapid_api_client.get_latest_news,
        limit=5
    )
    
    # Test Free NBA API
    print("\n\n" + "="*80)
    print("🆓 TESTING FREE NBA API")
    print("="*80)
    
    results["all_players"] = test_endpoint(
        "All Players",
        rapid_api_client.get_all_players,
        per_page=10
    )
    
    results["all_teams_free"] = test_endpoint(
        "All Teams (Free NBA)",
        rapid_api_client.get_all_teams
    )
    
    results["all_games"] = test_endpoint(
        "All Games",
        rapid_api_client.get_all_games,
        per_page=10
    )
    
    results["all_stats"] = test_endpoint(
        "All Stats",
        rapid_api_client.get_all_stats,
        per_page=10
    )
    
    # Test NBA Results Pro
    print("\n\n" + "="*80)
    print("🏆 TESTING NBA RESULTS PRO")
    print("="*80)
    
    results["teams_info"] = test_endpoint(
        "Teams Info",
        rapid_api_client.get_teams_info
    )
    
    results["games_info"] = test_endpoint(
        "Games Info",
        rapid_api_client.get_games_info
    )
    
    # Test Fantasy Sports
    print("\n\n" + "="*80)
    print("🎮 TESTING FANTASY SPORTS")
    print("="*80)
    
    results["fantasy_ros_g"] = test_endpoint(
        "Fantasy ROS (Guards)",
        rapid_api_client.get_nba_fantasy_rest_of_season,
        "G"
    )
    
    results["fantasy_week_f"] = test_endpoint(
        "Fantasy Week (Forwards)",
        rapid_api_client.get_nba_fantasy_current_week,
        "F"
    )
    
    # Test Basketball Data
    print("\n\n" + "="*80)
    print("🏀 TESTING BASKETBALL DATA")
    print("="*80)
    
    results["games_list"] = test_endpoint(
        "Games List",
        rapid_api_client.get_games_list,
        "2024"
    )
    
    # Test NBA Backtest
    print("\n\n" + "="*80)
    print("🎲 TESTING NBA BACKTEST")
    print("="*80)
    
    results["sim_day"] = test_endpoint(
        "Simulated Day",
        rapid_api_client.get_sim_day
    )
    
    results["random_set"] = test_endpoint(
        "Random Set",
        rapid_api_client.get_random_set,
        10
    )
    
    # Test Sports Odds API
    print("\n\n" + "="*80)
    print("💵 TESTING SPORTS ODDS API")
    print("="*80)
    
    results["nba_futures"] = test_endpoint(
        "NBA Futures",
        rapid_api_client.get_nba_futures
    )
    
    results["nba_game_odds"] = test_endpoint(
        "NBA Game Odds",
        rapid_api_client.get_nba_game_odds
    )
    
    # Print Summary
    print("\n\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests
    
    print(f"\nTotal Endpoints Tested: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    print("\n" + "="*80)
    print("DETAILED RESULTS")
    print("="*80)
    
    for name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {name}")
    
    if failed_tests > 0:
        print("\n⚠️  Some endpoints failed. This could be due to:")
        print("   - Rate limiting (free tier restrictions)")
        print("   - No data available for the current date/time")
        print("   - API endpoint changes")
        print("   - Network issues")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
