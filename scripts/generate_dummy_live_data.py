"""
Generate dummy live sequence data for RNN training verification.
"""
import pandas as pd
import numpy as np
from pathlib import Path

def main():
    print("Generating dummy live data...")
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Create dummy sequences
    # We need 'game_id', 'score_diff', 'winner'
    
    data = []
    for i in range(100): # 100 games
        game_id = f"game_{i:03d}"
        winner = np.random.randint(0, 2)
        
        # Create a sequence of 50 time steps
        for t in range(50):
            # Score diff tends towards the winner
            trend = (t / 50) * (10 if winner == 1 else -10)
            noise = np.random.normal(0, 5)
            score_diff = trend + noise
            
            data.append({
                'game_id': game_id,
                'time_step': t,
                'score_diff': score_diff,
                'winner': winner
            })
            
    df = pd.DataFrame(data)
    out_path = data_dir / "live_sequences.parquet"
    df.to_parquet(out_path)
    print(f"✅ Saved {len(df)} rows to {out_path}")

if __name__ == "__main__":
    main()
