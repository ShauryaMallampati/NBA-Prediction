"""
Service for calculating travel fatigue for players.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

from src.data.ingest.game_fetcher import get_game_fetcher
from src.data.ingest.player_fetcher import get_player_fetcher
from src.data.ingest.travel_ors import TravelFatigueCalculator, NBA_ARENAS

logger = logging.getLogger(__name__)

class TravelFatigueService:
    def __init__(self):
        self.game_fetcher = get_game_fetcher()
        self.player_fetcher = get_player_fetcher()
        self.calculator = TravelFatigueCalculator()

    def get_travel_fatigue(self, player_name: str, game_date: str) -> float:
        """
        Calculate travel fatigue score for a player on a given date.

        Args:
            player_name: Name of the player (e.g., "LeBron James")
            game_date: Date string (YYYY-MM-DD)

        Returns:
            Fatigue score (0-100)
        """
        try:
            # 1. Get Player Info to find Team
            players = self.player_fetcher.search_players(player_name)
            if not players:
                logger.warning(f"Player {player_name} not found.")
                return 0.0

            player_id = players[0]['id']

            # Get player stats to find current team
            # We fetch recent stats to determine the team.
            # Ideally we would have a 'get_player_team' method but checking recent stats is a good proxy.
            stats = self.player_fetcher.get_player_stats(player_id, last_n_games=1)

            if not stats:
                 # Fallback: Try to find team from roster? Or just return 0.0
                 logger.warning(f"No stats found for {player_name} to determine team.")
                 return 0.0

            team_name = stats[0].get('TEAM_NAME') # e.g., "Los Angeles Lakers"
            team_id = stats[0].get('TEAM_ID')

            if not team_name:
                logger.warning(f"Could not determine team for {player_name}")
                return 0.0

            # 2. Get Schedule for the Team
            # We need past few games and upcoming game to determine travel
            # Let's fetch games for the team in a range around the game_date

            date_obj = datetime.strptime(game_date, "%Y-%m-%d")
            start_date = (date_obj - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = (date_obj + timedelta(days=1)).strftime("%Y-%m-%d") # include today/tomorrow for B2B check

            all_games = self.game_fetcher.get_games_date_range(start_date, end_date)

            # Filter for team's games
            team_schedule = []
            current_arena = None

            for game in all_games:
                home_id = game.get('home_team', {}).get('id')
                visitor_id = game.get('visitor_team', {}).get('id')

                if home_id == team_id or visitor_id == team_id:
                    # Determine arena
                    # We assume arena is Home Team Name
                    home_team_name = game.get('home_team', {}).get('name')

                    # If name is None (some API responses), we might need to map ID to name
                    # But for now let's hope it's there or we can use team_name if it matches

                    # Correction: API returns None for name sometimes in scoreboardv2 for some reason?
                    # Let's check the earlier test output.
                    # Sample game: 'home_team': {'id': 1610612754, 'name': None, ...}
                    # That is bad. We need to map ID to Name.

                    arena = self._resolve_arena_name(home_id, home_team_name)

                    game_entry = {
                        "date": game.get('date'),
                        "arena": arena,
                        "game_id": game.get('game_id')
                    }
                    team_schedule.append(game_entry)

                    if game.get('date') == game_date:
                        current_arena = arena

            if not current_arena:
                logger.warning(f"No game found for {team_name} on {game_date}")
                # If they are not playing today, fatigue is not relevant for a game context?
                # But maybe this is called for a potential bet.
                return 0.0

            # 3. Get Minutes Yesterday
            minutes_yesterday = 0.0
            yesterday_date = (date_obj - timedelta(days=1)).strftime("%Y-%m-%d")

            # Check if they played yesterday
            played_yesterday = False
            for game in team_schedule:
                if game['date'] == yesterday_date:
                    played_yesterday = True
                    break

            if played_yesterday:
                 # Fetch stats for yesterday
                 # We already fetched recent stats, let's see if we can find yesterday's game
                 # We can use get_player_stats with specific date if needed, or filter the list
                 # But get_player_stats doesn't take date list directly in the simple wrapper
                 # Let's just fetch last 5 games again and look for date
                 recent_stats = self.player_fetcher.get_player_stats(player_id, last_n_games=5)
                 for stat in recent_stats:
                     # stat['GAME_DATE'] format? NBA API usually returns it.
                     # In test output: 'GAME_DATE': '2026-01-13T00:00:00'
                     stat_date = stat.get('GAME_DATE')
                     if stat_date and stat_date.startswith(yesterday_date):
                         minutes_yesterday = stat.get('MIN', 0.0)
                         break

            # 4. Calculate Fatigue
            fatigue_data = self.calculator.extract_travel_fatigue(
                team=team_name,
                current_date=game_date,
                current_arena=current_arena,
                schedule=team_schedule,
                minutes_yesterday=minutes_yesterday
            )

            return fatigue_data.get('fatigue_score', 0.0)

        except Exception as e:
            logger.error(f"Error calculating travel fatigue for {player_name}: {e}")
            return 0.0

    def _resolve_arena_name(self, team_id: int, team_name: Optional[str]) -> str:
        """
        Resolve team ID/Name to an Arena Name (which is mapped to Team Name in NBA_ARENAS).
        """
        # If we have a valid name that is in NBA_ARENAS, use it.
        # NBA_ARENAS keys are full team names like "Boston Celtics"

        if team_name and team_name in NBA_ARENAS:
            return team_name

        # If not, we might need a mapping from ID to Name
        # We can use static_teams from nba_api
        try:
             from nba_api.stats.static import teams
             team_info = teams.find_team_name_by_id(team_id)
             if team_info:
                 full_name = team_info['full_name']
                 if full_name in NBA_ARENAS:
                     return full_name
        except:
            pass

        return "Unknown"

# Singleton
_travel_service: Optional[TravelFatigueService] = None

def get_travel_service() -> TravelFatigueService:
    global _travel_service
    if _travel_service is None:
        _travel_service = TravelFatigueService()
    return _travel_service
