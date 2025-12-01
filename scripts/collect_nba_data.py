"""
NBA Data Collection Script
Fetches data from all RapidAPI endpoints and stores for model training
"""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

from src.services.api.rapid_api_client import rapid_api_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NBADataCollector:
    """Collects and stores NBA data from all available API endpoints"""
    
    def __init__(self, output_dir: str = "data/raw/rapid_api"):
        """Initialize data collector"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = rapid_api_client
        
    def save_data(self, data: Dict[str, Any], filename: str):
        """Save data to JSON file"""
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved data to {filepath}")
    
    def collect_daily_snapshot(self, date: str = None) -> Dict[str, Any]:
        """
        Collect a complete snapshot of all available data for a specific day
        This is the main method for collecting training data
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"=" * 80)
        logger.info(f"Collecting NBA data snapshot for {date}")
        logger.info(f"=" * 80)
        
        snapshot = {
            "collection_date": date,
            "timestamp": datetime.now().isoformat(),
            "data": {}
        }
        
        # 1. League & Teams Information
        logger.info("\n📊 Collecting League & Teams Data...")
        snapshot["data"]["league_info"] = self.client.get_nba_league_info()
        snapshot["data"]["teams"] = self.client.get_nba_teams()
        snapshot["data"]["all_teams"] = self.client.get_all_teams()
        
        # 2. Schedule & Standings
        logger.info("\n📅 Collecting Schedule & Standings...")
        snapshot["data"]["schedule"] = self.client.get_nba_schedule()
        snapshot["data"]["standings"] = self.client.get_nba_standings()
        snapshot["data"]["scoreboard"] = self.client.get_nba_scoreboard(date)
        
        # 3. Players & Statistics
        logger.info("\n👥 Collecting Player Data...")
        snapshot["data"]["players"] = self.client.get_nba_players()
        snapshot["data"]["all_players"] = self.client.get_all_players(per_page=100)
        snapshot["data"]["statistics"] = self.client.get_nba_statistics()
        snapshot["data"]["daily_leaders"] = self.client.get_daily_leaders(date)
        
        # 4. Games & Scores
        logger.info("\n🏀 Collecting Games & Scores...")
        snapshot["data"]["games"] = self.client.get_all_games(per_page=100)
        snapshot["data"]["scores"] = self.client.get_nba_scores()
        snapshot["data"]["games_info"] = self.client.get_games_info(date=date)
        
        # 5. Injury Reports
        logger.info("\n🏥 Collecting Injury Data...")
        snapshot["data"]["injury_reports"] = self.client.get_injury_reports(date)
        
        # 6. Betting Odds & Props
        logger.info("\n💰 Collecting Betting Data...")
        snapshot["data"]["live_odds"] = self.client.get_nba_odds()
        snapshot["data"]["nba_futures"] = self.client.get_nba_futures()
        snapshot["data"]["events_today"] = self.client.get_events_for_today()
        snapshot["data"]["all_markets"] = self.client.get_all_markets()
        snapshot["data"]["all_bookies"] = self.client.get_all_bookies()
        
        # 7. News & Media
        logger.info("\n📰 Collecting News Data...")
        snapshot["data"]["latest_news"] = self.client.get_latest_news(limit=50)
        snapshot["data"]["espn_news"] = self.client.get_latest_news(source="espn", limit=20)
        snapshot["data"]["bleacher_news"] = self.client.get_latest_news(source="bleacher-report", limit=20)
        
        # 8. Fantasy Sports Data
        logger.info("\n🎮 Collecting Fantasy Data...")
        fantasy_positions = ["G", "F", "C"]
        snapshot["data"]["fantasy_ros"] = {}
        snapshot["data"]["fantasy_week"] = {}
        for pos in fantasy_positions:
            snapshot["data"]["fantasy_ros"][pos] = self.client.get_nba_fantasy_rest_of_season(pos)
            snapshot["data"]["fantasy_week"][pos] = self.client.get_nba_fantasy_current_week(pos)
        
        # Save snapshot
        filename = f"nba_snapshot_{date}.json"
        self.save_data(snapshot, filename)
        
        return snapshot
    
    def collect_historical_data(
        self,
        start_date: str,
        end_date: str,
        save_interval: int = 1
    ):
        """
        Collect historical data over a date range
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            save_interval: Days between collection (1 = daily)
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current = start
        
        collected_dates = []
        
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            try:
                self.collect_daily_snapshot(date_str)
                collected_dates.append(date_str)
            except Exception as e:
                logger.error(f"Failed to collect data for {date_str}: {e}")
            
            current += timedelta(days=save_interval)
        
        # Create summary
        summary = {
            "collection_period": {
                "start": start_date,
                "end": end_date
            },
            "dates_collected": collected_dates,
            "total_days": len(collected_dates)
        }
        
        self.save_data(summary, "historical_collection_summary.json")
        logger.info(f"\n✅ Historical collection complete: {len(collected_dates)} days collected")
    
    def collect_season_data(self, season: str = "2024"):
        """
        Collect comprehensive season data
        
        Args:
            season: Season year (e.g., "2024" for 2024-2025 season)
        """
        logger.info(f"Collecting season data for {season}-{int(season)+1}")
        
        season_data = {
            "season": season,
            "collection_timestamp": datetime.now().isoformat(),
            "data": {}
        }
        
        # Season-specific endpoints
        logger.info("\n📊 Collecting Season Statistics...")
        season_data["data"]["schedule"] = self.client.get_nba_schedule(season)
        season_data["data"]["standings"] = self.client.get_nba_standings(season)
        season_data["data"]["statistics"] = self.client.get_nba_statistics(season)
        
        # Get all games for the season
        logger.info("\n🏀 Collecting Season Games...")
        season_data["data"]["games"] = self.client.get_all_games(
            seasons=[int(season)],
            per_page=100
        )
        
        # Get player stats for the season
        logger.info("\n👥 Collecting Season Player Stats...")
        season_data["data"]["player_stats"] = self.client.get_all_stats(
            seasons=[int(season)],
            per_page=100
        )
        
        filename = f"nba_season_{season}_{int(season)+1}.json"
        self.save_data(season_data, filename)
        
        return season_data
    
    def collect_team_specific_data(self, team_name: str):
        """
        Collect all available data for a specific team
        
        Args:
            team_name: Team name (e.g., "lakers", "warriors")
        """
        logger.info(f"Collecting data for {team_name}")
        
        team_data = {
            "team": team_name,
            "collection_timestamp": datetime.now().isoformat(),
            "data": {}
        }
        
        # Team-specific endpoints
        team_data["data"]["schedule"] = self.client.get_schedule_data(team=team_name)
        team_data["data"]["games_list"] = self.client.get_games_list(season="2024", team=team_name)
        team_data["data"]["news"] = self.client.get_latest_news(team=team_name, limit=50)
        
        filename = f"nba_team_{team_name}.json"
        self.save_data(team_data, filename)
        
        return team_data
    
    def collect_player_specific_data(self, player_name: str):
        """
        Collect all available data for a specific player
        
        Args:
            player_name: Player name (e.g., "lebron-james")
        """
        logger.info(f"Collecting data for {player_name}")
        
        player_data = {
            "player": player_name,
            "collection_timestamp": datetime.now().isoformat(),
            "data": {}
        }
        
        # Player-specific endpoints
        player_data["data"]["search"] = self.client.get_all_players(search=player_name)
        player_data["data"]["news"] = self.client.get_latest_news(player=player_name, limit=50)
        
        filename = f"nba_player_{player_name.replace(' ', '_')}.json"
        self.save_data(player_data, filename)
        
        return player_data
    
    def collect_betting_training_data(self):
        """
        Collect comprehensive betting data for model training
        Includes backtesting data and historical odds
        """
        logger.info("Collecting betting training data")
        
        betting_data = {
            "collection_timestamp": datetime.now().isoformat(),
            "data": {}
        }
        
        # Backtesting data
        logger.info("\n🎲 Collecting Backtesting Data...")
        betting_data["data"]["sim_day"] = self.client.get_sim_day()
        betting_data["data"]["sim_week"] = self.client.get_sim_week()
        betting_data["data"]["sim_month"] = self.client.get_sim_month()
        betting_data["data"]["random_set"] = self.client.get_random_set(size=200)
        
        # Current odds
        logger.info("\n💰 Collecting Current Odds...")
        betting_data["data"]["live_odds"] = self.client.get_nba_odds()
        betting_data["data"]["game_odds"] = self.client.get_nba_game_odds()
        betting_data["data"]["futures"] = self.client.get_nba_futures()
        
        # Player props
        logger.info("\n🎯 Collecting Player Props...")
        events = self.client.get_events_for_today()
        if events and "events" in events:
            betting_data["data"]["player_props"] = []
            for event in events["events"][:5]:  # Limit to first 5 events
                event_id = event.get("id")
                if event_id:
                    props = self.client.get_player_odds_for_event(event_id)
                    betting_data["data"]["player_props"].append({
                        "event_id": event_id,
                        "props": props
                    })
        
        filename = "nba_betting_training_data.json"
        self.save_data(betting_data, filename)
        
        return betting_data
    
    def create_training_dataset(
        self,
        output_file: str = "data/processed/nba_training_dataset.json"
    ):
        """
        Create a consolidated training dataset from all collected data
        """
        logger.info("Creating consolidated training dataset")
        
        # List all collected data files
        data_files = list(self.output_dir.glob("*.json"))
        
        consolidated = {
            "created_at": datetime.now().isoformat(),
            "num_files": len(data_files),
            "files": [str(f.name) for f in data_files],
            "datasets": []
        }
        
        # Load and consolidate all data
        for file in data_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    consolidated["datasets"].append({
                        "filename": file.name,
                        "data": data
                    })
            except Exception as e:
                logger.error(f"Error loading {file}: {e}")
        
        # Save consolidated dataset
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(consolidated, f, indent=2)
        
        logger.info(f"✅ Training dataset created: {output_path}")
        logger.info(f"   - Total files: {len(data_files)}")
        logger.info(f"   - File size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        return consolidated


def main():
    """Main data collection workflow"""
    collector = NBADataCollector()
    
    print("\n" + "=" * 80)
    print("NBA DATA COLLECTION MENU")
    print("=" * 80)
    print("\n1. Collect Today's Data Snapshot")
    print("2. Collect Historical Data Range")
    print("3. Collect Season Data")
    print("4. Collect Team-Specific Data")
    print("5. Collect Player-Specific Data")
    print("6. Collect Betting Training Data")
    print("7. Collect ALL Data (Comprehensive)")
    print("8. Create Training Dataset from Collected Data")
    print("9. Exit")
    
    choice = input("\nEnter your choice (1-9): ")
    
    if choice == "1":
        date = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
        collector.collect_daily_snapshot(date if date else None)
    
    elif choice == "2":
        start = input("Start date (YYYY-MM-DD): ").strip()
        end = input("End date (YYYY-MM-DD): ").strip()
        interval = int(input("Collection interval in days (default 1): ").strip() or "1")
        collector.collect_historical_data(start, end, interval)
    
    elif choice == "3":
        season = input("Season year (default 2024): ").strip() or "2024"
        collector.collect_season_data(season)
    
    elif choice == "4":
        team = input("Team name (e.g., 'lakers'): ").strip()
        collector.collect_team_specific_data(team)
    
    elif choice == "5":
        player = input("Player name (e.g., 'lebron-james'): ").strip()
        collector.collect_player_specific_data(player)
    
    elif choice == "6":
        collector.collect_betting_training_data()
    
    elif choice == "7":
        print("\n🚀 Starting comprehensive data collection...")
        date = datetime.now().strftime("%Y-%m-%d")
        
        # Collect today's snapshot
        collector.collect_daily_snapshot(date)
        
        # Collect current season
        collector.collect_season_data("2024")
        
        # Collect betting data
        collector.collect_betting_training_data()
        
        # Create consolidated dataset
        collector.create_training_dataset()
        
        print("\n✅ Comprehensive data collection complete!")
    
    elif choice == "8":
        collector.create_training_dataset()
    
    elif choice == "9":
        print("Exiting...")
    
    else:
        print("Invalid choice!")


if __name__ == "__main__":
    main()
