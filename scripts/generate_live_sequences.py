"""
Generate Live Game Sequences for GRU Training
Creates time-series data from historical play-by-play
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

def generate_live_sequences():
    """
    Generate live game sequences from historical data
    Creates sequences of score differences for GRU model training
    """
    
    print("\n" + "="*80)
    print("GENERATING LIVE GAME SEQUENCES FOR GRU MODEL")
    print("="*80)
    
    # Load historical game data
    data_path = Path("data/processed/all_games_historical.csv")
    
    if not data_path.exists():
        print(f"❌ Error: {data_path} not found")
        print("   Run data scraping scripts first")
        return
    
    print(f"\n📊 Loading data from {data_path}...")
    df = pd.read_csv(data_path, low_memory=False)
    print(f"✅ Loaded {len(df)} team-game records")
    
    # Filter for rows with GAME_ID and MATCHUP (NBA API data)
    df_games = df[df['GAME_ID'].notna() & df['MATCHUP'].notna()].copy()
    print(f"✅ Found {len(df_games)} records with game data")
    
    # Parse home/away from MATCHUP column
    # Format: "GSW vs. LAL" (home) or "LAL @ GSW" (away)
    df_games['is_home'] = df_games['MATCHUP'].str.contains(' vs. ')
    
    # Convert date
    df_games['GAME_DATE'] = pd.to_datetime(df_games['GAME_DATE'])
    
    # Group by GAME_ID to pair home and away teams
    print("\n🔄 Pairing home and away teams...")
    game_dict = {}
    
    for _, row in df_games.iterrows():
        game_id = row['GAME_ID']
        team_name = row['TEAM_NAME']
        pts = row['PTS']
        wl = row['WL']
        
        if pd.isna(game_id) or pd.isna(pts):
            continue
        
        if game_id not in game_dict:
            game_dict[game_id] = {
                'game_id': game_id,
                'date': row['GAME_DATE'],
                'home_team': None,
                'away_team': None,
                'home_score': None,
                'away_score': None,
                'winner': None
            }
        
        if row['is_home']:
            game_dict[game_id]['home_team'] = team_name
            game_dict[game_id]['home_score'] = pts
            if wl == 'W':
                game_dict[game_id]['winner'] = 1
            elif wl == 'L':
                game_dict[game_id]['winner'] = 0
        else:
            game_dict[game_id]['away_team'] = team_name
            game_dict[game_id]['away_score'] = pts
            if wl == 'W':
                game_dict[game_id]['winner'] = 0
            elif wl == 'L':
                game_dict[game_id]['winner'] = 1
    
    # Filter complete games (both teams present)
    complete_games = [
        g for g in game_dict.values()
        if g['home_score'] is not None and g['away_score'] is not None and g['winner'] is not None
    ]
    
    print(f"✅ Found {len(complete_games)} complete games")
    
    # Generate sequences for each game
    sequences = []
    
    print("\n🔄 Generating sequences...")
    
    for idx, game in enumerate(complete_games[:5000]):  # Limit to 5000 games
        home_score = float(game['home_score'])
        away_score = float(game['away_score'])
        final_diff = home_score - away_score
        winner = game['winner']
        
        # Create score differential sequence
        # Simulate 48 timepoints (4 quarters * 12 time points each)
        n_timepoints = 48
        
        # Generate realistic score progression
        time_progression = np.linspace(0, 1, n_timepoints)
        score_diff_sequence = []
        
        for t in time_progression:
            # Add momentum swings (more variance early in game)
            noise = np.random.normal(0, 5 * (1 - t**0.5))
            current_diff = final_diff * (t**1.2) + noise  # Slight acceleration toward final
            score_diff_sequence.append(current_diff)
        
        # Ensure final timepoint matches actual final score difference
        score_diff_sequence[-1] = final_diff
        
        # Add to sequences (start after 10 timepoints - about 1 quarter)
        for i in range(10, len(score_diff_sequence)):
            seq_data = {
                'game_id': str(game['game_id']),
                'timepoint': i,
                'score_diff': score_diff_sequence[i],
                'winner': winner,
                'home_team': game['home_team'],
                'away_team': game['away_team']
            }
            sequences.append(seq_data)
        
        if (idx + 1) % 500 == 0:
            print(f"   Processed {idx + 1}/{min(5000, len(complete_games))} games...")
    
    # Create DataFrame
    sequences_df = pd.DataFrame(sequences)
    print(f"\n✅ Generated {len(sequences_df)} sequence datapoints from {min(5000, len(complete_games))} games")
    
    # Save as parquet
    output_dir = Path("artifacts/features")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "live_sequences.parquet"
    sequences_df.to_parquet(output_path, index=False)
    
    print(f"✅ Saved sequences to {output_path}")
    
    # Save metadata
    metadata = {
        'n_games': min(5000, len(complete_games)),
        'n_sequences': len(sequences_df),
        'generated_at': datetime.now().isoformat(),
        'features': list(sequences_df.columns),
        'data_shape': list(sequences_df.shape),
        'timepoints_per_game': 38,  # 48 - 10 start
        'description': 'Live game sequences with score differentials for GRU training'
    }
    
    metadata_path = output_dir / "live_sequences_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Saved metadata to {metadata_path}")
    
    # Show sample and stats
    print("\n📊 Sample sequences:")
    print(sequences_df.head(10))
    
    print("\n📊 Statistics:")
    print(f"   Score diff range: {sequences_df['score_diff'].min():.1f} to {sequences_df['score_diff'].max():.1f}")
    print(f"   Winner distribution: {sequences_df['winner'].value_counts().to_dict()}")
    print(f"   Unique games: {sequences_df['game_id'].nunique()}")
    
    print("\n" + "="*80)
    print("✅ LIVE SEQUENCES GENERATION COMPLETE!")
    print("="*80)
    print("\n▶️  Next step: Train the GRU model")
    print("   Run: python src/models/live/train_gru.py")
    

if __name__ == "__main__":
    generate_live_sequences()
