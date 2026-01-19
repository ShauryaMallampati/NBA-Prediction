#!/usr/bin/env python3
"""
Train Audio Crowd Classifier for Multi-Modal NBA Prediction.

This script trains a classifier on audio features extracted from
highlight videos to predict home-team momentum from crowd noise.

Usage:
    poetry run python scripts/train_audio.py --epochs 20 --batch_size 32
    poetry run python scripts/train_audio.py --resume  # Resume from checkpoint

Training Data:
    Extracted audio features from pre-October 2024 highlight videos.
"""

import argparse
import json
import logging
import sys
import time
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Training cutoff
TRAINING_CUTOFF = "2024-10-01"

# Output directory
OUTPUT_DIR = Path("artifacts/models/audio")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class AudioClassifier(nn.Module):
    """
    Simple MLP classifier for audio features.
    
    Input: 4 audio features (mean_loudness, max_loudness, num_peaks, peak_std)
    Output: 1 logit for home win probability
    """
    
    def __init__(self, input_dim: int = 4, hidden_dim: int = 16, dropout: float = 0.2):
        super().__init__()
        
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )
    
    def forward(self, x):
        return self.net(x)


class AudioDataset(Dataset):
    """
    Dataset for training the audio classifier.
    
    Each sample contains:
    - Audio features: [mean_loudness, max_loudness, num_peaks, peak_std]
    - Label: home win (0 or 1)
    """
    
    def __init__(self, data_path: Path = None):
        self.samples = []
        
        if data_path and data_path.exists():
            with open(data_path, 'r') as f:
                raw_data = json.load(f)
            
            for entry in raw_data:
                self.samples.append({
                    'features': entry['features'],
                    'label': entry['home_win'],
                })
        else:
            # Generate synthetic training data
            logger.warning("No training data found. Using synthetic data.")
            self._generate_synthetic_data(300)
    
    def _generate_synthetic_data(self, n_samples: int):
        """Generate synthetic training data."""
        for _ in range(n_samples):
            # Home games have louder crowds (on average)
            is_home_win = random.random() < 0.55  # Home advantage
            
            # Generate features with some correlation to outcome
            base_loudness = 0.05 + random.uniform(0, 0.1)
            if is_home_win:
                # Winning home team = louder crowd
                mean_loudness = base_loudness + random.uniform(0.02, 0.05)
                max_loudness = mean_loudness * (1.5 + random.uniform(0, 0.5))
                num_peaks = random.randint(20, 60)
            else:
                # Losing home team = quieter crowd
                mean_loudness = base_loudness
                max_loudness = mean_loudness * (1.2 + random.uniform(0, 0.3))
                num_peaks = random.randint(10, 40)
            
            peak_std = random.uniform(0.01, 0.05)
            
            self.samples.append({
                'features': [mean_loudness, max_loudness, num_peaks, peak_std],
                'label': 1 if is_home_win else 0,
            })
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        s = self.samples[idx]
        x = torch.tensor(s['features'], dtype=torch.float32)
        y = torch.tensor([s['label']], dtype=torch.float32)
        return x, y


def train_epoch(model, dataloader, criterion, optimizer, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0.0
    n_batches = 0
    
    for x, y in dataloader:
        x, y = x.to(device), y.to(device)
        
        optimizer.zero_grad()
        logits = model(x)
        loss = criterion(logits, y)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        n_batches += 1
    
    return total_loss / n_batches


def evaluate(model, dataloader, device):
    """Evaluate model accuracy."""
    model.eval()
    correct = 0
    total = 0
    
    with torch.no_grad():
        for x, y in dataloader:
            x, y = x.to(device), y.to(device)
            probs = torch.sigmoid(model(x))
            preds = (probs > 0.5).float()
            correct += (preds == y).sum().item()
            total += y.size(0)
    
    return correct / total if total > 0 else 0.0


def main():
    parser = argparse.ArgumentParser(description="Train Audio Classifier")
    parser.add_argument("--epochs", type=int, default=20, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--hidden_dim", type=int, default=16, help="Hidden dimension")
    parser.add_argument("--dropout", type=float, default=0.2, help="Dropout rate")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--data_path", type=str, default=None,
                       help="Path to training data JSON")
    args = parser.parse_args()
    
    # Set seeds
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    
    # Device
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    logger.info(f"🔧 Device: {device}")
    logger.info(f"🔧 Training cutoff: {TRAINING_CUTOFF}")
    
    # Dataset
    data_path = Path(args.data_path) if args.data_path else None
    dataset = AudioDataset(data_path)
    
    # Train/val split
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    
    logger.info(f"📊 Dataset: {len(dataset)} samples (train={train_size}, val={val_size})")
    
    # Model
    model = AudioClassifier(
        input_dim=4,
        hidden_dim=args.hidden_dim,
        dropout=args.dropout,
    ).to(device)
    
    # Loss and optimizer
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    
    # Resume
    start_epoch = 0
    best_acc = 0.0
    
    if args.resume:
        checkpoints = sorted(OUTPUT_DIR.glob("audio_classifier_epoch*.pt"))
        if checkpoints:
            latest = checkpoints[-1]
            checkpoint = torch.load(latest, map_location=device)
            model.load_state_dict(checkpoint['model_state_dict'])
            optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            start_epoch = checkpoint.get('epoch', 0) + 1
            best_acc = checkpoint.get('best_acc', 0.0)
            logger.info(f"✅ Resumed from {latest} (epoch {start_epoch})")
    
    # Training loop
    logger.info(f"🚀 Starting training for {args.epochs} epochs...")
    
    for epoch in range(start_epoch, args.epochs):
        start_time = time.time()
        
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        val_acc = evaluate(model, val_loader, device)
        
        epoch_time = time.time() - start_time
        
        is_best = val_acc > best_acc
        if is_best:
            best_acc = val_acc
        
        logger.info(f"[Epoch {epoch+1}/{args.epochs}] "
                   f"Loss: {train_loss:.4f} | Val Acc: {val_acc:.2%} | "
                   f"Best: {best_acc:.2%} | Time: {epoch_time:.1f}s"
                   f"{' ⭐' if is_best else ''}")
        
        # Save checkpoint
        if (epoch + 1) % 5 == 0 or is_best:
            checkpoint = {
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_acc': best_acc,
                'training_cutoff': TRAINING_CUTOFF,
            }
            
            ckpt_path = OUTPUT_DIR / f"audio_classifier_epoch{epoch+1}.pt"
            torch.save(checkpoint, ckpt_path)
            
            if is_best:
                best_path = OUTPUT_DIR / "crowd_classifier.pt"
                torch.save(checkpoint, best_path)
                logger.info(f"   💾 Saved best model: {best_path}")
    
    logger.info(f"\n✅ Training complete! Best accuracy: {best_acc:.2%}")
    logger.info(f"   Model saved to: {OUTPUT_DIR / 'crowd_classifier.pt'}")


if __name__ == "__main__":
    main()
