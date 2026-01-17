#!/usr/bin/env python3
"""
🎥 YouTube Highlights Downloader for Vision CNN Case Study

Downloads NBA game highlights from YouTube for the 2024-2026 seasons
to run through the Vision CNN for the "Real Video" validation.

Usage:
    poetry run python scripts/download_highlights.py --season 2025-26 --num-games 100

Dependencies:
    pip install yt-dlp
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
VIDEO_DIR = Path("data/video_highlights")
METADATA_DIR = Path("data/video_metadata")
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)

# NBA Team YouTube-friendly names
TEAM_NAMES = {
    "Lakers": "Los Angeles Lakers",
    "Celtics": "Boston Celtics",
    "Warriors": "Golden State Warriors",
    "Nuggets": "Denver Nuggets",
    "Bucks": "Milwaukee Bucks",
    "76ers": "Philadelphia 76ers",
    "Heat": "Miami Heat",
    "Suns": "Phoenix Suns",
    "Cavaliers": "Cleveland Cavaliers",
    "Mavericks": "Dallas Mavericks",
    "Clippers": "LA Clippers",
    "Kings": "Sacramento Kings",
    "Timberwolves": "Minnesota Timberwolves",
    "Thunder": "Oklahoma City Thunder",
    "Pelicans": "New Orleans Pelicans",
    "Knicks": "New York Knicks",
    "Nets": "Brooklyn Nets",
    "Hawks": "Atlanta Hawks",
    "Bulls": "Chicago Bulls",
    "Raptors": "Toronto Raptors",
    "Pacers": "Indiana Pacers",
    "Magic": "Orlando Magic",
    "Hornets": "Charlotte Hornets",
    "Wizards": "Washington Wizards",
    "Pistons": "Detroit Pistons",
    "Grizzlies": "Memphis Grizzlies",
    "Spurs": "San Antonio Spurs",
    "Trail Blazers": "Portland Trail Blazers",
    "Jazz": "Utah Jazz",
    "Rockets": "Houston Rockets",
}


def get_recent_games(season: str = "2025-26", num_games: int = 100) -> pd.DataFrame:
    """Get the most recent games from the dataset for case study."""
    df = pd.read_csv("data/nba_games_enhanced.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter to requested season
    if season == "2025-26":
        start_date = "2025-10-01"
        end_date = "2026-06-30"
    elif season == "2024-25":
        start_date = "2024-10-01"
        end_date = "2025-06-30"
    else:
        raise ValueError(f"Unknown season: {season}")
    
    filtered = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    
    # Sort by date descending and take num_games
    recent = filtered.sort_values('date', ascending=False).head(num_games)
    
    logger.info(f"Found {len(recent)} games for {season} season")
    return recent


def search_youtube_highlight(home: str, away: str, date: str) -> str:
    """Generate YouTube search query for a game."""
    home_full = TEAM_NAMES.get(home, home)
    away_full = TEAM_NAMES.get(away, away)
    
    # Format: "Lakers vs Celtics Full Game Highlights January 15 2026"
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    date_str = date_obj.strftime("%B %d %Y")
    
    query = f"{away_full} vs {home_full} Full Game Highlights {date_str}"
    return query


def download_video(query: str, output_path: Path, max_duration: int = 600) -> bool:
    """
    Download a YouTube video using yt-dlp.
    
    Args:
        query: YouTube search query
        output_path: Path to save video
        max_duration: Max video duration in seconds (default 10 min)
    
    Returns:
        True if download successful
    """
    if output_path.exists():
        logger.info(f"Video already exists: {output_path.name}")
        return True
    
    try:
        cmd = [
            "yt-dlp",
            f"ytsearch1:{query}",  # Search and take first result
            "-o", str(output_path),
            "-f", "best[height<=720]",  # Max 720p to save space
            "--max-filesize", "200M",  # Max 200MB
            "--match-filter", f"duration <= {max_duration}",
            "--no-playlist",
            "--quiet",
            "--no-warnings",
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0 and output_path.exists():
            logger.info(f"✅ Downloaded: {output_path.name}")
            return True
        else:
            logger.warning(f"❌ Failed: {query}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.warning(f"⏰ Timeout: {query}")
        return False
    except Exception as e:
        logger.error(f"Error downloading {query}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download NBA highlights for Vision CNN")
    parser.add_argument("--season", default="2025-26", choices=["2024-25", "2025-26"])
    parser.add_argument("--num-games", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true", help="Just list games, don't download")
    args = parser.parse_args()
    
    print("=" * 70)
    print("🎥 NBA HIGHLIGHTS DOWNLOADER FOR VISION CNN CASE STUDY")
    print("=" * 70)
    
    # Check yt-dlp is installed
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("❌ yt-dlp not found! Install with: pip install yt-dlp")
        sys.exit(1)
    
    # Get games
    games = get_recent_games(args.season, args.num_games)
    print(f"\n📅 Processing {len(games)} games from {args.season} season")
    
    if args.dry_run:
        print("\n🔍 DRY RUN - Would download these games:")
        for _, row in games.head(10).iterrows():
            query = search_youtube_highlight(row['home'], row['away'], 
                                              row['date'].strftime('%Y-%m-%d'))
            print(f"   {query}")
        print(f"   ... and {len(games) - 10} more")
        return
    
    # Download each game
    success = 0
    failed = 0
    metadata = []
    
    for idx, row in games.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        query = search_youtube_highlight(row['home'], row['away'], date_str)
        
        # Create filename
        filename = f"{date_str}_{row['away']}_at_{row['home']}.mp4"
        output_path = VIDEO_DIR / filename
        
        print(f"\n[{success + failed + 1}/{len(games)}] {row['away']} @ {row['home']} ({date_str})")
        
        if download_video(query, output_path):
            success += 1
            metadata.append({
                "game_id": row.get('game_id', f"{date_str}_{row['home']}_{row['away']}"),
                "date": date_str,
                "home": row['home'],
                "away": row['away'],
                "home_pts": row['home_pts'],
                "away_pts": row['away_pts'],
                "home_win": row['home_win'],
                "video_path": str(output_path),
                "download_time": datetime.now().isoformat(),
            })
        else:
            failed += 1
    
    # Save metadata
    metadata_file = METADATA_DIR / f"downloads_{args.season}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 70)
    print(f"✅ Downloaded: {success} videos")
    print(f"❌ Failed: {failed} videos")
    print(f"📁 Videos saved to: {VIDEO_DIR}")
    print(f"📋 Metadata saved to: {metadata_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
