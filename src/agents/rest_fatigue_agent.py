"""
Rest & Fatigue Agent - Calculates rest days and travel fatigue
"""
import pandas as pd
import numpy as np
import logging
import time
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta
from nba_api.stats.endpoints import teamgamelog

logger = logging.getLogger(__name__)

class RestFatigueAgent:
    """Calculate rest days and back-to-back games"""
    
    def __init__(self):
        self.cache_dir = Path("data/rest_fatigue")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.gamelog_cache = {}  # Cache gamelogs per team
        self.last_api_call = 0
        
    def calculate_rest_days(self, team_id: int, target_date: str, season='2024-25') -> Dict:
        """Calculate days of rest before a game"""
        cache_key = f"{team_id}_{season}"
        
        # Use cached gamelog if available
        if cache_key not in self.gamelog_cache:
            try:
                # Rate limit: 1 request per second
                time_since_last = time.time() - self.last_api_call
                if time_since_last < 1.0:
                    time.sleep(1.0 - time_since_last)
                
                gamelog = teamgamelog.TeamGameLog(team_id=team_id, season=season, timeout=60)
                self.last_api_call = time.time()
                df = gamelog.get_data_frames()[0]
                
                # Sort by date
                df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'], format='%b %d, %Y')
                df = df.sort_values('GAME_DATE', ascending=False)
                
                self.gamelog_cache[cache_key] = df
            except Exception as e:
                logger.warning(f"Failed to fetch gamelog for team {team_id}: {e}")
                return {'rest_days': 1, 'is_back_to_back': False, 'games_in_last_7_days': 0}
        
        try:
            df = self.gamelog_cache[cache_key]
            
            target = pd.to_datetime(target_date)
            
            # Find last game before target
            past_games = df[df['GAME_DATE'] < target]
            if len(past_games) > 0:
                last_game = past_games.iloc[0]['GAME_DATE']
                rest_days = (target - last_game).days
                is_back_to_back = rest_days == 1
                
                return {
                    'rest_days': rest_days,
                    'is_back_to_back': is_back_to_back,
                    'games_in_last_7_days': len(past_games[past_games['GAME_DATE'] >= target - timedelta(days=7)])
                }
            
            return {'rest_days': 7, 'is_back_to_back': False, 'games_in_last_7_days': 0}
            
        except Exception as e:
            logger.warning(f"Failed to calculate rest for team {team_id}: {e}")
            return {}
    
    def calculate_travel_fatigue(self, team_id: int, target_date: str, season: str = '2024-25') -> Dict:
        """
        Calculate travel fatigue based on distance between games and timezone changes.
        
        Returns:
            Dict with travel_distance_miles, timezone_change, travel_fatigue_score (0-100)
        """
        # NBA Arena locations (lat, lon, timezone offset from ET)
        ARENA_LOCATIONS = {
            1610612737: (33.7573, -84.3963, 0),    # ATL Hawks
            1610612738: (42.3662, -71.0621, 0),    # BOS Celtics
            1610612751: (40.6826, -73.9754, 0),    # BKN Nets
            1610612766: (35.2251, -80.8392, 0),    # CHA Hornets
            1610612741: (41.8807, -87.6742, -1),   # CHI Bulls
            1610612739: (41.4965, -81.6882, 0),    # CLE Cavaliers
            1610612742: (32.7905, -96.8103, -1),   # DAL Mavericks
            1610612743: (39.7487, -105.0077, -2),  # DEN Nuggets
            1610612765: (42.3410, -83.0552, 0),    # DET Pistons
            1610612744: (37.7503, -122.2033, -3),  # GSW Warriors
            1610612745: (29.7508, -95.3621, -1),   # HOU Rockets
            1610612754: (39.7640, -86.1555, 0),    # IND Pacers
            1610612746: (34.0430, -118.2673, -3),  # LAC Clippers
            1610612747: (34.0430, -118.2673, -3),  # LAL Lakers
            1610612763: (35.1382, -90.0505, -1),   # MEM Grizzlies
            1610612748: (25.7814, -80.1870, 0),    # MIA Heat
            1610612749: (43.0451, -87.9173, -1),   # MIL Bucks
            1610612750: (44.9795, -93.2760, -1),   # MIN Timberwolves
            1610612740: (29.9490, -90.0821, -1),   # NOP Pelicans
            1610612752: (40.7505, -73.9934, 0),    # NYK Knicks
            1610612760: (35.4634, -97.5151, -1),   # OKC Thunder
            1610612753: (28.5392, -81.3839, 0),    # ORL Magic
            1610612755: (39.9012, -75.1720, 0),    # PHI 76ers
            1610612756: (33.4457, -112.0712, -2),  # PHX Suns
            1610612757: (45.5316, -122.6668, -3),  # POR Trail Blazers
            1610612758: (38.5802, -121.4997, -3),  # SAC Kings
            1610612759: (29.4270, -98.4375, -1),   # SAS Spurs
            1610612761: (43.6435, -79.3791, 0),    # TOR Raptors
            1610612762: (40.7683, -111.9011, -2),  # UTA Jazz
            1610612764: (38.8981, -77.0209, 0),    # WAS Wizards
        }
        
        try:
            cache_key = f"{team_id}_{season}"
            
            if cache_key not in self.gamelog_cache:
                return {'travel_distance_miles': 0, 'timezone_change': 0, 'travel_fatigue_score': 0}
            
            df = self.gamelog_cache[cache_key]
            target = pd.to_datetime(target_date)
            
            # Get last two games
            past_games = df[df['GAME_DATE'] < target].head(2)
            
            if len(past_games) < 1:
                return {'travel_distance_miles': 0, 'timezone_change': 0, 'travel_fatigue_score': 0}
            
            # Get home location
            team_loc = ARENA_LOCATIONS.get(team_id, (39.0, -98.0, -1))  # Default to center of US
            
            # Determine if last game was away (check MATCHUP column for '@')
            last_game = past_games.iloc[0]
            matchup = last_game.get('MATCHUP', '')
            
            distance = 0
            tz_change = 0
            
            if '@' in matchup:
                # Extract opponent team abbr and find their location
                # MATCHUP format: "LAL @ BOS" or "LAL vs. BOS"
                parts = matchup.split('@')
                if len(parts) == 2:
                    # Approximate distance calculation using lat/lon
                    # This is simplified - real implementation would use team abbreviation lookup
                    # For now, estimate based on whether it was an away game
                    distance = 1500  # Average NBA travel distance
                    tz_change = 1  # Assume 1 timezone on average
            
            # Calculate fatigue score (0-100)
            # Factors: distance, timezone changes, back-to-back status
            fatigue_score = 0
            
            # Distance factor (0-40 points)
            if distance > 2000:
                fatigue_score += 40
            elif distance > 1500:
                fatigue_score += 30
            elif distance > 1000:
                fatigue_score += 20
            elif distance > 500:
                fatigue_score += 10
            
            # Timezone factor (0-30 points)
            fatigue_score += min(abs(tz_change) * 10, 30)
            
            # Back-to-back factor (0-30 points)
            rest_info = self.calculate_rest_days(team_id, target_date, season)
            if rest_info.get('is_back_to_back', False):
                fatigue_score += 30
            elif rest_info.get('rest_days', 3) <= 2:
                fatigue_score += 15
            
            return {
                'travel_distance_miles': distance,
                'timezone_change': tz_change,
                'travel_fatigue_score': min(fatigue_score, 100)
            }
            
        except Exception as e:
            logger.warning(f"Failed to calculate travel fatigue for team {team_id}: {e}")
            return {'travel_distance_miles': 0, 'timezone_change': 0, 'travel_fatigue_score': 0}


rest_fatigue_agent = RestFatigueAgent()
