#!/usr/bin/env python3
"""
Train Ensemble v2 with different era cutoffs and evaluate.
Helps determine if modern-only training data improves predictions.
"""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
from src.common.features import RunningWorldState
from src.models.pregame.train_ensemble_v2 import EnsembleTrainerV2


def evaluate_with_era(df, era_start, cutoff='2024-10-01'):
    """Train on data from era_start to cutoff, evaluate on 2024-25."""
    print(f"\n{'='*60}")
    print(f"   Training on {era_start} to {cutoff}")
    print(f"{'='*60}")
    
    trainer = EnsembleTrainerV2(output_dir=f"artifacts/models/pregame_era_{era_start[:4]}")
    
    # Build features using RunningWorldState on ALL data (for proper warm-up)
    # but only train on games after era_start
    games = df.sort_values('date').reset_index(drop=True)
    world_state = RunningWorldState()
    
    all_features, all_labels, all_dates = [], [], []
    
    era_date = pd.to_datetime(era_start)
    cutoff_date = pd.to_datetime(cutoff)
    
    for _, row in games.iterrows():
        if row['date'] >= cutoff_date:
            break
            
        features = world_state.get_team_features(row['home'], row['away'], row['date'])
        
        # Only collect training data from era onwards
        if row['date'] >= era_date:
            all_features.append(features)
            all_labels.append(row['home_win'])
            all_dates.append(row['date'])
        
        world_state.update(row['home'], row['away'], row['date'], row['home_win'],
                          row.get('home_pts'), row.get('away_pts'))
    
    X = pd.DataFrame(all_features).replace([np.inf, -np.inf], np.nan).fillna(0)
    y = np.array(all_labels)
    
    trainer.feature_names = list(X.columns)
    print(f"  Training samples: {len(X)}")
    
    # Quick 3-fold CV to avoid long training times
    metrics = trainer.train_all(X, y, cv_folds=3)
    trainer.save_models()
    
    # Quick eval on 2024-25
    eval_games = df[(df['date'] >= '2024-10-22') & (df['date'] <= '2025-06-30')].sort_values('date')
    
    # Re-warm state
    world_state2 = RunningWorldState()
    past = df[df['date'] < '2024-10-22'].sort_values('date')
    for _, row in past.iterrows():
        world_state2.update(row['home'], row['away'], row['date'], row['home_win'],
                           row.get('home_pts'), row.get('away_pts'))
    
    correct = 0
    total = 0
    for _, row in eval_games.iterrows():
        features = world_state2.get_team_features(row['home'], row['away'], row['date'])
        X_pred = pd.DataFrame([features]).reindex(columns=trainer.feature_names, fill_value=0.0)
        
        try:
            prob = trainer.predict_ensemble(X_pred)[0]
        except:
            prob = features.get('elo_win_prob', 0.5)
        
        pred = 1 if prob > 0.5 else 0
        if pred == row['home_win']:
            correct += 1
        total += 1
        
        world_state2.update(row['home'], row['away'], row['date'], row['home_win'],
                           row.get('home_pts'), row.get('away_pts'))
    
    acc = correct / total * 100
    print(f"\n  📊 2024-25 OOS Accuracy: {correct}/{total} = {acc:.2f}%")
    return acc, metrics


if __name__ == "__main__":
    df = pd.read_csv("data/nba_games_enhanced.csv")
    df['date'] = pd.to_datetime(df['date'])
    
    results = {}
    for era in ['1996-10-01', '2004-10-01', '2014-10-01']:
        acc, _ = evaluate_with_era(df, era)
        results[era] = acc
    
    print("\n" + "=" * 60)
    print("📊 ERA COMPARISON RESULTS")
    print("=" * 60)
    for era, acc in results.items():
        print(f"  {era}: {acc:.2f}%")
    print(f"  Full history: 64.92% (from main v2 training)")
    print("=" * 60)
