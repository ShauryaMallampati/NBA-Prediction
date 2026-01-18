"""
Season Sequence Dataset for Momentum Transformer.

Converts team game histories into tokenized sequences for Transformer training.
Each "token" represents a single game with features like Win/Loss, Margin, etc.
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
    Dataset that creates sequences of games for each team.
    
    Research Motivation:
    Unlike standard ML features (rolling averages), a Transformer can learn
    complex patterns like "after 2 losses, this team usually bounces back strongly".
    
    Each sequence is: [Game_t-N, Game_t-N+1, ..., Game_t-1] -> Predict Game_t
    """
    
    def __init__(
        self,
        data_path: str = "data/nba_games_enhanced.csv",
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
        
        # Load data
        self.data_path = Path(data_path)
        if not self.data_path.exists():
            logger.warning(f"Data file not found: {data_path}. Run scripts/process_game_data.py first!")
            raise FileNotFoundError(f"Missing data file: {data_path}")
        
        self.df = pd.read_csv(data_path)
        
        # Filter by max_date if provided
        if max_date:
            self.df['date'] = pd.to_datetime(self.df['date'])
            self.df = self.df[self.df['date'] < max_date]
            logger.info(f"📅 Filtered dataset to games before {max_date}")
            
        logger.info(f"Loaded {len(self.df)} games from {data_path}")
        
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
        """Create synthetic game data for development/testing."""
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
                    
                    # Feature vector: [is_home, win, normalized_margin]
                    features = [
                        float(is_home),
                        float(win),
                        margin / 50.0,  # Normalize margin to ~[-0.5, 0.5]
                    ]
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
        return 3  # is_home, win, margin


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
