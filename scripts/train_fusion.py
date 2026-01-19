#!/usr/bin/env python3
"""
Train Gated Fusion Model for Multi-Modal NBA Prediction.

This script trains the learnable fusion network that combines outputs
from all modalities (Ensemble, Vision, Audio, Flow, Chemistry, Momentum, PBP).

Usage:
    poetry run python scripts/train_fusion.py --epochs 30 --batch_size 64
    poetry run python scripts/train_fusion.py --resume  # Resume from checkpoint

Training Data:
    Uses predictions from the 4-modality system on the 2023-24 season
    to train the fusion weights.
"""

import argparse
import json
import logging
import sys
import time
import random
from pathlib import Path
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.fusion.learnable_fusion import GatedFusion

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Training cutoff
TRAINING_CUTOFF = "2024-10-01"

# Output directory
OUTPUT_DIR = Path("artifacts/models/fusion")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class FusionDataset(Dataset):
    """
    Dataset for training the fusion model.
    
    Each sample contains:
    - Modality outputs: [base_prob, vis_Δ, aud_Δ, flow_Δ, chem_Δ, mom_Δ, pbp_Δ]
    - Label: actual home win (0 or 1)
    """
    
    def __init__(self, data_path: Path = None):
        self.samples = []
        
        if data_path and data_path.exists():
            if data_path.suffix == '.csv':
                import pandas as pd
                df = pd.read_csv(data_path)
                logger.info(f"Loaded {len(df)} samples from CSV")
                for _, row in df.iterrows():
                    self.samples.append({
                        'base_prob': float(row['base_prob']),
                        'vision_delta': float(row['vis_delta']),
                        'audio_delta': float(row['aud_delta']),
                        'flow_delta': float(row['flow_delta']),
                        'chemistry_delta': float(row['chem_delta']),
                        'momentum_delta': float(row['mom_delta']),
                        'pbp_delta': float(row['pbp_delta']),
                        'label': int(row['home_win']),
                    })
            else:
                with open(data_path, 'r') as f:
                    raw_data = json.load(f)
                
                for game in raw_data.get('games', []):
                    # Extract modality outputs
                    sample = {
                        'base_prob': game.get('predicted_prob', 0.5),
                        'vision_delta': (game.get('home_vision_score', 0.5) - 0.5) * 0.15,
                        'audio_delta': 0.0,
                        'flow_delta': 0.0,
                        'chemistry_delta': game.get('chemistry_delta', 0.0),
                        'momentum_delta': game.get('momentum_delta', 0.0),
                        'pbp_delta': 0.0,
                        'label': game.get('actual_home_win', 0),
                    }
                    self.samples.append(sample)
        else:
            # Generate synthetic training data for initial development
            logger.warning("No training data found. Using synthetic data.")
            self._generate_synthetic_data(500)
    
    def _generate_synthetic_data(self, n_samples: int):
        """Generate synthetic training data for development."""
        for _ in range(n_samples):
            # Generate realistic-ish modality outputs
            base_prob = random.uniform(0.3, 0.7)
            
            # True home win probability (unknown, simulate)
            true_prob = base_prob + random.gauss(0, 0.1)
            true_prob = max(0.1, min(0.9, true_prob))
            
            # Generate deltas that correlate with true outcome
            vision_delta = random.gauss(0, 0.02)
            audio_delta = random.gauss(0, 0.01)
            flow_delta = random.gauss(0, 0.01)
            chemistry_delta = random.gauss(0, 0.02)
            momentum_delta = random.gauss(0, 0.02)
            pbp_delta = random.gauss(0, 0.01)
            
            # Sample outcome
            label = 1 if random.random() < true_prob else 0
            
            self.samples.append({
                'base_prob': base_prob,
                'vision_delta': vision_delta,
                'audio_delta': audio_delta,
                'flow_delta': flow_delta,
                'chemistry_delta': chemistry_delta,
                'momentum_delta': momentum_delta,
                'pbp_delta': pbp_delta,
                'label': label,
            })
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        s = self.samples[idx]
        x = torch.tensor([
            s['base_prob'],
            s['vision_delta'],
            s['audio_delta'],
            s['flow_delta'],
            s['chemistry_delta'],
            s['momentum_delta'],
            s['pbp_delta'],
        ], dtype=torch.float32)
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
    parser = argparse.ArgumentParser(description="Train Gated Fusion Model")
    parser.add_argument("--epochs", type=int, default=30, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--hidden_dim", type=int, default=32, help="Hidden dimension")
    parser.add_argument("--dropout", type=float, default=0.1, help="Dropout rate")
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
    dataset = FusionDataset(data_path)
    
    # Train/val split (80/20)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
    
    logger.info(f"📊 Dataset: {len(dataset)} samples (train={train_size}, val={val_size})")
    
    # Model
    model = GatedFusion(
        n_modalities=7,
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
        checkpoints = sorted(OUTPUT_DIR.glob("gated_fusion_epoch*.pt"))
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
        
        # Train
        train_loss = train_epoch(model, train_loader, criterion, optimizer, device)
        
        # Evaluate
        val_acc = evaluate(model, val_loader, device)
        
        epoch_time = time.time() - start_time
        
        # Log
        is_best = val_acc > best_acc
        if is_best:
            best_acc = val_acc
        
        logger.info(f"[Epoch {epoch+1}/{args.epochs}] "
                   f"Loss: {train_loss:.4f} | Val Acc: {val_acc:.2%} | "
                   f"Best: {best_acc:.2%} | Time: {epoch_time:.1f}s"
                   f"{' ⭐' if is_best else ''}")
        
        # Save checkpoint every 5 epochs
        if (epoch + 1) % 5 == 0 or is_best:
            checkpoint = {
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_acc': best_acc,
                'n_modalities': 7,
                'hidden_dim': args.hidden_dim,
                'training_cutoff': TRAINING_CUTOFF,
            }
            
            # Save epoch checkpoint
            ckpt_path = OUTPUT_DIR / f"gated_fusion_epoch{epoch+1}.pt"
            torch.save(checkpoint, ckpt_path)
            
            # Save best model
            if is_best:
                best_path = OUTPUT_DIR / "gated_fusion.pt"
                torch.save(checkpoint, best_path)
                logger.info(f"   💾 Saved best model: {best_path}")
    
    logger.info(f"\n✅ Training complete! Best accuracy: {best_acc:.2%}")
    logger.info(f"   Model saved to: {OUTPUT_DIR / 'gated_fusion.pt'}")


if __name__ == "__main__":
    main()
