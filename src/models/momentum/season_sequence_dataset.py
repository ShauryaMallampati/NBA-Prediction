"""
"""Dataset that turns game histories into sequences for the Transformer.

Each game becomes a token with features like Win/Loss, margin, rest, etc.
The Transformer learns patterns across sequences of games.

Why this matters: Standard ML uses rolling averages, but a Transformer can
learn more subtle patterns like "after 2 bad losses, teams often rally".
"""

import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset
from pathlib import Path
from typing import List, Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SeasonSequenceDataset(Dataset):
    """
    """Create sequences of games for training the Transformer.
    
    Research idea: Instead of just averaging stats, let the model learn
    complex momentum patterns like "team bounces back after 2 losses".
    
    Each sequence: [Game_t-N, Game_t-N+1, ..., Game_t-1] -> Predict Game_t
    """
    
    def __init__(
        self,
        data_path: str = "artifacts/features/pregame_full.parquet",
        sequence_length: int = 10,
        min_games: int = 15,
        split: str = "train",  # train, val, test
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        max_date: Optional[str] = None
    ):
        """
        Args:
            max_date: Optional cutoff date 'YYYY-MM-DD'. Games after this are discarded.
        """
        self.sequence_length = sequence_length
        self.split = split
        
        # Load data (Parquet or CSV)
        self.data_path = Path(data_path)
        if not self.data_path.exists():
            # Fallback to CSV if parquet missing (but warn)
            csv_path = Path("data/nba_games_enhanced.csv")
            if csv_path.exists():
                logger.warning(f"Parquet features not found, falling back to basic CSV: {csv_path}")
                self.df = pd.read_csv(csv_path)
                # Basic fill for missing columns if using raw CSV
                if 'home_rest_days' not in self.df.columns: self.df['home_rest_days'] = 0
                if 'home_win_streak' not in self.df.columns: self.df['home_win_streak'] = 0
                if 'home_fatigue_score' not in self.df.columns: self.df['home_fatigue_score'] = 0
            else:
                raise FileNotFoundError(f"Missing data file: {data_path}")
        else:
            self.df = pd.read_parquet(self.data_path)
            # Normalize column names: ensure we use home/away consistently
            if 'home_team' in self.df.columns and 'home' not in self.df.columns:
                self.df = self.df.rename(columns={'home_team': 'home', 'away_team': 'away'})
            
            # Ensure margin exists
            if 'margin' not in self.df.columns and 'home_pts' in self.df.columns:
                self.df['margin'] = (self.df['home_pts'] - self.df['away_pts']).abs()
        
        # Filter by max_date if provided
        if max_date:
            self.df['date'] = pd.to_datetime(self.df['date'])
            self.df = self.df[self.df['date'] < max_date]
            logger.info(f"📅 Filtered dataset to games before {max_date}")
            
        logger.info(f"Loaded {len(self.df)} games from {self.data_path}")
        
        # Prepare sequences
        self.sequences = self._build_sequences(min_games)
        
        # Split data
        n_total = len(self.sequences)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)
        
        if split == "train":
            self.sequences = self.sequences[:n_train]
        elif split == "val":
            self.sequences = self.sequences[n_train:n_train + n_val]
        else:  # test
            self.sequences = self.sequences[n_train + n_val:]
        
        logger.info(f"SeasonSequenceDataset ({split}): {len(self.sequences)} sequences")
    
    def _create_synthetic_data(self) -> pd.DataFrame:
        """Generate fake game data for testing when we don't have real data yet."""
        np.random.seed(42)
        
        teams = ["LAL", "GSW", "BOS", "MIA", "PHX", "DEN", "MIL", "PHI"]
        n_games = 500
        
        rows = []
        for i in range(n_games):
            home = np.random.choice(teams)
            away = np.random.choice([t for t in teams if t != home])
            
            # Simulate game outcome
            home_strength = teams.index(home) / len(teams)  # Crude ranking
            away_strength = teams.index(away) / len(teams)
            home_win_prob = 0.55 + (away_strength - home_strength) * 0.3
            home_win = np.random.random() < home_win_prob
            
            margin = np.random.randint(1, 25) * (1 if home_win else -1)
            
            rows.append({
                "date": f"2024-{(i // 30) + 1:02d}-{(i % 28) + 1:02d}",
                "home": home,
                "away": away,
                "home_pts": 110 + margin // 2,
                "away_pts": 110 - margin // 2,
                "home_win": int(home_win),
                "margin": margin,
            })
        
        return pd.DataFrame(rows)
    
    def _build_sequences(self, min_games: int) -> List[Tuple[torch.Tensor, int]]:
        """
        Build game sequences for each team.
        
        Returns:
            List of (sequence_tensor, target_label) tuples
        """
        sequences = []
        
        # Get all unique teams
        all_teams = set(self.df['home'].unique()) | set(self.df['away'].unique())
        
        for team in all_teams:
            # Get all games for this team (home or away)
            team_games = self.df[
                (self.df['home'] == team) | (self.df['away'] == team)
            ].sort_values('date').reset_index(drop=True)
            
            if len(team_games) < min_games:
                continue
            
            # Build sequences
            for i in range(self.sequence_length, len(team_games)):
                seq_games = team_games.iloc[i - self.sequence_length:i]
                target_game = team_games.iloc[i]
                
                # Extract features for each game in sequence
                seq_features = []
                for _, game in seq_games.iterrows():
                    is_home = game['home'] == team
                    win = game['home_win'] if is_home else (1 - game['home_win'])
                    margin = game['margin'] if is_home else -game['margin']
                    
                    # Feature vector: [is_home, win, normalized_margin, rest, streak, fatigue, elo_diff]
                    is_home_val = float(is_home)
                    win_val = float(win)
                    margin_val = margin / 50.0
                    
                    # Enhanced features (handle home/away mapping)
                    if is_home:
                        rest = game.get('home_rest_days', 0) / 7.0
                        streak = game.get('home_win_streak', 0) / 10.0
                        fatigue = game.get('home_fatigue_score', 0) / 5.0
                        elo = game.get('elo_p_home', 0.5)
                    else:
                        rest = game.get('away_rest_days', 0) / 7.0
                        streak = game.get('away_win_streak', 0) / 10.0
                        fatigue = game.get('away_fatigue_score', 0) / 5.0
                        elo = 1.0 - game.get('elo_p_home', 0.5)

                    features = [
                        is_home_val,
                        win_val,
                        margin_val,
                        rest,
                        streak,
                        fatigue,
                        elo
                    ]
                    
                    # Ensure no NaNs
                    features = [0.0 if np.isnan(x) else x for x in features]
                    seq_features.append(features)
                
                # Target: did team win next game?
                is_home_target = target_game['home'] == team
                target = target_game['home_win'] if is_home_target else (1 - target_game['home_win'])
                
                seq_tensor = torch.tensor(seq_features, dtype=torch.float32)
                sequences.append((seq_tensor, int(target)))
        
        # Shuffle sequences
        np.random.shuffle(sequences)
        
        return sequences
    
    def __len__(self) -> int:
        return len(self.sequences)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        seq, target = self.sequences[idx]
        return seq, target
    
    @property
    def feature_dim(self) -> int:
        """Number of features per game token."""
        return 7  # is_home, win, margin, rest, streak, fatigue, elo_win_prob


def get_momentum_dataloaders(
    batch_size: int = 32,
    sequence_length: int = 10,
) -> Tuple[torch.utils.data.DataLoader, torch.utils.data.DataLoader, torch.utils.data.DataLoader]:
    """
    Convenience function to get train/val/test dataloaders.
    """
    train_ds = SeasonSequenceDataset(split="train", sequence_length=sequence_length)
    val_ds = SeasonSequenceDataset(split="val", sequence_length=sequence_length)
    test_ds = SeasonSequenceDataset(split="test", sequence_length=sequence_length)
    
    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = torch.utils.data.DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    test_loader = torch.utils.data.DataLoader(test_ds, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader, test_loader
