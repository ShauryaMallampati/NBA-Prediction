"""
Fetch NBA Lineup Data for Player Chemistry Analysis (Robust Version)

Uses nba_api with retries and smaller requests to avoid timeout.
"""

import json
import time
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("data/chemistry")
PLAYER_PAIRS_FILE = OUTPUT_DIR / "player_pairs.json"


def fetch_player_pairs_by_team():
    """Fetch 2-man lineup data team by team to avoid timeout."""
    from nba_api.stats.endpoints import teamdashlineups
    from nba_api.stats.static import teams
    
    logger.info("🏀 Fetching player pair chemistry data...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    nba_teams = teams.get_teams()
    all_pairs = {}
    
    for team in nba_teams:
        team_id = team['id']
        team_abbr = team['abbreviation']
        
        logger.info(f"   Fetching {team_abbr}...")
        
        try:
            lineups = teamdashlineups.TeamDashLineups(
                team_id=team_id,
                season='2024-25',
                season_type_all_star='Regular Season',
                group_quantity=2,  # 2-man combos
                per_mode_detailed='PerGame',
                timeout=60
            )
            time.sleep(1.0)  # Rate limiting
            
            df = lineups.get_data_frames()[1]  # Lineups dataframe
            
            for _, row in df.iterrows():
                group_name = row.get('GROUP_NAME', '')
                if ' - ' in group_name:
                    players = [p.strip() for p in group_name.split(' - ')]
                    if len(players) == 2:
                        player1, player2 = sorted(players)
                        pair_key = f"{player1}|{player2}"
                        
                        all_pairs[pair_key] = {
                            'player1': player1,
                            'player2': player2,
                            'team': team_abbr,
                            'games': int(row.get('GP', 0)),
                            'minutes': float(row.get('MIN', 0)),
                            'net_rating': float(row.get('NET_RATING', 0) or 0),
                            'plus_minus': float(row.get('PLUS_MINUS', 0) or 0),
                        }
            
            logger.info(f"      Found {len(df)} pairs for {team_abbr}")
            
        except Exception as e:
            logger.warning(f"      ⚠️ Failed for {team_abbr}: {e}")
            time.sleep(2.0)  # Wait longer on error
            continue
    
    # Save
    with open(PLAYER_PAIRS_FILE, 'w') as f:
        json.dump({
            'scraped_at': datetime.now().isoformat(),
            'total_pairs': len(all_pairs),
            'pairs': all_pairs
        }, f, indent=2)
    
    logger.info(f"✅ Saved {len(all_pairs)} player pairs to {PLAYER_PAIRS_FILE}")
    return all_pairs


def build_chemistry_scores():
    """Build team chemistry scores from player pairs."""
    import numpy as np
    
    if not PLAYER_PAIRS_FILE.exists():
        logger.error("No player pairs data. Run fetch_player_pairs_by_team() first.")
        return None
    
    with open(PLAYER_PAIRS_FILE, 'r') as f:
        data = json.load(f)
    
    pairs = data.get('pairs', {})
    logger.info(f"🔗 Building chemistry scores from {len(pairs)} pairs...")
    
    # Group pairs by team
    team_pairs = {}
    for pair_key, pair_data in pairs.items():
        team = pair_data['team']
        if team not in team_pairs:
            team_pairs[team] = []
        team_pairs[team].append(pair_data)
    
    # Calculate team chemistry score using PLUS_MINUS (since net_rating is often 0)
    team_chemistry = {}
    for team, pair_list in team_pairs.items():
        if not pair_list:
            team_chemistry[team] = 0.5
            continue
        
        # Weight by minutes played together
        total_mins = sum(p['minutes'] for p in pair_list)
        if total_mins == 0:
            team_chemistry[team] = 0.5
            continue
        
        # Weighted average plus_minus (use this instead of net_rating)
        weighted_pm = sum(p['plus_minus'] * p['minutes'] for p in pair_list) / total_mins
        
        # Normalize to 0-1 (plus_minus typically -5 to +5 per game)
        score = (weighted_pm + 5) / 10
        score = max(0.1, min(0.9, score))
        
        team_chemistry[team] = round(score, 3)
    
    # Find top duos by plus_minus (weighted by games played)
    top_duos = sorted(
        [p for p in pairs.values() if p['games'] >= 10],  # At least 10 games
        key=lambda x: x['plus_minus'],
        reverse=True
    )[:20]
    
    # Save chemistry scores
    output = {
        'generated_at': datetime.now().isoformat(),
        'team_chemistry': team_chemistry,
        'top_duos': [
            {
                'players': f"{d['player1']} + {d['player2']}",
                'team': d['team'],
                'net_rating': d['plus_minus'],  # Use plus_minus as the metric
                'games': d['games'],
                'chemistry_score': round((d['plus_minus'] + 5) / 10, 2)
            }
            for d in top_duos
        ]
    }
    
    with open(OUTPUT_DIR / "chemistry_scores.json", 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"✅ Generated chemistry scores for {len(team_chemistry)} teams")
    if top_duos:
        logger.info(f"   Top duo: {top_duos[0]['player1']} + {top_duos[0]['player2']} ({top_duos[0]['plus_minus']:.1f} +/-)")
    
    return team_chemistry, top_duos


if __name__ == "__main__":
    pairs = fetch_player_pairs_by_team()
    if pairs:
        build_chemistry_scores()
