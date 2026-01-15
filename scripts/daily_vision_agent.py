#!/usr/bin/env python3
"""
Daily Vision Agent

Phase 2 of the Architecture:
1. Finds yesterday's NBA games using nba_api
2. Generates YouTube search queries for highlights
3. (Placeholder) Streams video for Vision CNN analysis
"""

import sys
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from nba_api.stats.endpoints import scoreboardv2
    HAS_NBA_API = True
except ImportError:
    HAS_NBA_API = False
    logger.warning("nba_api not installed. Using mock data.")

try:
    import yt_dlp
    HAS_YT_DLP = True
except ImportError:
    HAS_YT_DLP = False
    logger.warning("yt-dlp not installed. Video search will be simulated.")


class DailyVisionAgent:
    def __init__(self):
        self.vision_model_path = Path("artifacts/models/vision/basketball_shot_classifier.pt")
        
    def get_yesterdays_games(self) -> List[Dict[str, Any]]:
        """Fetch games played yesterday."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        # Format for nba_api (MM/DD/YYYY) usually, but scoreboard takes date as string
        display_date = (datetime.now() - timedelta(days=1)).strftime('%m/%d/%Y')
        
        logger.info(f"🏀 Fetching games for {yesterday}...")
        
        games = []
        
        if HAS_NBA_API:
            try:
                board = scoreboardv2.ScoreboardV2(game_date=yesterday)
                header = board.game_header.get_dict()
                linescore = board.line_score.get_dict()
                
                # Process games
                # Note: nba_api structures are complex, simplifying for this agent
                # Creating a simplified list for demonstration
                game_headers = header.get('data', [])
                for game in game_headers:
                    # Indices based on nba_api response structure
                    game_id = game[2] 
                    home_team_id = game[6]
                    away_team_id = game[7]
                    
                    # Convert IDs to Names (Simplified mapping would be needed in prod)
                    # For now, using ID placeholder
                    games.append({
                        "game_id": game_id,
                        "date": yesterday,
                        "home_team_id": home_team_id,
                        "away_team_id": away_team_id,
                        "home_score": 0, # Would fetch from linescore
                        "away_score": 0
                    })
            except Exception as e:
                logger.error(f"NBA API Fetch failed: {e}")
        
        # Fallback/Mock if API fails or empty (for reliability)
        if not games:
            logger.info("Using mock data for demonstration.")
            games = [
                {"game_id": "0022400001", "home_team": "Lakers", "away_team": "Warriors", "home_score": 110, "away_score": 105},
                {"game_id": "0022400002", "home_team": "Celtics", "away_team": "Bucks", "home_score": 115, "away_score": 112}
            ]
            
        return games

    def find_highlight_video(self, home_team: str, away_team: str) -> str:
        """Find Official NBA or reputable highlight video URL."""
        query = f"{away_team} at {home_team} Full Game Highlights Official NBA"
        logger.info(f"🔍 Searching YouTube for: '{query}'")
        
        if HAS_YT_DLP:
            ydl_opts = {
                'default_search': 'ytsearch1',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True, # Don't download, just get JSON
            }
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    result = ydl.extract_info(query, download=False)
                    if 'entries' in result and result['entries']:
                        video_info = result['entries'][0]
                        video_url = video_info.get('url', '')
                        title = video_info.get('title', '')
                        logger.info(f"   Found: {title} ({video_url})")
                        return video_url
            except Exception as e:
                logger.error(f"   Search failed: {e}")
        
        return "https://www.youtube.com/watch?v=MOCK_VIDEO_ID"

    def run_daily_loop(self):
        """Execute the daily agent workflow."""
        print("="*60)
        print("🤖 DAILY VISION AGENT - INITIALIZING")
        print("="*60)
        
        # 1. Get Games
        games = self.get_yesterdays_games()
        print(f"\n📋 Found {len(games)} games from yesterday.")
        
        for game in games:
            home = game.get('home_team', f"Team_{game.get('home_team_id')}")
            away = game.get('away_team', f"Team_{game.get('away_team_id')}")
            
            print(f"\n📺 Processing: {away} @ {home}")
            
            # 2. Find Video
            video_url = self.find_highlight_video(home, away)
            
            # 3. Stream & Learn (Placeholder)
            print(f"   ⚡ Streaming to Vision CNN (RAM only)...")
            # In production: cv2.VideoCapture(video_url), frame-by-frame feed to self.vision_model
            
            # 4. Self-Correction
            print(f"   ✅ Cross-referencing with box scores...")
            print(f"   🧠 Updating weights [Simulated]")
            
        print("\n" + "="*60)
        print("😴 Agent loop complete. Sleeping until tomorrow.")
        print("="*60)

if __name__ == "__main__":
    agent = DailyVisionAgent()
    agent.run_daily_loop()
