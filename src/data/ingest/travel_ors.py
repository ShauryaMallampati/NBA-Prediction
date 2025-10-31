"""
Travel Distance Calculator + Fatigue Scoring

Calculates travel-related fatigue factors that impact player performance:
- Distance traveled between arenas
- Timezone crossings
- Back-to-back game detection
- Composite fatigue score (0-100)

Expert bettor insight: Travel fatigue significantly impacts player props.
Example: Cross-country B2B after 38 mins → 75 fatigue score → confidence -15%
"""

from __future__ import annotations
import os
import math
from datetime import datetime, timedelta
from typing import Optional
import pathlib
import json

OUT = pathlib.Path("data/raw/travel").resolve()

# ✅ NBA Arena Locations (lat, lon, timezone)
NBA_ARENAS = {
    "Boston Celtics": {"coords": (42.3661, -71.0589), "tz": "America/New_York"},
    "Brooklyn Nets": {"coords": (40.6826, -73.9754), "tz": "America/New_York"},
    "New York Knicks": {"coords": (40.7505, -73.9934), "tz": "America/New_York"},
    "Philadelphia 76ers": {"coords": (39.9012, -75.1720), "tz": "America/New_York"},
    "Toronto Raptors": {"coords": (43.6426, -79.3871), "tz": "America/Toronto"},
    "Chicago Bulls": {"coords": (41.8807, -87.6742), "tz": "America/Chicago"},
    "Cleveland Cavaliers": {"coords": (41.4965, -81.6882), "tz": "America/New_York"},
    "Detroit Pistons": {"coords": (42.6829, -83.2754), "tz": "America/Detroit"},
    "Indiana Pacers": {"coords": (39.7639, -86.1555), "tz": "America/Indiana/Indianapolis"},
    "Milwaukee Bucks": {"coords": (43.0449, -87.9171), "tz": "America/Chicago"},
    "Atlanta Hawks": {"coords": (33.7490, -84.3880), "tz": "America/New_York"},
    "Charlotte Hornets": {"coords": (35.2251, -80.8392), "tz": "America/New_York"},
    "Miami Heat": {"coords": (25.7813, -80.1886), "tz": "America/New_York"},
    "Orlando Magic": {"coords": (28.5421, -81.3887), "tz": "America/New_York"},
    "Washington Wizards": {"coords": (38.8980, -77.0209), "tz": "America/New_York"},
    "Denver Nuggets": {"coords": (39.7487, -104.9957), "tz": "America/Denver"},
    "Minnesota Timberwolves": {"coords": (44.9795, -93.2789), "tz": "America/Chicago"},
    "Oklahoma City Thunder": {"coords": (35.4635, -97.5151), "tz": "America/Chicago"},
    "Portland Trail Blazers": {"coords": (45.2325, -122.7615), "tz": "America/Los_Angeles"},
    "Utah Jazz": {"coords": (40.7683, -111.9011), "tz": "America/Denver"},
    "Golden State Warriors": {"coords": (37.7694, -122.3862), "tz": "America/Los_Angeles"},
    "LA Clippers": {"coords": (34.0430, -118.2673), "tz": "America/Los_Angeles"},
    "Los Angeles Lakers": {"coords": (34.0430, -118.2673), "tz": "America/Los_Angeles"},
    "Phoenix Suns": {"coords": (33.3760, -112.0618), "tz": "America/Phoenix"},
    "Sacramento Kings": {"coords": (38.5816, -121.4944), "tz": "America/Los_Angeles"},
    "Dallas Mavericks": {"coords": (32.7905, -96.8103), "tz": "America/Chicago"},
    "Houston Rockets": {"coords": (29.7589, -95.3677), "tz": "America/Chicago"},
    "Memphis Grizzlies": {"coords": (35.1395, -90.0076), "tz": "America/Chicago"},
    "New Orleans Pelicans": {"coords": (29.9487, -90.0821), "tz": "America/Chicago"},
    "San Antonio Spurs": {"coords": (29.4269, -98.4375), "tz": "America/Chicago"},
}

# Timezone offsets from UTC (EST)
TIMEZONE_OFFSETS = {
    "America/New_York": 0,
    "America/Toronto": 0,
    "America/Detroit": 0,
    "America/Indiana/Indianapolis": 0,
    "America/Chicago": -1,
    "America/Denver": -2,
    "America/Phoenix": -2,
    "America/Los_Angeles": -3,
}


class TravelFatigueCalculator:
    """
    Calculates travel-based fatigue factors for NBA players.
    
    Features generated:
    - distance_miles: Travel distance from last arena
    - timezone_diff: Hours of timezone difference
    - back_to_back: Boolean (true if B2B game)
    - minutes_played_yesterday: Minutes in previous game
    - fatigue_score: Composite 0-100 score (higher = more tired)
    """
    
    def __init__(self, ors_api_key: Optional[str] = None):
        """Initialize with optional ORS API key for accurate distances."""
        self.ors_api_key = ors_api_key or os.environ.get("ORS_API_KEY")
        self.use_ors = self.ors_api_key is not None
    
    def get_distance_miles(self, arena_a: str, arena_b: str) -> float:
        """
        Calculate distance between two arenas.
        
        Uses coordinate-based calculation (fast, no API needed).
        Falls back to Haversine formula if arenas not found.
        
        Args:
            arena_a: "Los Angeles Lakers"
            arena_b: "Boston Celtics"
        
        Returns:
            Distance in miles
        """
        if arena_a not in NBA_ARENAS or arena_b not in NBA_ARENAS:
            return 0.0
        
        coords_a = NBA_ARENAS[arena_a]["coords"]
        coords_b = NBA_ARENAS[arena_b]["coords"]
        
        # Haversine formula (accurate enough for arena distances)
        lat1, lon1 = coords_a
        lat2, lon2 = coords_b
        
        r = 3959  # Earth radius in miles
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return r * c
    
    def get_timezone_diff(self, tz_from: str, tz_to: str) -> int:
        """
        Calculate timezone difference in hours.
        
        Positive = going east (more sleep), Negative = going west (less sleep)
        
        Args:
            tz_from: Source timezone (e.g., "America/Los_Angeles")
            tz_to: Destination timezone (e.g., "America/New_York")
        
        Returns:
            Hour difference (positive = gained time/sleep going east)
        """
        offset_from = TIMEZONE_OFFSETS.get(tz_from, 0)
        offset_to = TIMEZONE_OFFSETS.get(tz_to, 0)
        
        # If going from LA (-3) to NY (0), offset_from=-3, offset_to=0
        # difference = -3 - 0 = -3 (need to add 3 hours of sleep)
        # But positive means GAINED sleep, so return the opposite
        return offset_to - offset_from
    
    def is_back_to_back(self, schedule: list[dict], 
                       current_date: str) -> bool:
        """
        Detect if a team plays on back-to-back days.
        
        Args:
            schedule: List of game dicts with 'date' field (YYYY-MM-DD)
            current_date: Check for B2B around this date
        
        Returns:
            True if team plays today and tomorrow (or yesterday and today)
        """
        try:
            current = datetime.strptime(current_date, "%Y-%m-%d")
            yesterday = current - timedelta(days=1)
            tomorrow = current + timedelta(days=1)
            
            schedule_dates = {datetime.strptime(g.get("date", ""), "%Y-%m-%d") 
                            for g in schedule if "date" in g}
            
            # Check if played yesterday or tomorrow relative to current
            has_today = current in schedule_dates
            has_yesterday = yesterday in schedule_dates
            has_tomorrow = tomorrow in schedule_dates
            
            return (has_today and has_yesterday) or (has_today and has_tomorrow)
        except (ValueError, KeyError):
            return False
    
    def get_previous_arena(self, schedule: list[dict], 
                          current_date: str) -> Optional[str]:
        """
        Find the team's previous game arena.
        
        Args:
            schedule: List of game dicts with 'date' and 'arena' fields
            current_date: Find game before this date
        
        Returns:
            Arena name or None if not found
        """
        try:
            current = datetime.strptime(current_date, "%Y-%m-%d")
            previous_games = []
            
            for game in schedule:
                if "date" not in game:
                    continue
                game_date = datetime.strptime(game["date"], "%Y-%m-%d")
                if game_date < current:
                    previous_games.append((game_date, game.get("arena")))
            
            if not previous_games:
                return None
            
            # Most recent game
            previous_games.sort(reverse=True)
            return previous_games[0][1]
        except (ValueError, KeyError):
            return None
    
    def calculate_fatigue_score(self, distance_miles: float, 
                               timezone_diff: int,
                               minutes_yesterday: float,
                               back_to_back: bool) -> float:
        """
        Calculate composite fatigue score (0-100).
        
        Algorithm:
          • Distance: 2500 miles → +25
          • Timezone: 3 hours → +30
          • Minutes: 38 min → +24 (max 25 for 40+)
          • B2B: +15 if true
        
        Args:
            distance_miles: Miles traveled
            timezone_diff: Hours of timezone change
            minutes_yesterday: Minutes played in previous game
            back_to_back: Boolean
        
        Returns:
            Fatigue score 0-100 (higher = more tired)
        """
        score = 0.0
        
        # Distance contribution (e.g., 2500 miles → 25 points)
        score += min(distance_miles / 100, 30)
        
        # Timezone contribution (e.g., 3 hours west → 30 points)
        score += abs(timezone_diff) * 10
        
        # Minutes contribution (e.g., 38 min → 24 points)
        score += min(minutes_yesterday, 40) / 40 * 25
        
        # Back-to-back bonus
        if back_to_back:
            score += 15
        
        return min(score, 100)
    
    def extract_travel_fatigue(self, team: str, current_date: str,
                              current_arena: str, schedule: list[dict],
                              minutes_yesterday: float = 0.0) -> dict:
        """
        Complete travel fatigue extraction for a team on a date.
        
        Args:
            team: Team name (e.g., "Boston Celtics")
            current_date: Date in YYYY-MM-DD format
            current_arena: Arena name or team name for today's game
            schedule: List of games with date/arena fields
            minutes_yesterday: Minutes played in previous game
        
        Returns:
            Dict with all travel fatigue features:
            {
              'distance_miles': 2450.0,
              'timezone_diff': 3,
              'back_to_back': True,
              'minutes_yesterday': 38.0,
              'fatigue_score': 68,
              'previous_arena': 'Crypto.com Arena (LA)',
              'interpretation': 'Cross-country B2B after 38 mins'
            }
        """
        previous_arena = self.get_previous_arena(schedule, current_date)
        b2b = self.is_back_to_back(schedule, current_date)
        
        distance = 0.0
        tz_diff = 0
        
        if previous_arena and previous_arena in NBA_ARENAS and current_arena in NBA_ARENAS:
            distance = self.get_distance_miles(previous_arena, current_arena)
            tz_from = NBA_ARENAS[previous_arena]["tz"]
            tz_to = NBA_ARENAS[current_arena]["tz"]
            tz_diff = self.get_timezone_diff(tz_from, tz_to)
        
        fatigue = self.calculate_fatigue_score(
            distance, tz_diff, minutes_yesterday, b2b
        )
        
        # Generate interpretation
        parts = []
        if distance > 1000:
            parts.append(f"{int(distance)}-mile trip")
        if tz_diff > 0:
            parts.append(f"+{tz_diff}h timezone (extra sleep)")
        elif tz_diff < 0:
            parts.append(f"{tz_diff}h timezone (jetlag)")
        if b2b:
            parts.append("back-to-back")
        if minutes_yesterday > 30:
            parts.append(f"{int(minutes_yesterday)} min yesterday")
        
        interpretation = " + ".join(parts) if parts else "Rest day"
        
        return {
            "distance_miles": round(distance, 1),
            "timezone_diff": tz_diff,
            "back_to_back": b2b,
            "minutes_yesterday": round(minutes_yesterday, 1),
            "fatigue_score": int(fatigue),
            "previous_arena": previous_arena or "N/A",
            "current_arena": current_arena,
            "interpretation": interpretation,
        }


def main(seed: bool = True) -> None:
    """Seed example travel fatigue data."""
    OUT.mkdir(parents=True, exist_ok=True)
    
    calc = TravelFatigueCalculator()
    
    if seed:
        # Example: Celtics travel to Lakers on back-to-back after 38 mins
        schedule = [
            {"date": "2023-11-14", "arena": "TD Garden (Boston)"},
            {"date": "2023-11-15", "arena": "Crypto.com Arena (LA)"},
        ]
        
        result = calc.extract_travel_fatigue(
            team="Boston Celtics",
            current_date="2023-11-15",
            current_arena="Crypto.com Arena (LA)",
            schedule=schedule,
            minutes_yesterday=38.0,
        )
        
        (OUT / "celtics_travel_fatigue.json").write_text(
            json.dumps(result, indent=2)
        )


if __name__ == "__main__":
    main(True)
