"""
Master script to fetch all enhanced data sources.
Run this daily to keep your predictions fresh!
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from src.data.live_playbyplay import playbyplay_fetcher
from src.data.player_stats import stats_fetcher
from src.data.web_scraper import injury_scraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("\n" + "="*80)
    print("🚀 FETCHING ENHANCED NBA DATA")
    print("="*80)
    
    # 1. Play-by-Play Data
    print("\n1️⃣  Fetching Live Play-by-Play Data...")
    pbp_data = playbyplay_fetcher.get_current_season_data(max_games=10)  # Limit for demo
    if len(pbp_data) > 0:
        print(f"   ✅ Got {len(pbp_data)} play-by-play actions")
        
        # Extract momentum features
        pbp_enhanced = playbyplay_fetcher.extract_momentum_features(pbp_data)
        pbp_enhanced.to_parquet("data/playbyplay/enhanced_pbp.parquet")
        print(f"   ✅ Saved enhanced play-by-play data")
    
    # 2. Player Stats
    print("\n2️⃣  Fetching Player Season Stats...")
    player_stats = stats_fetcher.get_player_season_stats('2024-25')
    if len(player_stats) > 0:
        print(f"   ✅ Got stats for {len(player_stats)} players")
    
    # 3. Team Stats
    print("\n3️⃣  Fetching Team Stats...")
    team_stats = stats_fetcher.get_team_stats('2024-25')
    if len(team_stats) > 0:
        print(f"   ✅ Got stats for {len(team_stats)} teams")
    
    # 4. Injury Reports
    print("\n4️⃣  Scraping Injury Reports...")
    injuries = injury_scraper.scrape_espn_injuries()
    if len(injuries) > 0:
        print(f"   ✅ Scraped {len(injuries)} injury reports")
    
    print("\n" + "="*80)
    print("✅ DATA FETCH COMPLETE!")
    print("="*80)
    print("\n💡 Next steps:")
    print("   1. Integrate this data into your ensemble features")
    print("   2. Add injury status as a binary feature")
    print("   3. Use player momentum/form for live predictions")
    print("   4. Schedule this script to run daily (cron job)")

if __name__ == "__main__":
    main()
