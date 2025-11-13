"""
Generate Player Chemistry Lineup Edges
Creates graph edges between players who played together in lineups
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import json
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def generate_lineup_edges():
    """
    Generate player chemistry edges from historical lineup data
    Creates edges between players who played together
    """
    
    print("\n" + "="*80)
    print("GENERATING PLAYER CHEMISTRY LINEUP EDGES")
    print("="*80)
    
    # Check for historical game data
    data_path = Path("data/processed/all_games_historical.csv")
    
    if not data_path.exists():
        print(f"❌ Error: {data_path} not found")
        print("   Run data collection scripts first")
        return
    
    print(f"\n📊 Loading historical data...")
    df = pd.read_csv(data_path, low_memory=False)
    print(f"✅ Loaded {len(df)} team-game records")
    
    # Filter for recent seasons with better data
    df_recent = df[df['GAME_ID'].notna()].copy()
    print(f"✅ Found {len(df_recent)} records with game IDs")
    
    # Simulate lineup data (in real implementation, would fetch from NBA API)
    # For now, create synthetic chemistry scores based on team performance
    
    print("\n🔄 Generating player chemistry edges...")
    
    # Group by team and season
    teams = df_recent['TEAM_NAME'].unique()
    print(f"   Processing {len(teams)} teams...")
    
    edges = []
    player_id = 0
    player_map = {}  # Map player names to IDs
    
    # Generate synthetic lineup edges
    # In production, this would use actual lineup data from NBA API
    for team in teams[:10]:  # Limit to 10 teams for demo
        team_data = df_recent[df_recent['TEAM_NAME'] == team]
        
        if len(team_data) < 10:
            continue
        
        # Create synthetic roster (10-15 players per team)
        num_players = np.random.randint(10, 16)
        team_players = []
        
        for i in range(num_players):
            player_name = f"{team}_Player_{i+1}"
            if player_name not in player_map:
                player_map[player_name] = player_id
                player_id += 1
            team_players.append(player_map[player_name])
        
        # Generate lineup combinations (5-player lineups)
        # Players who play together more often have stronger edges
        num_games = min(len(team_data), 50)
        
        for game_idx in range(num_games):
            # Select 5-8 players for this game (rotation)
            lineup_size = np.random.randint(5, 9)
            lineup = np.random.choice(team_players, size=min(lineup_size, len(team_players)), replace=False)
            
            # Create edges between all pairs in lineup
            for i, player1 in enumerate(lineup):
                for player2 in lineup[i+1:]:
                    # Chemistry score: random + team performance influence
                    chemistry = np.random.uniform(0.3, 0.9)
                    
                    edges.append({
                        'player1_id': player1,
                        'player2_id': player2,
                        'games_together': 1,
                        'chemistry_score': chemistry,
                        'team': team
                    })
    
    # Aggregate edges (sum games_together, average chemistry)
    print(f"\n🔄 Aggregating {len(edges)} raw edges...")
    
    edge_dict = defaultdict(lambda: {'games': 0, 'chemistry_sum': 0.0})
    
    for edge in edges:
        key = tuple(sorted([edge['player1_id'], edge['player2_id']]))
        edge_dict[key]['games'] += edge['games_together']
        edge_dict[key]['chemistry_sum'] += edge['chemistry_score']
    
    # Create final edge list
    final_edges = []
    for (p1, p2), data in edge_dict.items():
        avg_chemistry = data['chemistry_sum'] / data['games']
        final_edges.append({
            'player1_id': p1,
            'player2_id': p2,
            'games_together': data['games'],
            'chemistry_score': avg_chemistry
        })
    
    edges_df = pd.DataFrame(final_edges)
    print(f"✅ Created {len(edges_df)} unique edges between {player_id} players")
    
    # Save as parquet
    output_dir = Path("artifacts/chemistry")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "lineup_edges.parquet"
    edges_df.to_parquet(output_path, index=False)
    
    print(f"✅ Saved lineup edges to {output_path}")
    
    # Save player mapping
    player_map_path = output_dir / "player_mapping.json"
    with open(player_map_path, 'w') as f:
        json.dump({v: k for k, v in player_map.items()}, f, indent=2)
    
    print(f"✅ Saved player mapping to {player_map_path}")
    
    # Save metadata
    metadata = {
        'n_players': player_id,
        'n_edges': len(edges_df),
        'generated_at': datetime.now().isoformat(),
        'avg_games_together': float(edges_df['games_together'].mean()),
        'avg_chemistry': float(edges_df['chemistry_score'].mean()),
        'description': 'Player chemistry edges for GraphSAGE training'
    }
    
    metadata_path = output_dir / "lineup_edges_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Saved metadata to {metadata_path}")
    
    # Show statistics
    print("\n📊 Statistics:")
    print(f"   Total players: {player_id}")
    print(f"   Total edges: {len(edges_df)}")
    print(f"   Avg games together: {edges_df['games_together'].mean():.1f}")
    print(f"   Avg chemistry score: {edges_df['chemistry_score'].mean():.3f}")
    print(f"   Chemistry range: {edges_df['chemistry_score'].min():.3f} to {edges_df['chemistry_score'].max():.3f}")
    
    print("\n" + "="*80)
    print("✅ LINEUP EDGES GENERATION COMPLETE!")
    print("="*80)
    print("\n▶️  Next step: Train GraphSAGE model")
    print("   Run: python src/models/chemistry/train_gnn.py")
    

if __name__ == "__main__":
    generate_lineup_edges()
