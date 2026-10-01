"""Pull game details out of YouTube video titles.

When you have a video like "Lakers vs Warriors Full Highlights",
we extract the teams, date, and other metadata.
"""

import re
import subprocess
import json
from typing import Optional


# =============================================================================
# NBA Team Name Mappings
# =============================================================================

NBA_TEAMS = {
    # Full names
    "Atlanta Hawks": ("Atlanta Hawks", "Hawks", "ATL"),
    "Boston Celtics": ("Boston Celtics", "Celtics", "BOS"),
    "Brooklyn Nets": ("Brooklyn Nets", "Nets", "BKN"),
    "Charlotte Hornets": ("Charlotte Hornets", "Hornets", "CHA"),
    "Chicago Bulls": ("Chicago Bulls", "Bulls", "CHI"),
    "Cleveland Cavaliers": ("Cleveland Cavaliers", "Cavaliers", "CLE"),
    "Dallas Mavericks": ("Dallas Mavericks", "Mavericks", "DAL"),
    "Denver Nuggets": ("Denver Nuggets", "Nuggets", "DEN"),
    "Detroit Pistons": ("Detroit Pistons", "Pistons", "DET"),
    "Golden State Warriors": ("Golden State Warriors", "Warriors", "GSW"),
    "Houston Rockets": ("Houston Rockets", "Rockets", "HOU"),
    "Indiana Pacers": ("Indiana Pacers", "Pacers", "IND"),
    "LA Clippers": ("LA Clippers", "Clippers", "LAC"),
    "Los Angeles Lakers": ("Los Angeles Lakers", "Lakers", "LAL"),
    "Memphis Grizzlies": ("Memphis Grizzlies", "Grizzlies", "MEM"),
    "Miami Heat": ("Miami Heat", "Heat", "MIA"),
    "Milwaukee Bucks": ("Milwaukee Bucks", "Bucks", "MIL"),
    "Minnesota Timberwolves": ("Minnesota Timberwolves", "Timberwolves", "MIN"),
    "New Orleans Pelicans": ("New Orleans Pelicans", "Pelicans", "NOP"),
    "New York Knicks": ("New York Knicks", "Knicks", "NYK"),
    "Oklahoma City Thunder": ("Oklahoma City Thunder", "Thunder", "OKC"),
    "Orlando Magic": ("Orlando Magic", "Magic", "ORL"),
    "Philadelphia 76ers": ("Philadelphia 76ers", "76ers", "PHI"),
    "Phoenix Suns": ("Phoenix Suns", "Suns", "PHX"),
    "Portland Trail Blazers": ("Portland Trail Blazers", "Trail Blazers", "POR"),
    "Sacramento Kings": ("Sacramento Kings", "Kings", "SAC"),
    "San Antonio Spurs": ("San Antonio Spurs", "Spurs", "SAS"),
    "Toronto Raptors": ("Toronto Raptors", "Raptors", "TOR"),
    "Utah Jazz": ("Utah Jazz", "Jazz", "UTA"),
    "Washington Wizards": ("Washington Wizards", "Wizards", "WAS"),
}

# Build reverse lookup for all variations
TEAM_LOOKUP = {}
for full_name, (name, short, abbrev) in NBA_TEAMS.items():
    TEAM_LOOKUP[full_name.lower()] = full_name
    TEAM_LOOKUP[name.lower()] = full_name
    TEAM_LOOKUP[short.lower()] = full_name
    TEAM_LOOKUP[abbrev.lower()] = full_name


def normalize_team_name(name: str) -> str:
    """Take any variation of a team name and return the full official version."""
    return TEAM_LOOKUP.get(name.lower().strip(), name)


# =============================================================================
# Title Parsing
# =============================================================================

def extract_game_info_from_title(title: str) -> dict:
    """Parse out home vs. away teams from a YouTube video title.
    
    We handle all the common formats:
    - "Boston Celtics vs New York Knicks Full Game Highlights"
    - "LAL vs GSW | NBA Highlights"
    - "Celtics @ Knicks"
    - "Heat vs Celtics - Full Game"
    
    Returns:
        Dictionary with home_team, away_team, and date (if we can find it)
    """
    result = {
        "home_team": "Unknown",
        "away_team": "Unknown",
        "date": None
    }
    
    # Normalize title
    title_lower = title.lower()
    
    # Pattern 1: "Team1 vs Team2" or "Team1 @ Team2"
    vs_pattern = r'([a-zA-Z\s]+?)\s*(?:vs\.?|@|versus)\s*([a-zA-Z\s]+?)(?:\s*[-|:]|\s+full|\s+game|\s+highlights|$)'
    match = re.search(vs_pattern, title, re.IGNORECASE)
    
    if match:
        team1 = match.group(1).strip()
        team2 = match.group(2).strip()
        
        # Normalize team names
        team1_full = normalize_team_name(team1)
        team2_full = normalize_team_name(team2)
        
        # In "vs" format, second team is usually home (but not always)
        # In "@" format, second team is definitly home
        if "@" in title:
            result["away_team"] = team1_full
            result["home_team"] = team2_full
        else:
            # Default: first team is "visiting" context in highlights
            result["home_team"] = team2_full
            result["away_team"] = team1_full
    
    # Pattern 2: Search for any team abbreviations (fallback)
    if result["home_team"] == "Unknown":
        found_teams = []
        for key in TEAM_LOOKUP:
            if len(key) >= 3 and key in title_lower:
                found_teams.append(TEAM_LOOKUP[key])
        
        # Deduplicate
        found_teams = list(dict.fromkeys(found_teams))
        
        if len(found_teams) >= 2:
            result["away_team"] = found_teams[0]
            result["home_team"] = found_teams[1]
        elif len(found_teams) == 1:
            result["home_team"] = found_teams[0]
    
    # Try to extract date (common formats)
    date_patterns = [
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # 12/25/2024
        r'(\w+\s+\d{1,2},?\s+\d{4})',         # December 25, 2024
    ]
    
    for pattern in date_patterns:
        date_match = re.search(pattern, title)
        if date_match:
            result["date"] = date_match.group(1)
            break
    
    return result


# =============================================================================
# YouTube Metadata
# =============================================================================

def get_video_metadata(url: str) -> Optional[dict]:
    """
    Fetch video metadata using yt-dlp.
    
    Returns:
        {
            "title": str,
            "duration": float (seconds),
            "upload_date": str,
            "view_count": int,
            "channel": str
        }
    """
    try:
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            url
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return None
        
        data = json.loads(result.stdout)
        
        return {
            "title": data.get("title", "Unknown"),
            "duration": data.get("duration", 0),
            "upload_date": data.get("upload_date"),
            "view_count": data.get("view_count", 0),
            "channel": data.get("channel", "Unknown")
        }
        
    except Exception:
        return None


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    # Test title parsing
    test_titles = [
        "Boston Celtics vs New York Knicks Full Game Highlights",
        "LAL vs GSW | NBA Highlights 12/25/2024",
        "Heat @ Celtics - Full Game Recap",
        "Philadelphia 76ers versus Milwaukee Bucks Highlights",
    ]
    
    for title in test_titles:
        info = extract_game_info_from_title(title)
        print(f"\nTitle: {title}")
        print(f"  Home: {info['home_team']}")
        print(f"  Away: {info['away_team']}")
