
import logging
from typing import Optional, Dict
from nba_api.stats.static import players, teams

logger = logging.getLogger(__name__)

# Simple cache for player team ID
_PLAYER_TEAM_CACHE: Dict[str, int] = {}

# Simple cache for team name -> ID
_TEAM_NAME_CACHE: Dict[str, int] = {}

def get_team_id_by_name(team_name: str) -> Optional[int]:
    """Get team ID from team name using static cache."""
    if not _TEAM_NAME_CACHE:
        all_teams = teams.get_teams()
        for team in all_teams:
            _TEAM_NAME_CACHE[team['full_name']] = team['id']
            _TEAM_NAME_CACHE[team['nickname']] = team['id']
            _TEAM_NAME_CACHE[team['abbreviation']] = team['id']
            _TEAM_NAME_CACHE[team['city']] = team['id']

    return _TEAM_NAME_CACHE.get(team_name)

def get_player_team_id(player_name: str, home_team_name: Optional[str] = None, away_team_name: Optional[str] = None) -> Optional[int]:
    """
    Get the team ID for a player.

    Args:
        player_name: Full name of the player.
        home_team_name: Name of the home team in the current game (hint).
        away_team_name: Name of the away team in the current game (hint).

    Returns:
        Team ID if found, else None.
    """
    if player_name in _PLAYER_TEAM_CACHE:
        return _PLAYER_TEAM_CACHE[player_name]

    try:
        # 1. Try to find player by name
        found_players = players.find_players_by_full_name(player_name)
        if not found_players:
            logger.warning(f"Player {player_name} not found in static list.")
            return None

        # There might be multiple players with same name, or inactive ones.
        # We prefer active players.
        active_players = [p for p in found_players if p.get('is_active')]
        if not active_players:
            # If no active player found, maybe the static list is outdated, stick with found_players
            player_matches = found_players
        else:
            player_matches = active_players

        player_id = player_matches[0]['id']

        # 2. Get player info to find team ID
        # We can use commonplayerinfo endpoint
        from nba_api.stats.endpoints import commonplayerinfo

        # Add rate limiting or catching here if needed
        # But for now let's assume low volume or cache hits
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        data = info.get_dict()

        if 'resultSets' in data and len(data['resultSets']) > 0:
            headers = data['resultSets'][0]['headers']
            row = data['resultSets'][0]['rowSet'][0]
            player_data = dict(zip(headers, row))

            team_id = player_data.get('TEAM_ID')
            if team_id:
                _PLAYER_TEAM_CACHE[player_name] = team_id
                return team_id

    except Exception as e:
        logger.warning(f"Error fetching team for player {player_name}: {e}")
        return None

    return None
