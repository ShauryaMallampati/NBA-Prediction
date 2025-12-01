#!/usr/bin/env python3
"""
Collect data from working RapidAPI endpoints
Focus on: sports_list, nba_odds, nba_scores, nba_futures, nba_game_odds
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.api.rapid_api_client import rapid_api_client

def collect_working_endpoints_data():
    """Collect data from all verified working endpoints"""
    print("\n" + "="*80)
    print("🏀 COLLECTING DATA FROM WORKING RAPIDAPI ENDPOINTS")
    print("="*80)
    
    output_dir = Path("data/raw/rapid_api_working")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    all_data = {
        "collection_timestamp": datetime.now().isoformat(),
        "endpoints": {}
    }
    
    # 1. Sports List
    print("\n📊 Collecting Sports List...")
    sports_list = rapid_api_client.get_sports_list()
    if sports_list:
        all_data["endpoints"]["sports_list"] = sports_list
        print(f"✅ Got {len(sports_list)} sports")
    
    # 2. NBA Odds (most important for betting)
    print("\n💰 Collecting NBA Odds (all markets)...")
    nba_odds = rapid_api_client.get_nba_odds(
        regions="us,uk,eu,au",  # Get from all regions
        markets="h2h,spreads,totals",
        odds_format="american"
    )
    if nba_odds:
        all_data["endpoints"]["nba_odds"] = nba_odds
        print(f"✅ Got odds for {len(nba_odds)} games")
        print(f"   Bookmakers per game: {len(nba_odds[0].get('bookmakers', [])) if nba_odds else 0}")
    
    # 3. NBA Scores (for validation and historical data)
    print("\n📈 Collecting NBA Scores (last 7 days)...")
    nba_scores = rapid_api_client.get_nba_scores(days_from=7)
    if nba_scores:
        all_data["endpoints"]["nba_scores"] = nba_scores
        completed = [g for g in nba_scores if g.get('completed')]
        print(f"✅ Got {len(nba_scores)} games ({len(completed)} completed)")
    
    # 4. NBA Futures
    print("\n🏆 Collecting NBA Futures...")
    futures_types = ["nbafinals", "conference", "division"]
    all_data["endpoints"]["nba_futures"] = {}
    
    for future_type in futures_types:
        futures = rapid_api_client.get_nba_futures(
            group_name=future_type,
            season="2024"
        )
        if futures:
            all_data["endpoints"]["nba_futures"][future_type] = futures
            print(f"✅ Got {future_type} futures")
    
    # 5. NBA Game Odds (alternative source)
    print("\n🎲 Collecting NBA Game Odds (alternative)...")
    game_odds = rapid_api_client.get_nba_game_odds()
    if game_odds:
        all_data["endpoints"]["nba_game_odds"] = game_odds
        print(f"✅ Got alternative game odds")
    
    # Save all collected data
    output_file = output_dir / f"nba_comprehensive_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump(all_data, f, indent=2)
    
    print("\n" + "="*80)
    print("✅ DATA COLLECTION COMPLETE")
    print("="*80)
    print(f"\nData saved to: {output_file}")
    print(f"File size: {output_file.stat().st_size / 1024:.2f} KB")
    
    # Print summary
    print("\n📊 COLLECTION SUMMARY:")
    for endpoint, data in all_data["endpoints"].items():
        if isinstance(data, list):
            print(f"  ✅ {endpoint}: {len(data)} items")
        elif isinstance(data, dict):
            print(f"  ✅ {endpoint}: {len(data)} keys")
    
    return all_data

def collect_historical_odds_series():
    """Collect odds multiple times to build historical dataset"""
    print("\n" + "="*80)
    print("📊 COLLECTING HISTORICAL ODDS SERIES")
    print("="*80)
    
    output_dir = Path("data/raw/odds_history")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect current odds
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    odds = rapid_api_client.get_nba_odds()
    
    if odds:
        filename = output_dir / f"odds_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "games": odds
            }, f, indent=2)
        print(f"✅ Saved odds snapshot: {filename.name}")
        print(f"   Games: {len(odds)}")
        return True
    return False

if __name__ == "__main__":
    # Collect comprehensive data
    data = collect_working_endpoints_data()
    
    # Also collect historical series
    print("\n")
    collect_historical_odds_series()
    
    print("\n💡 TIP: Run this script multiple times per day to track line movement")
    print("   and build historical odds dataset for model training!")
