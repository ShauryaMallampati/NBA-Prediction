#!/usr/bin/env python3
"""
Vision CNN Training Script

Trains a shot classifier on the Basketball_51 dataset (10,311 video clips).
Labels: 2p0/2p1, 3p0/3p1, ft0/ft1, mp0/mp1 (miss/make for each shot type)
"""

import os
import argparse
import logging
import random
from pathlib import Path
from typing import List, Tuple, Dict
import json
import os

# Enable MPS fallback for 3D operations not yet supported on Apple Silicon
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
import numpy as np

# Try to import video reading libraries
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("Warning: cv2 not available, using dummy data")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path("data/Basketball_51 dataset")
OUTPUT_DIR = Path("artifacts/models/vision")

# Label mapping (8 classes)
LABELS = {
    "2p0": 0,  # 2-point miss
    "2p1": 1,  # 2-point make
    "3p0": 2,  # 3-point miss
    "3p1": 3,  # 3-point make
    "ft0": 4,  # free throw miss
    "ft1": 5,  # free throw make
    "mp0": 6,  # mid-range miss
    "mp1": 7,  # mid-range make
}

LABEL_NAMES = {v: k for k, v in LABELS.items()}


class Basketball51Dataset(Dataset):
    """Dataset for Basketball-51 video clips."""
    
    def __init__(
        self, 
        data_dir: Path,
        split: str = "train",
        num_frames: int = 16,
        frame_size: int = 224,
        train_ratio: float = 0.8
    ):
        self.data_dir = data_dir
        self.num_frames = num_frames
        self.frame_size = frame_size
        
        # Collect all video paths with labels
        self.samples: List[Tuple[Path, int]] = []
        
        for label_name, label_id in LABELS.items():
            label_dir = data_dir / label_name
            if label_dir.exists():
                videos = list(label_dir.glob("*.mp4"))
                for video_path in videos:
                    self.samples.append((video_path, label_id))
        
        # Shuffle and split
        random.seed(42)
        random.shuffle(self.samples)
        
        split_idx = int(len(self.samples) * train_ratio)
        if split == "train":
            self.samples = self.samples[:split_idx]
        else:
            self.samples = self.samples[split_idx:]
        
        logger.info(f"Loaded {len(self.samples)} samples for {split} split")
        
        # Transform
        self.transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((frame_size, frame_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    def __len__(self) -> int:
        return len(self.samples)
    
    def _load_video_frames(self, video_path: Path) -> torch.Tensor:
        """Load and sample frames from video."""
        if not HAS_CV2:
            # Return dummy data if cv2 not available
            return torch.randn(self.num_frames, 3, self.frame_size, self.frame_size)
        
        cap = cv2.VideoCapture(str(video_path))
        frames = []
        
        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames == 0:
                total_frames = 100  # Fallback
            
            # Sample frames evenly
            indices = np.linspace(0, total_frames - 1, self.num_frames, dtype=int)
            
            for idx in indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = self.transform(frame)
                    frames.append(frame)
                else:
                    # Pad with last frame or zeros
                    if frames:
                        frames.append(frames[-1].clone())
                    else:
                        frames.append(torch.zeros(3, self.frame_size, self.frame_size))
        finally:
            cap.release()
        
        # Stack frames: (num_frames, 3, H, W)
        return torch.stack(frames)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        video_path, label = self.samples[idx]
        frames = self._load_video_frames(video_path)
        return frames, label


class Simple3DCNN(nn.Module):
    """Simple 3D CNN for video classification."""
    
    def __init__(self, num_classes: int = 8, num_frames: int = 16):
        super().__init__()
        
        # 3D Convolutions
        self.features = nn.Sequential(
            # Input: (batch, 3, num_frames, 224, 224)
            nn.Conv3d(3, 32, kernel_size=(3, 7, 7), stride=(1, 2, 2), padding=(1, 3, 3)),
            nn.BatchNorm3d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2), padding=(0, 1, 1)),
            
            nn.Conv3d(32, 64, kernel_size=(3, 3, 3), padding=1),
            nn.BatchNorm3d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool3d(kernel_size=(2, 2, 2), stride=(2, 2, 2)),
            
            nn.Conv3d(64, 128, kernel_size=(3, 3, 3), padding=1),
            nn.BatchNorm3d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool3d(kernel_size=(2, 2, 2), stride=(2, 2, 2)),
            
            nn.Conv3d(128, 256, kernel_size=(3, 3, 3), padding=1),
            nn.BatchNorm3d(256),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool3d((1, 1, 1)),
        )
        
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(0.5),
            nn.Linear(256, 128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, num_frames, 3, H, W) -> (batch, 3, num_frames, H, W)
        x = x.permute(0, 2, 1, 3, 4)
        x = self.features(x)
        x = self.classifier(x)
        return x


def train_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    epoch: int = 1,
    start_batch: int = 0,
    checkpoint_callback=None,
    checkpoint_every: int = 50
) -> Tuple[float, float]:
    """Train for one epoch with batch-level checkpointing.
    
    Args:
        start_batch: Resume from this batch index (0 = start from beginning)
        checkpoint_callback: Function(epoch, batch_idx) to save checkpoint
        checkpoint_every: Save checkpoint every N batches
    """
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    for batch_idx, (frames, labels) in enumerate(dataloader):
        # Skip batches if resuming mid-epoch
        if batch_idx < start_batch:
            if (batch_idx + 1) % 50 == 0:
                logger.info(f"  ⏭️ Resuming: Fast-forwarding through batch {batch_idx + 1}/{start_batch}...")
            continue
            
        frames = frames.to(device)
        labels = labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(frames)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        if (batch_idx + 1) % 10 == 0:
            logger.info(f"  Batch {batch_idx + 1}/{len(dataloader)}, Loss: {loss.item():.4f}")
        
        # Save batch checkpoint
        if checkpoint_callback and (batch_idx + 1) % checkpoint_every == 0:
            checkpoint_callback(epoch, batch_idx + 1)
            logger.info(f"  💾 Checkpoint saved at batch {batch_idx + 1}")
    
    accuracy = 100.0 * correct / max(total, 1)
    avg_loss = total_loss / max(len(dataloader) - start_batch, 1)
    return avg_loss, accuracy


def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, float]:
    """Evaluate on validation set."""
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for frames, labels in dataloader:
            frames = frames.to(device)
            labels = labels.to(device)
            
            outputs = model(frames)
            loss = criterion(outputs, labels)
            
            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    
    accuracy = 100.0 * correct / total
    avg_loss = total_loss / len(dataloader)
    return avg_loss, accuracy


def main():
    logger.info("🏀 Starting Vision CNN Training on Basketball_51 Dataset")
    
    # Device
    if torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    logger.info(f"Using device: {device}")
    
    # Config
    parser = argparse.ArgumentParser(description="Train Vision CNN")
    parser.add_argument("--resume", action="store_true", help="Resume from latest checkpoint")
    args = parser.parse_args()

    num_epochs = 20
    batch_size = 4  # Small batch due to video memory
    learning_rate = 1e-4
    num_frames = 16
    
    # Create datasets
    logger.info(f"Loading dataset from {DATA_DIR}")
    train_dataset = Basketball51Dataset(DATA_DIR, split="train", num_frames=num_frames)
    val_dataset = Basketball51Dataset(DATA_DIR, split="val", num_frames=num_frames)
    
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=0
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False, num_workers=0
    )
    
    # Model
    model = Simple3DCNN(num_classes=8, num_frames=num_frames).to(device)
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Training setup
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)
    
    start_epoch = 1
    start_batch = 0
    best_val_acc = 0
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_path = OUTPUT_DIR / "checkpoint_latest.pt"
    best_model_path = OUTPUT_DIR / "basketball_shot_classifier.pt"

    # Checkpoint callback for batch-level saving
    def save_checkpoint(epoch: int, batch_idx: int):
        checkpoint_data = {
            'epoch': epoch,
            'batch': batch_idx,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'best_val_acc': best_val_acc,
        }
        torch.save(checkpoint_data, checkpoint_path)
        logger.info(f"     ✓ Batch checkpoint saved at epoch {epoch}, batch {batch_idx}")

    # Auto-load best model if it exists, or resume from checkpoint
    if best_model_path.exists() and not args.resume:
        logger.info(f"📦 Loading best model from previous training: {best_model_path}")
        best_checkpoint = torch.load(best_model_path, map_location=device)
        model.load_state_dict(best_checkpoint['model_state_dict'])
        best_val_acc = best_checkpoint.get('best_val_acc', 0)
        logger.info(f"   Loaded best model (previous best val_acc: {best_val_acc:.2f}%)")
        start_epoch = 1  # Start from epoch 1 with the best model
    elif args.resume and checkpoint_path.exists():
        logger.info(f"🔄 Resuming from checkpoint: {checkpoint_path}")
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        start_epoch = checkpoint['epoch']
        start_batch = checkpoint.get('batch', 0)
        best_val_acc = checkpoint.get('best_val_acc', 0)
        
        # If batch > 0, we're mid-epoch; otherwise start next epoch
        if start_batch == 0:
            start_epoch += 1
        logger.info(f"   Resuming at Epoch {start_epoch}, Batch {start_batch} (Best Val Acc: {best_val_acc:.2f}%)")
    elif args.resume:
        logger.warning(f"⚠️ Resume requested but no checkpoint found. Starting fresh.")
    
    # Training loop
    for epoch in range(start_epoch, num_epochs + 1):
        logger.info(f"\n📌 Epoch {epoch}/{num_epochs}")
        
        # On first epoch after resume, start from saved batch; otherwise 0
        batch_start = start_batch if epoch == start_epoch else 0
        
        train_loss, train_acc = train_epoch(
            model, train_loader, criterion, optimizer, device,
            epoch=epoch,
            start_batch=batch_start,
            checkpoint_callback=save_checkpoint,
            checkpoint_every=50  # Save every 50 batches
        )
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        
        scheduler.step()
        
        logger.info(f"  Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%")
        logger.info(f"  Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        # Save end-of-epoch checkpoint (batch=0 signals complete epoch)
        checkpoint_data = {
            'epoch': epoch,
            'batch': 0,  # 0 means epoch completed
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scheduler_state_dict': scheduler.state_dict(),
            'best_val_acc': best_val_acc,
        }
        torch.save(checkpoint_data, checkpoint_path)
        logger.info(f"  💾 Epoch checkpoint saved")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_checkpoint = {
                'model_state_dict': model.state_dict(),
                'num_classes': 8,
                'num_frames': num_frames,
                'labels': LABELS,
                'best_val_acc': best_val_acc,
                'epoch': epoch,
            }
            torch.save(best_checkpoint, best_model_path)
            logger.info(f"  ✅ Saved best model at epoch {epoch} (val_acc: {val_acc:.2f}%)")
    
    logger.info(f"\n🏆 Training complete! Best validation accuracy: {best_val_acc:.2f}%")
    logger.info(f"   Model saved to: {OUTPUT_DIR / 'basketball_shot_classifier.pt'}")


if __name__ == "__main__":
    main()
