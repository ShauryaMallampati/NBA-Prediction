#!/usr/bin/env python3
"""Turn the Kaggle NBA dataset into the flat game log the trainer reads.

Input:  data/kaggle_nba/Games.csv  (from kaggle.com/datasets/wyattowalsh/basketball)
Output: data/nba_games_enhanced.csv

The output has one row per completed game with the columns every downstream step
expects: date, game_id, home, away, home_pts, away_pts, home_win, margin.
Note that home_pts/away_pts/home_win/margin are outcome columns — they are used to
build the training target and to update team state after a game, never as features.
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "kaggle_nba" / "Games.csv"
OUTPUT_FILE = DATA_DIR / "nba_games_enhanced.csv"


def main():
    print("=" * 60)
    print("🏀 PROCESSING KAGGLE NBA DATASET")
    print("=" * 60)
    
    # Load data
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"{INPUT_FILE} not found. Download the Kaggle dataset "
            "'wyattowalsh/basketball' and place Games.csv there."
        )

    print(f"\n📂 Loading data from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    print(f"   Found {len(df)} total games")
    
    # Convert to standard format (extract date from first 10 chars to avoid timezone issues)
    processed = pd.DataFrame({
        'date': df['gameDateTimeEst'].astype(str).str[:10],
        'game_id': df['gameId'].astype(str),
        'home': df['hometeamName'],
        'away': df['awayteamName'],
        'home_pts': df['homeScore'],
        'away_pts': df['awayScore'],
        'home_win': (df['winner'] == df['hometeamId']).astype(int),
        'margin': df['homeScore'] - df['awayScore'],
    })
    
    # Filter out rows with missing scores
    processed = processed.dropna(subset=['home_pts', 'away_pts'])
    processed = processed[processed['home_pts'] > 0]
    
    # Sort by date
    processed = processed.sort_values('date').reset_index(drop=True)
    
    # Save
    processed.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Saved to {OUTPUT_FILE}")
    
    # Print summary
    print(f"\n📊 Data Summary:")
    print(f"   Games: {len(processed)}")
    print(f"   Date Range: {processed['date'].min()} to {processed['date'].max()}")
    print(f"   Teams: {len(set(processed['home'].unique()) | set(processed['away'].unique()))}")
    print(f"   Home Win Rate: {processed['home_win'].mean():.2%}")
    
    # Breakdown by decade
    processed['decade'] = pd.to_datetime(processed['date']).dt.year // 10 * 10
    decade_counts = processed.groupby('decade').size()
    print(f"\n📅 Games by Decade:")
    for decade, count in decade_counts.items():
        print(f"   {decade}s: {count} games")


if __name__ == "__main__":
    main()
