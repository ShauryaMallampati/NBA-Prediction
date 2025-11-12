"""
Update NBA schedule in database with current season data
Integrates with existing pregame feature engineering pipeline
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.static import teams

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.common.paths import Paths


def get_team_mapping():
    """Create team mapping from nba_api"""
    all_teams = teams.get_teams()
    mapping = {}
    
    for team in all_teams:
        # Map abbreviation to full name and ID
        mapping[team['abbreviation']] = {
            'id': team['id'],
            'full_name': team['full_name'],
            'city': team['city'],
            'abbreviation': team['abbreviation']
        }
    
    return mapping


def parse_today_games(scoreboard_data: dict, team_mapping: dict) -> pd.DataFrame:
    """
    Parse today's scoreboard data into DataFrame format
    
    Args:
        scoreboard_data: Raw scoreboard JSON
        team_mapping: Team abbreviation to metadata mapping
        
    Returns:
        DataFrame with games in our schema
    """
    games = scoreboard_data.get('scoreboard', {}).get('games', [])
    
    parsed_games = []
    
    for game in games:
        game_id = game['gameId']
        game_date = game['gameEt'][:10]  # Extract date from ISO timestamp
        
        home_team_code = game['homeTeam']['teamTricode']
        away_team_code = game['awayTeam']['teamTricode']
        
        home_team_id = game['homeTeam']['teamId']
        away_team_id = game['awayTeam']['teamId']
        
        game_status = game['gameStatusText']
        game_time_utc = game['gameTimeUTC']
        
        parsed_game = {
            'game_id': game_id,
            'date': game_date,
            'home_team': home_team_code,
            'away_team': away_team_code,
            'home_team_id': home_team_id,
            'away_team_id': away_team_id,
            'game_status': game_status,
            'game_time_utc': game_time_utc,
            'season': '2024-25',
            'scraped_at': datetime.now().isoformat()
        }
        
        # Add scores if game started
        if game['gameStatus'] >= 2:  # In progress or final
            parsed_game['home_score'] = game['homeTeam']['score']
            parsed_game['away_score'] = game['awayTeam']['score']
            parsed_game['home_win'] = 1 if game['homeTeam']['score'] > game['awayTeam']['score'] else 0
            parsed_game['away_win'] = 1 if game['awayTeam']['score'] > game['homeTeam']['score'] else 0
        else:
            parsed_game['home_score'] = None
            parsed_game['away_score'] = None
            parsed_game['home_win'] = None
            parsed_game['away_win'] = None
        
        parsed_games.append(parsed_game)
    
    return pd.DataFrame(parsed_games)


def update_schedule_database():
    """Main function to update schedule database"""
    print("=" * 80)
    print("UPDATING NBA SCHEDULE DATABASE")
    print("=" * 80)
    
    # Get team mapping
    team_mapping = get_team_mapping()
    print(f"✅ Loaded {len(team_mapping)} teams")
    
    # Fetch today's games
    print("\nFetching today's games...")
    try:
        games_today = scoreboard.ScoreBoard()
        scoreboard_data = games_today.get_dict()
        
        # Parse into our format
        games_df = parse_today_games(scoreboard_data, team_mapping)
        
        print(f"✅ Retrieved {len(games_df)} games for today")
        
        # Save to schedules directory
        schedule_dir = Paths.DATA / "schedules"
        schedule_dir.mkdir(parents=True, exist_ok=True)
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        output_file = schedule_dir / f"games_{today_str}.csv"
        games_df.to_csv(output_file, index=False)
        
        print(f"✅ Saved to {output_file}")
        
        # Display games
        print(f"\n📊 TODAY'S GAMES ({today_str}):")
        print("-" * 80)
        for _, game in games_df.iterrows():
            status = game['game_status']
            print(f"  {game['away_team']} @ {game['home_team']:3s} - {status}")
        
        # Load existing schedule if available
        full_schedule_file = schedule_dir / "full_schedule_2024-25.csv"
        
        if full_schedule_file.exists():
            print(f"\n📂 Loading existing schedule from {full_schedule_file}")
            existing_schedule = pd.read_csv(full_schedule_file)
            print(f"   Existing schedule has {len(existing_schedule)} games")
            
            # Merge new games (avoiding duplicates)
            games_df['game_id'] = games_df['game_id'].astype(str)
            existing_schedule['game_id'] = existing_schedule['game_id'].astype(str)
            
            # Remove today's games from existing schedule (to update them)
            existing_schedule = existing_schedule[~existing_schedule['game_id'].isin(games_df['game_id'])]
            
            # Combine
            updated_schedule = pd.concat([existing_schedule, games_df], ignore_index=True)
            updated_schedule = updated_schedule.sort_values('date').reset_index(drop=True)
            
            # Save updated schedule
            updated_schedule.to_csv(full_schedule_file, index=False)
            print(f"✅ Updated full schedule with {len(updated_schedule)} total games")
        else:
            print(f"\n📝 Creating new schedule file")
            games_df.to_csv(full_schedule_file, index=False)
            print(f"✅ Created {full_schedule_file} with {len(games_df)} games")
        
        # Check if we need predictions
        upcoming_games = games_df[games_df['home_score'].isna()]
        
        if len(upcoming_games) > 0:
            print(f"\n🎯 Found {len(upcoming_games)} games without predictions")
            print("   These games can be predicted using the ensemble model!")
            
            # Save games needing predictions
            predictions_needed_file = schedule_dir / f"predictions_needed_{today_str}.csv"
            upcoming_games.to_csv(predictions_needed_file, index=False)
            print(f"✅ Saved to {predictions_needed_file}")
        
        return games_df
        
    except Exception as e:
        print(f"❌ Error updating schedule: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run schedule update"""
    result = update_schedule_database()
    
    if result is not None:
        print("\n" + "=" * 80)
        print("✅ SCHEDULE DATABASE UPDATED SUCCESSFULLY!")
        print("=" * 80)
        print("\nNext steps:")
        print("  1. Run prediction model on games needing predictions")
        print("  2. Update frontend to display today's games")
        print("  3. Set up cron job to run this script daily")
    else:
        print("\n" + "=" * 80)
        print("❌ SCHEDULE UPDATE FAILED")
        print("=" * 80)


if __name__ == "__main__":
    main()
