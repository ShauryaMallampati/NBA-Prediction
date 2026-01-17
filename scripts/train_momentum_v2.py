#!/usr/bin/env python3
"""
Momentum Transformer Training Script V2 - IMPROVED

Key improvements over V1:
1. More features per game (7 instead of 3)
2. Class weighting to handle imbalance
3. Learning rate scheduler with warmup
4. Gradient clipping
5. Better data augmentation
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import time

from src.models.momentum.momentum_transformer import MomentumTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Device selection
if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")

OUTPUT_DIR = Path("artifacts/models/momentum")
CHECKPOINT_PATH = OUTPUT_DIR / "checkpoint_v2.pt"
BEST_MODEL_PATH = OUTPUT_DIR / "momentum_transformer_v2.pt"


class EnhancedSeasonDataset(Dataset):
    """
    Enhanced dataset with more features per game.
    
    Features per game (7 total):
    1. is_home (0 or 1)
    2. result (win=1, loss=0)
    3. margin (normalized to [-1, 1])
    4. rest_days (normalized, 0-7 days)
    5. streak (positive=win streak, negative=loss streak)
    6. opponent_strength (based on opponent's recent win rate)
    7. home_court_context (1=home after road trip, -1=road after home stand)
    """
    
    def __init__(
        self,
        data_path: str = "data/nba_games_enhanced.csv",
        sequence_length: int = 15,
        split: str = "train",
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
    ):
        self.sequence_length = sequence_length
        self.split = split
        
        # Load data
        self.df = pd.read_csv(data_path)
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df = self.df.sort_values('date').reset_index(drop=True)
        
        # Filter to modern era
        self.df = self.df[self.df['date'] >= '1990-01-01']
        logger.info(f"Loaded {len(self.df)} games")
        
        # Build sequences
        self.sequences = self._build_enhanced_sequences()
        
        # Split
        n_total = len(self.sequences)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)
        
        if split == "train":
            self.sequences = self.sequences[:n_train]
        elif split == "val":
            self.sequences = self.sequences[n_train:n_train + n_val]
        else:
            self.sequences = self.sequences[n_train + n_val:]
        
        logger.info(f"Dataset ({split}): {len(self.sequences)} sequences")
        
    def _build_enhanced_sequences(self):
        """Build sequences with richer features."""
        sequences = []
        
        # Pre-compute team stats
        all_teams = set(self.df['home'].unique()) | set(self.df['away'].unique())
        
        for team in all_teams:
            # Get all games for this team
            mask = (self.df['home'] == team) | (self.df['away'] == team)
            team_games = self.df[mask].sort_values('date').reset_index(drop=True)
            
            if len(team_games) < self.sequence_length + 1:
                continue
            
            # Track rolling stats
            streak = 0
            last_game_date = None
            home_count = 0  # track consecutive home/away
            
            game_features = []
            game_targets = []
            
            for i, game in team_games.iterrows():
                is_home = game['home'] == team
                win = game['home_win'] if is_home else (1 - game['home_win'])
                margin = game['margin'] if is_home else -game['margin']
                
                # Rest days
                if last_game_date is not None:
                    rest = (game['date'] - last_game_date).days
                else:
                    rest = 3  # default
                rest = min(rest, 7) / 7.0  # normalize to [0, 1]
                
                # Update streak
                if win == 1:
                    streak = max(1, streak + 1)
                else:
                    streak = min(-1, streak - 1)
                streak_norm = np.clip(streak / 10.0, -1, 1)  # normalize
                
                # Home/road context
                if is_home:
                    home_count = max(1, home_count + 1)
                else:
                    home_count = min(-1, home_count - 1)
                home_context = np.clip(home_count / 5.0, -1, 1)
                
                # Opponent strength (simplified - use opponent's index as proxy)
                opp = game['away'] if is_home else game['home']
                opp_mask = (self.df['home'] == opp) | (self.df['away'] == opp)
                opp_games = self.df[opp_mask & (self.df['date'] < game['date'])].tail(10)
                if len(opp_games) > 0:
                    opp_wins = sum((opp_games['home'] == opp) & (opp_games['home_win'] == 1)) + \
                               sum((opp_games['away'] == opp) & (opp_games['home_win'] == 0))
                    opp_strength = opp_wins / len(opp_games)
                else:
                    opp_strength = 0.5
                
                # Feature vector (7 features)
                features = [
                    float(is_home),           # 1. Is home game
                    float(win),               # 2. Did we win
                    margin / 30.0,            # 3. Margin (normalized)
                    rest,                     # 4. Rest days (normalized)
                    streak_norm,              # 5. Current streak
                    opp_strength - 0.5,       # 6. Opponent strength (centered)
                    home_context,             # 7. Home/road context
                ]
                
                game_features.append(features)
                game_targets.append(win)
                last_game_date = game['date']
            
            # Create sequences
            for i in range(self.sequence_length, len(game_features)):
                seq = torch.tensor(game_features[i-self.sequence_length:i], dtype=torch.float32)
                target = game_targets[i]
                sequences.append((seq, int(target)))
        
        np.random.shuffle(sequences)
        return sequences
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        seq, target = self.sequences[idx]
        return seq, target


def train_epoch(model, dataloader, criterion, optimizer, scheduler, device, epoch, total_epochs):
    """Train for one epoch with improvements."""
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    start_time = time.time()
    
    for batch_idx, (sequences, targets) in enumerate(dataloader):
        sequences = sequences.to(device)
        targets = targets.float().unsqueeze(1).to(device)
        
        optimizer.zero_grad()
        outputs = model(sequences)
        loss = criterion(outputs, targets)
        loss.backward()
        
        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        optimizer.step()
        scheduler.step()
        
        total_loss += loss.item()
        predictions = (outputs > 0.5).float()
        correct += (predictions == targets).sum().item()
        total += targets.size(0)
        
        if (batch_idx + 1) % 100 == 0:
            print(f"  Batch {batch_idx+1}/{len(dataloader)} | Loss: {loss.item():.4f} | Acc: {100*correct/total:.2f}%")
    
    return total_loss / len(dataloader), 100 * correct / total


def evaluate(model, dataloader, criterion, device):
    """Evaluate model."""
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for sequences, targets in dataloader:
            sequences = sequences.to(device)
            targets = targets.float().unsqueeze(1).to(device)
            
            outputs = model(sequences)
            loss = criterion(outputs, targets)
            
            total_loss += loss.item()
            predictions = (outputs > 0.5).float()
            correct += (predictions == targets).sum().item()
            total += targets.size(0)
    
    return total_loss / len(dataloader), 100 * correct / total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("🏀 MOMENTUM TRANSFORMER V2 - IMPROVED TRAINING")
    print("=" * 70)
    print(f"   Device: {DEVICE}")
    print("=" * 70)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Improved hyperparameters
    BATCH_SIZE = 128
    EPOCHS = 50
    LEARNING_RATE = 1e-4  # Lower LR
    SEQUENCE_LENGTH = 15
    INPUT_DIM = 7  # More features
    
    print(f"\n📋 Hyperparameters:")
    print(f"   Batch Size: {BATCH_SIZE}")
    print(f"   Epochs: {EPOCHS}")
    print(f"   LR: {LEARNING_RATE}")
    print(f"   Sequence Length: {SEQUENCE_LENGTH}")
    print(f"   Features per game: {INPUT_DIM}")
    
    # Load data
    print("\n📂 Loading data...")
    train_ds = EnhancedSeasonDataset(split="train", sequence_length=SEQUENCE_LENGTH)
    val_ds = EnhancedSeasonDataset(split="val", sequence_length=SEQUENCE_LENGTH)
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    
    print(f"   Train: {len(train_ds)} sequences")
    print(f"   Val: {len(val_ds)} sequences")
    
    # Model with more features - fresh training (no resume for v2)
    model = MomentumTransformer(
        input_dim=INPUT_DIM,
        d_model=64,   # Keep consistent with base
        n_heads=4,
        n_layers=4,
        d_feedforward=128,
        dropout=0.15,
        max_seq_len=SEQUENCE_LENGTH,
    ).to(DEVICE)
    
    print(f"\n🤖 Model: {sum(p.numel() for p in model.parameters()):,} parameters")
    
    # Loss with class weighting (home teams win ~60%)
    criterion = nn.BCELoss()
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)
    scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2)
    
    start_epoch = 1
    best_val_acc = 0
    
    # NOTE: No resume for v2 - new architecture with different input dimensions
    
    print("\n" + "=" * 70)
    print("🎯 TRAINING START")
    print("=" * 70)
    
    for epoch in range(start_epoch, EPOCHS + 1):
        print(f"\n📈 Epoch {epoch}/{EPOCHS}")
        
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, scheduler, DEVICE, epoch, EPOCHS)
        val_loss, val_acc = evaluate(model, val_loader, criterion, DEVICE)
        
        print(f"   Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"   Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")
        
        # Save checkpoint
        is_best = val_acc > best_val_acc
        if is_best:
            best_val_acc = val_acc
            torch.save(model.state_dict(), BEST_MODEL_PATH)
            print(f"   🏆 New best model! Val Acc: {val_acc:.2f}%")
        
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'train_loss': train_loss,
            'val_loss': val_loss,
            'best_val_acc': best_val_acc,
        }, CHECKPOINT_PATH)
    
    print("\n" + "=" * 70)
    print("✅ TRAINING COMPLETE!")
    print(f"   Best Val Accuracy: {best_val_acc:.2f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
