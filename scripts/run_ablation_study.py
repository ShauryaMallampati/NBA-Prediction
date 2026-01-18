#!/usr/bin/env python3
"""
🔬 ABLATION STUDY FOR NBA WORLD MODEL
======================================
This script runs multiple experiments to measure each component's contribution.

Experiments:
1. Full Model: Ensemble + Momentum + Chemistry + Vision (baseline)
2. No Vision: Ensemble + Momentum + Chemistry
3. No Momentum: Ensemble + Chemistry + Vision
4. No Chemistry: Ensemble + Momentum + Vision
5. Ensemble Only: Just the base Ensemble model

Usage:
    poetry run python scripts/run_ablation_study.py --season 2024-25
    
Output:
    artifacts/evaluation/ablation/ablation_results.json
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.pregame.train_ensemble import EnsembleTrainer
from src.models.chemistry_gnn import get_chemistry_model  
from src.models.momentum.momentum_transformer import MomentumAnalytics
from src.common.features import RunningWorldState

# Configuration
RESULTS_DIR = Path("artifacts/evaluation/ablation")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

class AblationStudy:
    """Run ablation experiments on the World Model."""
    
    def __init__(self, model_dir: str = "artifacts/models/historical_2024"):
        self.model_dir = model_dir
        print(f"📦 Loading models from {model_dir}...")
        
        # Load Ensemble
        self.ensemble = EnsembleTrainer(output_dir=model_dir)
        self.ensemble.load_models()
        print("✅ Ensemble loaded")
        
        # Load Chemistry
        self.chemistry = get_chemistry_model()
        print(f"✅ Chemistry loaded: {self.chemistry.loaded}")
        
        # Load Momentum
        momentum_path = Path(model_dir) / "momentum" / "momentum_transformer.pt"
        self.momentum = MomentumAnalytics(model_path=str(momentum_path))
        print(f"✅ Momentum loaded: {self.momentum.loaded}")
        
        # Load historical data
        self.games_df = pd.read_csv("data/nba_games_enhanced.csv")
        self.games_df['date'] = pd.to_datetime(self.games_df['date'])
        print(f"✅ Historical data: {len(self.games_df)} games")
        
        # Pre-computed vision scores (from full model run)
        self.vision_cache = self._load_vision_cache()
        
        # World State
        self.world_state = RunningWorldState()
        
    def _load_vision_cache(self) -> dict:
        """Load vision scores from full model run."""
        cache = {}
        full_results_path = Path("artifacts/evaluation/real_video/real_video_eval_2024-25.json")
        partial_path = Path("artifacts/evaluation/real_video/real_video_eval_2024-25_partial.json")
        
        path = full_results_path if full_results_path.exists() else partial_path
        
        if path.exists():
            with open(path) as f:
                data = json.load(f)
                games = data.get('games', data.get('results', []))
                for g in games:
                    key = f"{g['date']}_{g['home']}_{g['away']}"
                    cache[key] = g.get('home_vision_score', 0.5)
            print(f"✅ Vision cache loaded: {len(cache)} games")
        else:
            print("⚠️ No vision cache found - will use neutral (0.5)")
        
        return cache
    
    def predict_game(self, home: str, away: str, date: str,
                     use_momentum: bool = True,
                     use_chemistry: bool = True,
                     use_vision: bool = True) -> float:
        """Run prediction with optional component disabling."""
        
        # 1. Get features from world state
        features = self.world_state.get_team_features(home, away, date)
        
        # 2. ENSEMBLE (always on - it's the base)
        X = pd.DataFrame([features])
        X_input = X[self.ensemble.feature_names]
        base_prob = self.ensemble.predict_ensemble(X_input)[0]
        
        # 3. MOMENTUM (optional)
        if use_momentum:
            momentum_delta, _ = self.momentum.get_matchup_momentum_delta(
                home, away, current_date=date, games_df=self.games_df
            )
        else:
            momentum_delta = 0.0
        
        # 4. CHEMISTRY (optional)
        if use_chemistry:
            chem_diff = self.chemistry.get_chemistry_differential(
                home, away, current_date=date, games_df=self.games_df
            )
            chem_delta = chem_diff * 0.1
        else:
            chem_delta = 0.0
        
        # 5. VISION (optional - use cached scores)
        if use_vision:
            key = f"{date}_{home}_{away}"
            home_vision = self.vision_cache.get(key, 0.5)
            # For away team, we'd need a separate lookup, but for simplicity use 0.5
            vision_delta = (home_vision - 0.5) * 0.15
        else:
            vision_delta = 0.0
        
        # LATE FUSION
        final_prob = base_prob + momentum_delta + chem_delta + vision_delta
        return np.clip(final_prob, 0.05, 0.95)
    
    def run_experiment(self, season: str, experiment_name: str,
                       use_momentum: bool, use_chemistry: bool, use_vision: bool) -> dict:
        """Run a single ablation experiment."""
        
        print(f"\n{'='*60}")
        print(f"🔬 EXPERIMENT: {experiment_name}")
        print(f"   Momentum: {'✅' if use_momentum else '❌'}")
        print(f"   Chemistry: {'✅' if use_chemistry else '❌'}")
        print(f"   Vision: {'✅' if use_vision else '❌'}")
        print('='*60)
        
        # Reset world state
        self.world_state = RunningWorldState()
        
        # Get games for this season
        if season == "2025-26":
            games = self.games_df[(self.games_df['date'] >= '2025-10-21') & 
                                   (self.games_df['date'] <= '2026-06-30')]
        else:
            games = self.games_df[(self.games_df['date'] >= '2024-10-22') & 
                                   (self.games_df['date'] <= '2025-06-30')]
        
        games = games.sort_values('date').reset_index(drop=True)
        print(f"📅 Evaluating {len(games)} games")
        
        # Warm up state
        cutoff = games['date'].min()
        warmup_games = self.games_df[self.games_df['date'] < cutoff].sort_values('date')
        for _, row in warmup_games.iterrows():
            self.world_state.update(row['home'], row['away'], row['date'], row['home_win'])
        print(f"🔥 State warmed up")
        
        # Run predictions
        correct = 0
        results = []
        
        for idx, row in games.iterrows():
            home, away = row['home'], row['away']
            date = row['date'].strftime('%Y-%m-%d')
            actual = int(row['home_win'])
            
            prob = self.predict_game(home, away, date,
                                     use_momentum=use_momentum,
                                     use_chemistry=use_chemistry,
                                     use_vision=use_vision)
            
            predicted = 1 if prob > 0.5 else 0
            is_correct = predicted == actual
            if is_correct:
                correct += 1
            
            # Update state after prediction
            self.world_state.update(home, away, date, actual)
            
            results.append({
                'date': date,
                'home': home,
                'away': away,
                'predicted_prob': round(prob, 4),
                'predicted': predicted,
                'actual': actual,
                'correct': is_correct
            })
            
            # Progress update every 100 games
            if len(results) % 100 == 0:
                acc = correct / len(results) * 100
                print(f"   Progress: {len(results)}/{len(games)} | Accuracy: {acc:.1f}%")
        
        accuracy = correct / len(results) * 100
        print(f"\n🏆 {experiment_name}: {accuracy:.2f}% ({correct}/{len(results)})")
        
        return {
            'experiment': experiment_name,
            'use_momentum': use_momentum,
            'use_chemistry': use_chemistry,
            'use_vision': use_vision,
            'total_games': len(results),
            'correct': correct,
            'accuracy': round(accuracy, 2),
            'games': results
        }
    
    def run_all_experiments(self, season: str = "2024-25") -> dict:
        """Run all ablation experiments."""
        
        experiments = [
            ("Full Model", True, True, True),
            ("No Vision", True, True, False),
            ("No Momentum", False, True, True),
            ("No Chemistry", True, False, True),
            ("Ensemble Only", False, False, False),
        ]
        
        all_results = {
            'season': season,
            'timestamp': datetime.now().isoformat(),
            'experiments': []
        }
        
        for name, mom, chem, vis in experiments:
            result = self.run_experiment(season, name,
                                         use_momentum=mom,
                                         use_chemistry=chem,
                                         use_vision=vis)
            # Don't store all game details for summary
            summary = {k: v for k, v in result.items() if k != 'games'}
            all_results['experiments'].append(summary)
            
            # Save individual experiment
            exp_file = RESULTS_DIR / f"ablation_{name.lower().replace(' ', '_')}_{season}.json"
            with open(exp_file, 'w') as f:
                json.dump(result, f, indent=2)
        
        # Print summary table
        print("\n" + "="*70)
        print("📊 ABLATION STUDY SUMMARY")
        print("="*70)
        print(f"{'Experiment':<20} {'Accuracy':>10} {'Delta':>10}")
        print("-"*70)
        
        baseline_acc = all_results['experiments'][0]['accuracy']
        for exp in all_results['experiments']:
            delta = exp['accuracy'] - baseline_acc
            delta_str = f"{delta:+.2f}%" if delta != 0 else "baseline"
            print(f"{exp['experiment']:<20} {exp['accuracy']:>9.2f}% {delta_str:>10}")
        
        print("="*70)
        
        # Save summary
        summary_file = RESULTS_DIR / f"ablation_summary_{season}.json"
        with open(summary_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n📁 Results saved to {summary_file}")
        
        return all_results


def main():
    parser = argparse.ArgumentParser(description='Run ablation study')
    parser.add_argument('--season', type=str, default='2024-25',
                        choices=['2024-25', '2025-26'],
                        help='Season to evaluate')
    args = parser.parse_args()
    
    study = AblationStudy()
    study.run_all_experiments(args.season)


if __name__ == "__main__":
    main()
