import json
import pandas as pd
import numpy as np
from pathlib import Path
import sys

def analyze():
    # Find latest prediction file
    pred_dir = Path("data/predictions")
    files = list(pred_dir.glob("*.jsonl"))
    if not files:
        print("No prediction files found")
        return

    latest_file = sorted(files)[-1]
    print(f"Analyzing {latest_file}...")

    data = []
    with open(latest_file, 'r') as f:
        for line in f:
            data.append(json.loads(line))

    df = pd.DataFrame(data)
    
    # Probabilities
    probs = df['home_win_probability']
    
    print("\n=== Probability Stats (Home Win %) ===")
    print(probs.describe())
    
    print("\n=== Histogram Buckets ===")
    buckets = [0, 10, 20, 30, 40, 45, 50, 55, 60, 70, 80, 90, 100]
    print(pd.cut(probs, buckets).value_counts().sort_index())

    # Confidence (Edge)
    print("\n=== Confidence / Edge Stats ===")
    print(df['confidence'].describe())

    # Check for collapse
    near_50 = len(df[(probs >= 45) & (probs <= 55)])
    print(f"\nGames within 45-55%: {near_50} / {len(df)} ({near_50/len(df)*100:.1f}%)")

if __name__ == "__main__":
    analyze()
