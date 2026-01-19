#!/usr/bin/env python3
"""
🎧 Train Audio Classifier on Real NBA Crowd Noise (Enhanced Logging Version)

This script:
1. Scans `data/video_highlights/` for downloaded videos.
2. Extracts audio features (Loudness, Peaks).
3. Trains a simple MLP to predict "Home Win" from crowd audio features.

Hypothesis: Louder home crowd audio correlates with Home Win.

Usage:
    poetry run python scripts/train_audio_real.py --epochs 30

Outputs:
    artifacts/models/audio/crowd_classifier.pt
    artifacts/models/audio/training_log.json
"""

import sys
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np
from pathlib import Path
from tqdm import tqdm
import json
import logging
import subprocess
import tempfile
import warnings
import time
import datetime
import argparse

# Suppress warnings
warnings.filterwarnings("ignore")

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
OUTPUT_DIR = Path("artifacts/models/audio")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DEVICE = torch.device("cpu")

# Try importing librosa
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    print("❌ librosa not found. Install with: poetry add librosa")
    sys.exit(1)


class AudioFeatureDataset(Dataset):
    def __init__(self, features_list, labels):
        self.features = torch.tensor(features_list, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32)
        
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


class AudioClassifier(nn.Module):
    def __init__(self, input_dim=4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.BatchNorm1d(32),
            nn.Dropout(0.3),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, 1)
        )
        
    def forward(self, x):
        return self.net(x)


def extract_audio_features(video_path):
    """Extract 4 key features from video audio."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_path = temp_audio.name
        
        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1",
            temp_path
        ]
        result = subprocess.run(cmd, capture_output=True, check=True, timeout=30)
        
        y, sr = librosa.load(temp_path, sr=22050)
        Path(temp_path).unlink(missing_ok=True)
        
        rms = librosa.feature.rms(y=y)[0]
        
        mean_loudness = float(np.mean(rms))
        max_loudness = float(np.max(rms))
        
        threshold = np.percentile(rms, 90)
        peaks = np.where(rms > threshold)[0]
        num_peaks = len(peaks)
        
        peak_std = float(np.std(rms[peaks])) if len(peaks) > 0 else 0.0
        
        return [mean_loudness, max_loudness, num_peaks, peak_std]
        
    except Exception as e:
        return None


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
    print("🎧 AUDIO CLASSIFIER TRAINING — REAL NBA CROWD NOISE")
    print("="*70)
    print(f"📅 Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️  Device: {DEVICE}")
    print(f"📂 Video Dir: {VIDEO_DIR}")
    print(f"🔢 Epochs: {args.epochs}")
    print("="*70 + "\n")
    
    # ========================================
    # LOAD METADATA
    # ========================================
    print("📂 [STEP 1/4] Loading Metadata...")
    json_files = sorted(METADATA_DIR.glob("downloads_*.json"))
    if not json_files:
        print("❌ No metadata found! Run scripts/download_highlights.py first.")
        return

    dataset_items = []
    
    for jf in json_files:
        with open(jf, 'r') as f:
            data = json.load(f)
            for item in data:
                path = Path(item['video_path'])
                if path.exists():
                    dataset_items.append({
                        "path": path,
                        "label": 1.0 if item['home_win'] == 1 else 0.0
                    })
    
    if not dataset_items:
        print("❌ No videos found.")
        return

    print(f"   ✅ Found {len(dataset_items)} videos to process\n")
    
    # ========================================
    # EXTRACT AUDIO FEATURES
    # ========================================
    print("🎵 [STEP 2/4] Extracting Audio Features...")
    print(f"   ⏳ This may take a few minutes for {len(dataset_items)} videos...\n")
    
    features_list = []
    valid_labels = []
    failed_count = 0
    
    pbar = tqdm(dataset_items, desc="   Processing")
    for i, item in enumerate(pbar):
        feats = extract_audio_features(item['path'])
        if feats:
            # Normalize num_peaks
            feats[2] = feats[2] / 100.0 
            features_list.append(feats)
            valid_labels.append(item['label'])
        else:
            failed_count += 1
        
        # Log every 50 videos
        if (i + 1) % 50 == 0:
            logger.info(f"   Processed {i+1}/{len(dataset_items)} videos | Success: {len(features_list)} | Failed: {failed_count}")
            
    print(f"\n   ✅ Successfully extracted: {len(features_list)} videos")
    print(f"   ❌ Failed extraction: {failed_count} videos")
    
    if not features_list:
        print("❌ Failed to extract any audio features.")
        return
    
    # Feature Statistics
    features_array = np.array(features_list)
    print("\n   📊 Feature Statistics:")
    print(f"      {'Feature':<20} {'Mean':>10} {'Std':>10} {'Min':>10} {'Max':>10}")
    print(f"      {'-'*60}")
    feature_names = ["Mean Loudness", "Max Loudness", "Num Peaks (norm)", "Peak Std"]
    for i, name in enumerate(feature_names):
        print(f"      {name:<20} {features_array[:,i].mean():>10.4f} {features_array[:,i].std():>10.4f} {features_array[:,i].min():>10.4f} {features_array[:,i].max():>10.4f}")
    print()
    
    training_log["feature_stats"] = {
        name: {
            "mean": float(features_array[:,i].mean()),
            "std": float(features_array[:,i].std()),
            "min": float(features_array[:,i].min()),
            "max": float(features_array[:,i].max())
        } for i, name in enumerate(feature_names)
    }
    
    # ========================================
    # PREPARE DATA
    # ========================================
    print("📦 [STEP 3/4] Preparing DataLoaders...")
    
    split_idx = int(0.8 * len(features_list))
    train_feats, val_feats = features_list[:split_idx], features_list[split_idx:]
    train_labels, val_labels = valid_labels[:split_idx], valid_labels[split_idx:]
    
    print(f"   📈 Train Set: {len(train_feats)} samples")
    print(f"   📉 Val Set: {len(val_feats)} samples\n")
    
    train_ds = AudioFeatureDataset(train_feats, train_labels)
    val_ds = AudioFeatureDataset(val_feats, val_labels)
    
    train_dl = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_dl = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False)
    
    # ========================================
    # MODEL SETUP
    # ========================================
    print("🧠 Initializing Model...")
    model = AudioClassifier().to(DEVICE)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    
    total_params = sum(p.numel() for p in model.parameters())
    print(f"   📐 Total Parameters: {total_params:,}\n")
    
    # ========================================
    # TRAINING LOOP
    # ========================================
    print("🚀 [STEP 4/4] Training...\n")
    best_acc = 0.0
    
    for epoch in range(args.epochs):
        epoch_start = time.time()
        model.train()
        train_loss = 0
        train_correct = 0
        total_train = 0
        
        for x, y in train_dl:
            optimizer.zero_grad()
            out = model(x).squeeze()
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * len(x)
            preds = (torch.sigmoid(out) > 0.5).float()
            train_correct += (preds == y).sum().item()
            total_train += len(x)
        
        train_acc = train_correct / total_train
        avg_loss = train_loss / total_train
        
        # Validation
        model.eval()
        val_correct = 0
        total_val = 0
        with torch.no_grad():
            for x, y in val_dl:
                out = model(x).squeeze()
                preds = (torch.sigmoid(out) > 0.5).float()
                val_correct += (preds == y).sum().item()
                total_val += len(x)
        
        val_acc = val_correct / total_val if total_val > 0 else 0
        epoch_time = time.time() - epoch_start
        
        improved = ""
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model, OUTPUT_DIR / "crowd_classifier.pt")
            improved = " ⭐"
        
        # Log every epoch
        print(f"   Epoch {epoch+1:>3}/{args.epochs} | Loss: {avg_loss:.4f} | Train Acc: {train_acc*100:.1f}% | Val Acc: {val_acc*100:.1f}%{improved}")
        
        training_log["epochs"].append({
            "epoch": epoch + 1,
            "train_loss": avg_loss,
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
    print(f"   ⏱️  Total Time: {total_time:.1f} seconds")
    print(f"   🏆 Best Val Accuracy: {best_acc*100:.2f}%")
    print(f"   💾 Model Saved To: {OUTPUT_DIR / 'crowd_classifier.pt'}")
    print("="*70 + "\n")
    
    training_log["final"] = {
        "total_time_seconds": total_time,
        "best_val_acc": best_acc
    }
    
    # Save training log
    log_path = OUTPUT_DIR / "training_log.json"
    with open(log_path, 'w') as f:
        json.dump(training_log, f, indent=2)
    print(f"📋 Training log saved to: {log_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Audio Classifier on Real NBA Crowd Noise")
    parser.add_argument("--epochs", type=int, default=30, help="Number of epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.005, help="Learning rate")
    args = parser.parse_args()
    
    train(args)
