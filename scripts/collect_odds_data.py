#!/usr/bin/env python3
"""
Quick NBA Odds Data Collection
Collects betting odds from the working Live Sports Odds API
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.api.rapid_api_client import rapid_api_client

def collect_odds_data():
    """Collect NBA betting odds and scores"""
    print("\n" + "="*60)
    print("🏀 NBA BETTING ODDS DATA COLLECTION")
    print("="*60)
    
    output_dir = Path("data/raw/odds")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Collect current odds
    print("\n📊 Fetching NBA betting odds...")
    odds_data = rapid_api_client.get_nba_odds(
        regions="us",
        markets="h2h,spreads,totals",
        odds_format="american"
    )
    
    if odds_data:
        print(f"✅ Found {len(odds_data)} games with odds")
        
        # Save odds data
        odds_file = output_dir / f"nba_odds_{timestamp}.json"
        with open(odds_file, 'w') as f:
            json.dump(odds_data, f, indent=2)
        print(f"💾 Saved to: {odds_file}")
        
        # Print summary
        print("\n📋 Games with odds:")
        for i, game in enumerate(odds_data[:5], 1):  # Show first 5
            print(f"\n{i}. {game['away_team']} @ {game['home_team']}")
            print(f"   Start time: {game['commence_time']}")
            print(f"   Bookmakers: {len(game.get('bookmakers', []))}")
            
            # Show first bookmaker's odds
            if game.get('bookmakers'):
                bookie = game['bookmakers'][0]
                print(f"   {bookie['title']}:")
                for market in bookie.get('markets', []):
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            print(f"     - {outcome['name']}: {outcome['price']}")
        
        if len(odds_data) > 5:
            print(f"\n   ... and {len(odds_data) - 5} more games")
    else:
        print("⚠️  No odds data available")
    
    # Collect recent scores
    print("\n📊 Fetching recent NBA scores...")
    scores_data = rapid_api_client.get_nba_scores(days_from=3)
    
    if scores_data:
        completed_games = [g for g in scores_data if g.get('completed')]
        print(f"✅ Found {len(completed_games)} completed games")
        
        # Save scores data
        scores_file = output_dir / f"nba_scores_{timestamp}.json"
        with open(scores_file, 'w') as f:
            json.dump(scores_data, f, indent=2)
        print(f"💾 Saved to: {scores_file}")
        
        # Print recent results
        print("\n📋 Recent results:")
        for i, game in enumerate(completed_games[:5], 1):  # Show first 5
            scores = game.get('scores', [])
            if len(scores) >= 2:
                print(f"{i}. {game['away_team']} {scores[0].get('score', '?')} @ "
                      f"{game['home_team']} {scores[1].get('score', '?')}")
        
        if len(completed_games) > 5:
            print(f"   ... and {len(completed_games) - 5} more results")
    else:
        print("⚠️  No scores data available")
    
    # Create summary
    summary = {
        "collection_timestamp": datetime.now().isoformat(),
        "data_collected": {
            "odds": {
                "games_count": len(odds_data) if odds_data else 0,
                "file": str(odds_file.name) if odds_data else None
            },
            "scores": {
                "games_count": len(scores_data) if scores_data else 0,
                "completed_games": len(completed_games) if scores_data else 0,
                "file": str(scores_file.name) if scores_data else None
            }
        }
    }
    
    summary_file = output_dir / f"collection_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ DATA COLLECTION COMPLETE")
    print("="*60)
    print(f"\nFiles saved in: {output_dir}")
    print(f"- Odds: {odds_file.name if odds_data else 'N/A'}")
    print(f"- Scores: {scores_file.name if scores_data else 'N/A'}")
    print(f"- Summary: {summary_file.name}")
    print("\n💡 Use this data to train your betting models!")
    print("="*60 + "\n")
    
    return summary

if __name__ == "__main__":
    try:
        collect_odds_data()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
