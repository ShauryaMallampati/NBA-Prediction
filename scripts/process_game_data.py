#!/usr/bin/env python3
"""
Convert raw NBA game data to training format for Momentum Transformer.

This script reads the real game data from data/raw/games_2023_24.json
and creates a proper CSV file for training.
"""

import json
import pandas as pd
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("data")
RAW_FILE = DATA_DIR / "raw" / "games_2023_24.json"
OUTPUT_FILE = DATA_DIR / "nba_games_enhanced.csv"


def process_games(games: list) -> pd.DataFrame:
    """
    Process raw game data into a flat DataFrame.
    
    Each game has two rows in the raw data (one per team).
    We need to combine them into a single row with home/away info.
    """
    # Group games by GAME_ID
    game_pairs = defaultdict(list)
    for game in games:
        game_pairs[game['GAME_ID']].append(game)
    
    processed = []
    
    for game_id, teams in game_pairs.items():
        if len(teams) != 2:
            continue  # Skip incomplete games
        
        # Determine home vs away
        team1, team2 = teams
        
        # "vs." means home, "@" means away
        if 'vs.' in team1.get('MATCHUP', ''):
            home = team1
            away = team2
        else:
            home = team2
            away = team1
        
        processed.append({
            'date': home['GAME_DATE'],
            'game_id': game_id,
            'home': home['TEAM_ABBREVIATION'],
            'away': away['TEAM_ABBREVIATION'],
            'home_pts': home['PTS'],
            'away_pts': away['PTS'],
            'home_win': 1 if home['WL'] == 'W' else 0,
            'margin': home['PTS'] - away['PTS'],
            'home_fg_pct': home.get('FG_PCT', 0),
            'away_fg_pct': away.get('FG_PCT', 0),
            'home_fg3_pct': home.get('FG3_PCT', 0),
            'away_fg3_pct': away.get('FG3_PCT', 0),
            'home_reb': home.get('REB', 0),
            'away_reb': away.get('REB', 0),
            'home_ast': home.get('AST', 0),
            'away_ast': away.get('AST', 0),
            'home_tov': home.get('TOV', 0),
            'away_tov': away.get('TOV', 0),
        })
    
    return pd.DataFrame(processed)


def main():
    print("=" * 60)
    print("🏀 NBA GAME DATA PROCESSOR")
    print("=" * 60)
    
    # Load raw data
    print(f"\n📂 Loading data from {RAW_FILE}...")
    with open(RAW_FILE, 'r') as f:
        data = json.load(f)
    
    games = data.get('games', [])
    print(f"   Found {len(games)} raw game records")
    
    # Process into DataFrame
    df = process_games(games)
    print(f"   Created {len(df)} unique game rows")
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Save
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Saved to {OUTPUT_FILE}")
    
    # Print summary
    print(f"\n📊 Data Summary:")
    print(f"   Games: {len(df)}")
    print(f"   Date Range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Teams: {len(set(df['home'].unique()) | set(df['away'].unique()))}")
    print(f"   Home Win Rate: {df['home_win'].mean():.2%}")


if __name__ == "__main__":
    main()
