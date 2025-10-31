#!/usr/bin/env python3
"""
Historical NBA Data Downloader
Downloads game data, player stats, and team records from 2020-2024 seasons
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from data.ingest.nba_api_client import NBAAPIClient
from data.ingest.game_fetcher import GameFetcher
from data.ingest.player_fetcher import PlayerFetcher


class HistoricalDataDownloader:
    """Downloads and stores historical NBA data"""

    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.game_fetcher = GameFetcher()
        self.player_fetcher = PlayerFetcher()
        self.client = self.game_fetcher.client  # Use the client from game_fetcher
        
        # Seasons to download (2020-21 to 2024-25)
        self.seasons = [
            "2020-21",
            "2021-22",
            "2022-23",
            "2023-24",
            "2024-25"
        ]
    
    def download_season_games(self, season: str) -> List[Dict[str, Any]]:
        """
        Download all games for a season
        
        Args:
            season: Season string like "2023-24"
        
        Returns:
            List of game dictionaries
        """
        print(f"\n📅 Downloading games for {season} season...")
        
        # Determine date range for season
        year_start = int(season.split('-')[0])
        year_end = year_start + 1
        
        # NBA season typically runs October to June
        start_date = datetime(year_start, 10, 1)
        end_date = datetime(year_end, 6, 30)
        
        all_games = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            try:
                games = self.game_fetcher.get_games_by_date(date_str)
                
                if games:
                    print(f"  {date_str}: {len(games)} games")
                    all_games.extend(games)
                    time.sleep(0.6)  # Rate limiting
                
            except Exception as e:
                print(f"  ⚠️ Error on {date_str}: {e}")
            
            current_date += timedelta(days=1)
        
        print(f"  ✅ Total games downloaded: {len(all_games)}")
        
        # Save to file
        season_file = self.output_dir / f"games_{season.replace('-', '_')}.json"
        with open(season_file, 'w') as f:
            json.dump({
                'season': season,
                'total_games': len(all_games),
                'downloaded_at': datetime.now().isoformat(),
                'games': all_games
            }, f, indent=2)
        
        print(f"  💾 Saved to {season_file}")
        
        return all_games
    
    def download_all_teams(self) -> List[Dict[str, Any]]:
        """
        Download all NBA teams
        
        Returns:
            List of team dictionaries
        """
        print("\n🏀 Downloading all NBA teams...")
        
        teams = self.client.get_teams()
        print(f"  ✅ Downloaded {len(teams)} teams")
        
        # Save to file
        teams_file = self.output_dir / "teams.json"
        with open(teams_file, 'w') as f:
            json.dump({
                'total_teams': len(teams),
                'downloaded_at': datetime.now().isoformat(),
                'teams': teams
            }, f, indent=2)
        
        print(f"  💾 Saved to {teams_file}")
        
        return teams
    
    def download_player_season_stats(self, season: str, top_n: int = 500) -> List[Dict[str, Any]]:
        """
        Download player season averages for top N players
        
        Args:
            season: Season string like "2023-24"
            top_n: Number of top players to download
        
        Returns:
            List of player stat dictionaries
        """
        print(f"\n👥 Downloading top {top_n} player stats for {season}...")
        
        try:
            # Get all active players
            players = self.client.get_players(active_only=True)
            print(f"  Found {len(players)} active players")
            
            # Get season averages for each player
            player_stats = []
            
            for i, player in enumerate(players[:top_n], 1):
                try:
                    player_id = player.get('id')
                    player_name = player.get('full_name', 'Unknown')
                    
                    print(f"  [{i}/{min(top_n, len(players))}] {player_name}...", end=' ')
                    
                    # Get recent performance (last 10 games as proxy for season avg)
                    stats = self.player_fetcher.get_recent_performance(
                        player_id=player_id,
                        games=10
                    )
                    
                    if stats and stats.get('games_analyzed', 0) > 0:
                        player_stats.append({
                            'player_id': player_id,
                            'player_name': player_name,
                            'team_id': player.get('team_id'),
                            'season': season,
                            **stats
                        })
                        print("✓")
                    else:
                        print("No data")
                    
                    time.sleep(0.6)  # Rate limiting
                    
                except Exception as e:
                    print(f"Error: {e}")
                    continue
            
            print(f"  ✅ Downloaded stats for {len(player_stats)} players")
            
            # Save to file
            stats_file = self.output_dir / f"player_stats_{season.replace('-', '_')}.json"
            with open(stats_file, 'w') as f:
                json.dump({
                    'season': season,
                    'total_players': len(player_stats),
                    'downloaded_at': datetime.now().isoformat(),
                    'player_stats': player_stats
                }, f, indent=2)
            
            print(f"  💾 Saved to {stats_file}")
            
            return player_stats
            
        except Exception as e:
            print(f"  ❌ Error downloading player stats: {e}")
            return []
    
    def download_all_historical_data(self, download_games: bool = True, 
                                     download_players: bool = True,
                                     download_teams: bool = True):
        """
        Download all historical data
        
        Args:
            download_games: Whether to download game data
            download_players: Whether to download player stats
            download_teams: Whether to download team data
        """
        print("=" * 80)
        print("🚀 HISTORICAL NBA DATA DOWNLOADER")
        print("=" * 80)
        
        start_time = time.time()
        
        # Download teams
        if download_teams:
            self.download_all_teams()
        
        # Download data for each season
        for season in self.seasons:
            print(f"\n{'=' * 80}")
            print(f"📊 SEASON: {season}")
            print(f"{'=' * 80}")
            
            if download_games:
                self.download_season_games(season)
            
            if download_players:
                self.download_player_season_stats(season, top_n=300)
        
        elapsed_time = time.time() - start_time
        print(f"\n{'=' * 80}")
        print(f"✅ DOWNLOAD COMPLETE!")
        print(f"⏱️  Total time: {elapsed_time / 60:.1f} minutes")
        print(f"💾 Data saved to: {self.output_dir.absolute()}")
        print(f"{'=' * 80}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download historical NBA data')
    parser.add_argument('--output-dir', default='data/raw',
                       help='Output directory for downloaded data')
    parser.add_argument('--no-games', action='store_true',
                       help='Skip downloading game data')
    parser.add_argument('--no-players', action='store_true',
                       help='Skip downloading player stats')
    parser.add_argument('--no-teams', action='store_true',
                       help='Skip downloading team data')
    parser.add_argument('--season', type=str,
                       help='Download specific season only (e.g., 2023-24)')
    
    args = parser.parse_args()
    
    downloader = HistoricalDataDownloader(output_dir=args.output_dir)
    
    # If specific season requested, override seasons list
    if args.season:
        downloader.seasons = [args.season]
    
    downloader.download_all_historical_data(
        download_games=not args.no_games,
        download_players=not args.no_players,
        download_teams=not args.no_teams
    )


if __name__ == "__main__":
    main()
