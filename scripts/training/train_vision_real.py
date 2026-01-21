#!/usr/bin/env python3
"""
🎥 Train Vision CNN on Real NBA Video Highlights (Enhanced Logging Version)

This script trains a MobileNetV3 model on downloaded NBA highlights to predict
whether the HOME team won based on visual content. The underlying hypothesis
is that winning team footage contains more "makes", energetic plays, etc.

Usage:
    poetry run python scripts/training/train_vision_real.py --epochs 10

Outputs:
    artifacts/models/vision/basketball_shot_classifier.pt
    artifacts/models/vision/training_log.json
"""

import os
import sys
import glob
import cv2
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import json
import logging
import time
import datetime
from torchvision import transforms
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
VIDEO_DIR = Path("data/video_highlights")
METADATA_DIR = Path("data/video_metadata")
OUTPUT_DIR = Path("artifacts/models/vision")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

# Image transforms (Standard ImageNet normalization)
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


class NBAVideoDataset(Dataset):
    def __init__(self, video_files, labels, num_frames=16):
        self.video_files = video_files
        self.labels = labels
        self.num_frames = num_frames
        
    def __len__(self):
        return len(self.video_files)
    
    def __getitem__(self, idx):
        video_path = self.video_files[idx]
        label = self.labels[idx]
        frames = self._extract_frames(video_path)
        return torch.stack(frames), torch.tensor(label, dtype=torch.float32)

    def _extract_frames(self, video_path):
        cap = cv2.VideoCapture(str(video_path))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if total_frames <= 0:
            return [torch.zeros(3, 224, 224) for _ in range(self.num_frames)]
            
        indices = np.linspace(0, total_frames-1, self.num_frames, dtype=int)
        frames = []
        
        for i in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = transform(frame)
                frames.append(frame)
            else:
                frames.append(torch.zeros(3, 224, 224))
        
        cap.release()
        return frames


def get_model():
    from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights
    
    weights = MobileNet_V3_Large_Weights.DEFAULT
    model = mobilenet_v3_large(weights=weights)
    
    # Freeze backbone
    for param in model.features.parameters():
        param.requires_grad = False
        
    # Replace classifier
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, 1)
    
    return model


def train(args):
    start_time = time.time()
    training_log = {
        "start_time": datetime.datetime.now().isoformat(),
        "epochs": [],
        "config": vars(args)
    }
    
    # ========================================
    # HEADER
    # ========================================
    print("\n" + "="*70)
    print("🎬 VISION CNN TRAINING — REAL NBA VIDEO DATA")
    print("="*70)
    print(f"📅 Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️  Device: {DEVICE}")
    print(f"📂 Video Dir: {VIDEO_DIR}")
    print(f"🔢 Epochs: {args.epochs}")
    print(f"📦 Batch Size: {args.batch_size}")
    print("="*70 + "\n")
    
    # ========================================
    # LOAD DATA
    # ========================================
    print("📂 [STEP 1/4] Loading Dataset...")
    json_files = sorted(METADATA_DIR.glob("downloads_*.json"))
    if not json_files:
        print("❌ No metadata/videos found! Run scripts/download_highlights.py first.")
        return

    video_paths = []
    labels = []
    home_wins = 0
    
    for jf in json_files:
        with open(jf, 'r') as f:
            data = json.load(f)
            for item in data:
                path = Path(item['video_path'])
                if path.exists():
                    video_paths.append(path)
                    label = 1.0 if item['home_win'] == 1 else 0.0
                    labels.append(label)
                    home_wins += label
    
    if len(video_paths) == 0:
        print("❌ No video files found.")
        return
    
    print(f"   ✅ Total Videos: {len(video_paths)}")
    print(f"   📊 Home Wins: {int(home_wins)} ({home_wins/len(video_paths)*100:.1f}%)")
    print(f"   📊 Away Wins: {len(video_paths) - int(home_wins)} ({(1 - home_wins/len(video_paths))*100:.1f}%)")
    
    # Split
    split_idx = int(0.8 * len(video_paths))
    train_paths, val_paths = video_paths[:split_idx], video_paths[split_idx:]
    train_labels, val_labels = labels[:split_idx], labels[split_idx:]
    
    print(f"   📈 Train Set: {len(train_paths)} videos")
    print(f"   📉 Val Set: {len(val_paths)} videos\n")
    
    training_log["dataset"] = {
        "total_videos": len(video_paths),
        "train_size": len(train_paths),
        "val_size": len(val_paths),
        "home_win_rate": home_wins/len(video_paths)
    }
    
    train_ds = NBAVideoDataset(train_paths, train_labels)
    val_ds = NBAVideoDataset(val_paths, val_labels)
    
    train_dl = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_dl = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False)
    
    # ========================================
    # MODEL SETUP
    # ========================================
    print("🧠 [STEP 2/4] Initializing Model...")
    model = get_model().to(DEVICE)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"   📐 Total Parameters: {total_params:,}")
    print(f"   🔧 Trainable Parameters: {trainable_params:,}\n")
    
    training_log["model"] = {
        "architecture": "MobileNetV3-Large",
        "total_params": total_params,
        "trainable_params": trainable_params
    }
    
    # ========================================
    # TRAINING LOOP
    # ========================================
    print("🚀 [STEP 3/4] Training...\n")
    best_acc = 0.0
    
    for epoch in range(args.epochs):
        epoch_start = time.time()
        model.train()
        train_loss = 0
        train_correct = 0
        total_train = 0
        batch_losses = []
        
        print(f"┌{'─'*68}┐")
        print(f"│ EPOCH {epoch+1}/{args.epochs}{' '*55}│")
        print(f"├{'─'*68}┤")
        
        pbar = tqdm(train_dl, desc=f"  Training", leave=False)
        for batch_idx, (frames, targets) in enumerate(pbar):
            B, T, C, H, W = frames.shape
            frames = frames.view(B*T, C, H, W).to(DEVICE)
            targets = targets.to(DEVICE).unsqueeze(1)
            
            optimizer.zero_grad()
            outputs = model(frames)
            outputs = outputs.view(B, T, 1)
            avg_output = torch.mean(outputs, dim=1)
            
            loss = criterion(avg_output, targets)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * B
            preds = (torch.sigmoid(avg_output) > 0.5).float()
            train_correct += (preds == targets).sum().item()
            total_train += B
            batch_losses.append(loss.item())
            
            pbar.set_postfix({'loss': f'{loss.item():.4f}'})
            
            # Detailed log every 10 batches
            if (batch_idx + 1) % 10 == 0:
                running_acc = train_correct / total_train
                logger.info(f"  Batch {batch_idx+1}/{len(train_dl)} | Loss: {loss.item():.4f} | Running Acc: {running_acc:.4f}")
        
        train_acc = train_correct / total_train
        avg_train_loss = train_loss / total_train
        
        # Validation
        model.eval()
        val_correct = 0
        total_val = 0
        val_preds_all = []
        val_targets_all = []
        
        with torch.no_grad():
            for frames, targets in val_dl:
                B, T, C, H, W = frames.shape
                frames = frames.view(B*T, C, H, W).to(DEVICE)
                targets = targets.to(DEVICE).unsqueeze(1)
                
                outputs = model(frames)
                avg_output = torch.mean(outputs.view(B, T, 1), dim=1)
                
                preds = (torch.sigmoid(avg_output) > 0.5).float()
                val_correct += (preds == targets).sum().item()
                total_val += B
                
                val_preds_all.extend(preds.cpu().numpy().flatten().tolist())
                val_targets_all.extend(targets.cpu().numpy().flatten().tolist())
        
        val_acc = val_correct / total_val if total_val > 0 else 0
        epoch_time = time.time() - epoch_start
        
        # Epoch Summary
        print(f"│ {'Train Loss:':<20} {avg_train_loss:.4f}{' '*40}│")
        print(f"│ {'Train Accuracy:':<20} {train_acc*100:.2f}%{' '*39}│")
        print(f"│ {'Val Accuracy:':<20} {val_acc*100:.2f}%{' '*39}│")
        print(f"│ {'Epoch Time:':<20} {epoch_time:.1f}s{' '*41}│")
        
        improved = ""
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), OUTPUT_DIR / "basketball_shot_classifier.pt")
            improved = " ⭐ NEW BEST"
            print(f"│ {'💾 Model Saved!':<20} {improved}{' '*37}│")
        
        print(f"└{'─'*68}┘\n")
        
        # Log epoch
        training_log["epochs"].append({
            "epoch": epoch + 1,
            "train_loss": avg_train_loss,
            "train_acc": train_acc,
            "val_acc": val_acc,
            "time_seconds": epoch_time,
            "best": val_acc == best_acc
        })
    
    # ========================================
    # FINAL SUMMARY
    # ========================================
    total_time = time.time() - start_time
    print("\n" + "="*70)
    print("📊 TRAINING COMPLETE — FINAL SUMMARY")
    print("="*70)
    print(f"   ⏱️  Total Time: {total_time/60:.1f} minutes")
    print(f"   🏆 Best Val Accuracy: {best_acc*100:.2f}%")
    print(f"   💾 Model Saved To: {OUTPUT_DIR / 'basketball_shot_classifier.pt'}")
    print("="*70 + "\n")
    
    training_log["final"] = {
        "total_time_minutes": total_time / 60,
        "best_val_acc": best_acc
    }
    
    # Save training log
    log_path = OUTPUT_DIR / "training_log.json"
    with open(log_path, 'w') as f:
        json.dump(training_log, f, indent=2)
    print(f"📋 Training log saved to: {log_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Vision CNN on Real NBA Videos")
    parser.add_argument("--epochs", type=int, default=10, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    args = parser.parse_args()
    
    train(args)
