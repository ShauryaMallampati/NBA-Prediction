#!/usr/bin/env python3
"""
Momentum Transformer Training Script.

Trains the novel Momentum Transformer on team game sequences.
Supports resuming from checkpoints.

Usage:
    poetry run python scripts/train_momentum_transformer.py           # Fresh start
    poetry run python scripts/train_momentum_transformer.py --resume  # Resume from checkpoint
"""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import logging
from datetime import datetime
import time

from src.models.momentum.momentum_transformer import MomentumTransformer
from src.models.momentum.season_sequence_dataset import SeasonSequenceDataset

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
CHECKPOINT_PATH = OUTPUT_DIR / "checkpoint_latest.pt"
BEST_MODEL_PATH = OUTPUT_DIR / "momentum_transformer.pt"


def train_epoch(model, dataloader, criterion, optimizer, device, epoch, total_epochs):
    """Train for one epoch with verbose progress logging."""
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    num_batches = len(dataloader)
    
    start_time = time.time()
    
    print(f"\n{'='*60}")
    print(f"📈 EPOCH {epoch}/{total_epochs} - TRAINING")
    print(f"{'='*60}")
    
    for batch_idx, (sequences, targets) in enumerate(dataloader):
        sequences = sequences.to(device)
        targets = targets.float().to(device)
        
        optimizer.zero_grad()
        outputs = model(sequences)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        predictions = (outputs > 0.5).float()
        batch_correct = (predictions == targets).sum().item()
        correct += batch_correct
        total += targets.size(0)
        
        # Running accuracy
        running_acc = correct / total * 100
        
        # Log progress every 50 batches for more visibility
        if (batch_idx + 1) % 50 == 0:
            elapsed = time.time() - start_time
            batches_per_sec = (batch_idx + 1) / elapsed
            remaining = (num_batches - batch_idx - 1) / batches_per_sec
            
            print(f"  📊 Batch {batch_idx + 1:>5}/{num_batches} "
                  f"({100*(batch_idx+1)/num_batches:>5.1f}%) "
                  f"| Loss: {loss.item():.4f} "
                  f"| Acc: {running_acc:.2f}% "
                  f"| Speed: {batches_per_sec:.1f} batch/s "
                  f"| ETA: {remaining/60:.1f}min")
    
    epoch_time = time.time() - start_time
    final_acc = correct / total * 100
    avg_loss = total_loss / len(dataloader)
    
    print(f"\n  ✅ Epoch {epoch} Complete!")
    print(f"     Train Loss: {avg_loss:.4f}")
    print(f"     Train Accuracy: {final_acc:.2f}%")
    print(f"     Time: {epoch_time:.1f}s ({epoch_time/60:.1f} min)")
    
    return avg_loss, final_acc, epoch_time



def evaluate(model, dataloader, criterion, device):
    """Evaluate model on validation/test set."""
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for sequences, targets in dataloader:
            sequences = sequences.to(device)
            targets = targets.float().to(device)
            
            outputs = model(sequences)
            loss = criterion(outputs, targets)
            
            total_loss += loss.item()
            predictions = (outputs > 0.5).float()
            correct += (predictions == targets).sum().item()
            total += targets.size(0)
    
    return total_loss / len(dataloader), correct / total * 100


def main():
    parser = argparse.ArgumentParser(description='Train Momentum Transformer')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--max_date', type=str, help='Cutoff date used for historical training (YYYY-MM-DD)')
    parser.add_argument('--output_dir', type=str, help='Custom output directory')
    args = parser.parse_args()
    
    # Configure Output Directory
    global OUTPUT_DIR, CHECKPOINT_PATH, BEST_MODEL_PATH
    if args.output_dir:
        OUTPUT_DIR = Path(args.output_dir)
        CHECKPOINT_PATH = OUTPUT_DIR / "checkpoint_latest.pt"
        BEST_MODEL_PATH = OUTPUT_DIR / "momentum_transformer.pt"
    
    print("\n" + "=" * 70)
    print("🏀 MOMENTUM TRANSFORMER TRAINING")
    print("=" * 70)
    print(f"   Device: {DEVICE}")
    print(f"   Resume: {args.resume}")
    print(f"   Output: {OUTPUT_DIR}")
    if args.max_date:
        print(f"   Max Date: {args.max_date} (Historical Mode)")
    print("=" * 70)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Hyperparameters (OPTIMIZED for stability - Matches V2)
    BATCH_SIZE = 64
    EPOCHS = 100
    LEARNING_RATE = 5e-4
    SEQUENCE_LENGTH = 15
    
    # Model Architecture (V2 Specs)
    D_MODEL = 64
    N_HEADS = 4
    N_LAYERS = 4
    D_FF = 128
    
    print("\n📋 HYPERPARAMETERS:")
    print(f"   Batch Size: {BATCH_SIZE}")
    print(f"   Epochs: {EPOCHS}")
    print(f"   Learning Rate: {LEARNING_RATE}")
    print(f"   Sequence Length: {SEQUENCE_LENGTH} games")
    print(f"   Architecture: d_model={D_MODEL}, heads={N_HEADS}, layers={N_LAYERS}")
    
    # Load datasets
    print("\n📂 LOADING DATASETS...")
    print("   ⏳ Loading training data...")
    import time as time_module
    load_start = time_module.time()
    train_ds = SeasonSequenceDataset(split="train", sequence_length=SEQUENCE_LENGTH, max_date=args.max_date)
    print(f"   ✅ Train loaded: {len(train_ds):,} sequences ({time_module.time()-load_start:.1f}s)")
    
    print("   ⏳ Loading validation data...")
    load_start = time_module.time()
    val_ds = SeasonSequenceDataset(split="val", sequence_length=SEQUENCE_LENGTH, max_date=args.max_date)
    print(f"   ✅ Val loaded: {len(val_ds):,} sequences ({time_module.time()-load_start:.1f}s)")
    
    print("   ⏳ Loading test data...")
    load_start = time_module.time()
    test_ds = SeasonSequenceDataset(split="test", sequence_length=SEQUENCE_LENGTH, max_date=args.max_date)
    print(f"   ✅ Test loaded: {len(test_ds):,} sequences ({time_module.time()-load_start:.1f}s)")
    
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)
    
    num_batches = len(train_loader)
    
    print(f"\n📊 DATA SUMMARY:")
    print(f"   Train: {len(train_ds):,} sequences → {num_batches:,} batches of {BATCH_SIZE}")
    print(f"   Val: {len(val_ds):,} sequences → {len(val_loader):,} batches")
    print(f"   Test: {len(test_ds):,} sequences → {len(test_loader):,} batches")
    print(f"   Feature Dim: {train_ds.feature_dim}")
    
    # Initialize model (OPTIMIZED architecture)
    print("\n🧠 INITIALIZING MODEL...")
    print(f"   Architecture: Transformer Encoder")
    print(f"   d_model: {D_MODEL} (embedding dimension)")
    print(f"   n_heads: {N_HEADS} (attention heads)")
    print(f"   n_layers: {N_LAYERS} (transformer layers)")
    print(f"   d_feedforward: {D_FF} (FFN hidden size)")
    print(f"   dropout: 0.15")
    
    model = MomentumTransformer(
        input_dim=train_ds.feature_dim,
        d_model=D_MODEL,
        n_heads=N_HEADS,
        n_layers=N_LAYERS,
        d_feedforward=D_FF,
        dropout=0.15,
    ).to(DEVICE)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"   ✅ Model created!")
    print(f"   Total Parameters: {total_params:,}")
    print(f"   Trainable Parameters: {trainable_params:,}")
    
    criterion = nn.BCELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=20, T_mult=2)

    
    start_epoch = 1
    best_val_acc = 0
    
    # Resume from checkpoint if requested
    if args.resume and CHECKPOINT_PATH.exists():
        logger.info(f"📦 Loading checkpoint from {CHECKPOINT_PATH}")
        checkpoint = torch.load(CHECKPOINT_PATH, map_location=DEVICE)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        best_val_acc = checkpoint.get('best_val_acc', 0)
        logger.info(f"   Resuming from epoch {start_epoch}, best_val_acc: {best_val_acc:.2f}%")
    
    # Training loop
    total_start = time.time()
    
    for epoch in range(start_epoch, EPOCHS + 1):
        logger.info(f"\n{'='*50}")
        logger.info(f"Epoch {epoch}/{EPOCHS}")
        logger.info(f"{'='*50}")
        
        train_loss, train_acc, epoch_time = train_epoch(
            model, train_loader, criterion, optimizer, DEVICE, epoch, EPOCHS
        )
        val_loss, val_acc = evaluate(model, val_loader, criterion, DEVICE)
        scheduler.step()
        
        logger.info(f"  Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        logger.info(f"  Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        logger.info(f"  Epoch Time: {epoch_time:.1f}s")
        
        # Estimate remaining time
        epochs_remaining = EPOCHS - epoch
        est_remaining = epochs_remaining * epoch_time
        logger.info(f"  Estimated remaining: {est_remaining/60:.1f} minutes")
        
        # Save checkpoint every epoch
        checkpoint = {
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'best_val_acc': best_val_acc,
            'train_loss': train_loss,
            'val_acc': val_acc,
            'timestamp': datetime.now().isoformat(),
        }
        torch.save(checkpoint, CHECKPOINT_PATH)
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            checkpoint['best_val_acc'] = best_val_acc
            torch.save(checkpoint, BEST_MODEL_PATH)
            logger.info(f"  ✅ Saved best model (val_acc: {val_acc:.2f}%)")
    
    # Final evaluation on test set
    logger.info("\n🏆 Final Evaluation on Test Set:")
    test_loss, test_acc = evaluate(model, test_loader, criterion, DEVICE)
    logger.info(f"  Test Loss: {test_loss:.4f}, Test Acc: {test_acc:.2f}%")
    
    total_time = time.time() - total_start
    
    print("\n" + "=" * 60)
    print(f"✅ Training complete!")
    print(f"   Best validation accuracy: {best_val_acc:.2f}%")
    print(f"   Test accuracy: {test_acc:.2f}%")
    print(f"   Total time: {total_time/60:.1f} minutes")
    print(f"   Model saved to: {BEST_MODEL_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
