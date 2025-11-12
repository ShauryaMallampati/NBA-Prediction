"""
NBA Schedule and Live Data Scraper using nba_api
Fetches current season schedule, today's games, and live scores.
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import leaguegamefinder, scoreboardv2
from nba_api.stats.static import teams

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.common.paths import Paths


class NBAScheduleScraper:
    """Scrape NBA schedule and live data from nba_api"""
    
    def __init__(self, season: str = "2024-25"):
        """
        Initialize scraper
        
        Args:
            season: NBA season in format "2024-25"
        """
        self.season = season
        self.all_teams = teams.get_teams()
        self.team_mapping = {team['id']: team for team in self.all_teams}
        
        # Ensure data directories exist
        self.schedule_dir = Paths.DATA / "schedules"
        self.schedule_dir.mkdir(parents=True, exist_ok=True)
        
        self.live_dir = Paths.DATA / "live"
        self.live_dir.mkdir(parents=True, exist_ok=True)
        
    def get_today_games(self) -> dict:
        """
        Get today's games from Live NBA endpoint
        
        Returns:
            Dictionary with today's scoreboard data
        """
        print("Fetching today's games from NBA Live API...")
        try:
            games_today = scoreboard.ScoreBoard()
            games_dict = games_today.get_dict()
            
            # Save raw response
            today_str = datetime.now().strftime("%Y-%m-%d")
            output_file = self.live_dir / f"scoreboard_{today_str}.json"
            with open(output_file, 'w') as f:
                json.dump(games_dict, f, indent=2)
            
            print(f"✅ Saved today's scoreboard to {output_file}")
            
            # Parse and display game info
            games = games_dict.get('scoreboard', {}).get('games', [])
            print(f"\n📊 Found {len(games)} games today ({today_str}):")
            
            for game in games:
                home_team = game.get('homeTeam', {}).get('teamTricode', 'UNK')
                away_team = game.get('awayTeam', {}).get('teamTricode', 'UNK')
                game_status = game.get('gameStatusText', 'Unknown')
                
                home_score = game.get('homeTeam', {}).get('score', 0)
                away_score = game.get('awayTeam', {}).get('score', 0)
                
                print(f"  {away_team} @ {home_team} - {game_status}")
                if home_score > 0 or away_score > 0:
                    print(f"    Score: {away_team} {away_score} - {home_score} {home_team}")
            
            return games_dict
            
        except Exception as e:
            print(f"❌ Error fetching today's games: {e}")
            return {}
    
    def get_full_season_schedule(self, save_to_db: bool = True) -> pd.DataFrame:
        """
        Get full season schedule for current season
        
        Args:
            save_to_db: Whether to save to CSV
            
        Returns:
            DataFrame with season schedule
        """
        print(f"\nFetching full season schedule for {self.season}...")
        
        all_games = []
        
        try:
            # Use LeagueGameFinder to get all games for the season
            # Season format: "2024-25" -> need just "2024" for API
            season_year = self.season.split('-')[0]
            
            gamefinder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season_year,
                season_type_nullable='Regular Season',
                league_id_nullable='00'
            )
            
            games_df = gamefinder.get_data_frames()[0]
            
            print(f"✅ Retrieved {len(games_df)} game records (includes both teams per game)")
            
            # Process and deduplicate (each game appears twice, once for each team)
            games_df['GAME_DATE'] = pd.to_datetime(games_df['GAME_DATE'])
            
            # Group by game_id to get unique games
            unique_games = games_df.groupby('GAME_ID').first().reset_index()
            
            print(f"✅ Processed {len(unique_games)} unique games")
            
            # Save to CSV
            if save_to_db:
                output_file = self.schedule_dir / f"schedule_{self.season}.csv"
                unique_games.to_csv(output_file, index=False)
                print(f"✅ Saved schedule to {output_file}")
            
            return unique_games
            
        except Exception as e:
            print(f"❌ Error fetching season schedule: {e}")
            return pd.DataFrame()
    
    def get_upcoming_games(self, days_ahead: int = 7) -> pd.DataFrame:
        """
        Get games for next N days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            DataFrame with upcoming games
        """
        print(f"\nFetching games for next {days_ahead} days...")
        
        today = datetime.now().date()
        upcoming_games = []
        
        try:
            for day_offset in range(days_ahead + 1):
                target_date = today + timedelta(days=day_offset)
                date_str = target_date.strftime("%Y-%m-%d")
                
                # Use ScoreboardV2 for specific date
                scoreboard_data = scoreboardv2.ScoreboardV2(
                    game_date=target_date.strftime("%m/%d/%Y")
                )
                
                games_df = scoreboard_data.get_data_frames()[0]
                
                if not games_df.empty:
                    games_df['SCRAPE_DATE'] = date_str
                    upcoming_games.append(games_df)
                    print(f"  {date_str}: {len(games_df)} games")
                else:
                    print(f"  {date_str}: No games")
            
            if upcoming_games:
                all_upcoming = pd.concat(upcoming_games, ignore_index=True)
                
                # Save to CSV
                output_file = self.schedule_dir / f"upcoming_games_{today.strftime('%Y%m%d')}.csv"
                all_upcoming.to_csv(output_file, index=False)
                print(f"\n✅ Saved {len(all_upcoming)} upcoming games to {output_file}")
                
                return all_upcoming
            else:
                print("⚠️  No upcoming games found")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error fetching upcoming games: {e}")
            return pd.DataFrame()
    
    def get_team_schedule(self, team_abbr: str) -> pd.DataFrame:
        """
        Get schedule for a specific team
        
        Args:
            team_abbr: Team abbreviation (e.g., 'LAL')
            
        Returns:
            DataFrame with team's schedule
        """
        print(f"\nFetching schedule for {team_abbr}...")
        
        # Find team ID
        team_info = None
        for team in self.all_teams:
            if team['abbreviation'] == team_abbr:
                team_info = team
                break
        
        if not team_info:
            print(f"❌ Team {team_abbr} not found")
            return pd.DataFrame()
        
        try:
            season_year = self.season.split('-')[0]
            
            gamefinder = leaguegamefinder.LeagueGameFinder(
                team_id_nullable=team_info['id'],
                season_nullable=season_year,
                season_type_nullable='Regular Season'
            )
            
            team_schedule = gamefinder.get_data_frames()[0]
            
            print(f"✅ Retrieved {len(team_schedule)} games for {team_info['full_name']}")
            
            # Save to CSV
            output_file = self.schedule_dir / f"team_{team_abbr}_{self.season}.csv"
            team_schedule.to_csv(output_file, index=False)
            print(f"✅ Saved to {output_file}")
            
            return team_schedule
            
        except Exception as e:
            print(f"❌ Error fetching team schedule: {e}")
            return pd.DataFrame()
    
    def scrape_all(self):
        """Run all scrapers"""
        print("=" * 80)
        print("NBA SCHEDULE SCRAPER - FULL RUN")
        print("=" * 80)
        
        # 1. Get today's games
        today_data = self.get_today_games()
        
        # 2. Get upcoming week
        upcoming_df = self.get_upcoming_games(days_ahead=7)
        
        # 3. Get full season schedule
        season_df = self.get_full_season_schedule()
        
        print("\n" + "=" * 80)
        print("SCRAPING COMPLETE!")
        print("=" * 80)
        print(f"✅ Today's games: {len(today_data.get('scoreboard', {}).get('games', []))} games")
        print(f"✅ Upcoming games (7 days): {len(upcoming_df)} games")
        print(f"✅ Full season schedule: {len(season_df)} games")
        
        return {
            'today': today_data,
            'upcoming': upcoming_df,
            'season': season_df
        }


def main():
    """Main execution"""
    scraper = NBAScheduleScraper(season="2024-25")
    
    # Run all scrapers
    results = scraper.scrape_all()
    
    # Optional: Get schedule for specific teams
    print("\n" + "=" * 80)
    print("FETCHING SELECT TEAM SCHEDULES")
    print("=" * 80)
    
    popular_teams = ['LAL', 'GSW', 'BOS', 'MIA']
    for team_abbr in popular_teams:
        scraper.get_team_schedule(team_abbr)
    
    print("\n✅ ALL DONE! Check data/schedules/ and data/live/ directories")


if __name__ == "__main__":
    main()
