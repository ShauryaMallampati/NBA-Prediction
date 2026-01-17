import torch
from pathlib import Path
import json

def inspect_checkpoint(path, name):
    print(f"\n--- {name} Checkpoint ---")
    if not Path(path).exists():
        print(f"File not found: {path}")
        return
    
    try:
        # Load on CPU to avoid MPS/CUDA issues
        checkpoint = torch.load(path, map_location='cpu')
        
        # Most of our checkpoints have 'epoch', 'train_loss', 'val_acc', 'best_val_acc'
        epoch = checkpoint.get('epoch', 'N/A')
        train_loss = checkpoint.get('train_loss', 'N/A')
        val_acc = checkpoint.get('val_acc', 'N/A')
        best_val_acc = checkpoint.get('best_val_acc', 'N/A')
        timestamp = checkpoint.get('timestamp', 'N/A')
        
        print(f"Path: {path}")
        print(f"Epoch: {epoch}")
        print(f"Current Train Loss: {train_loss}")
        print(f"Current Val Accuracy: {val_acc}%")
        print(f"Best Val Accuracy: {best_val_acc}%")
        print(f"Last Updated: {timestamp}")
        
    except Exception as e:
        print(f"Error loading {path}: {e}")

if __name__ == "__main__":
    inspect_checkpoint("artifacts/models/vision/checkpoint_latest.pt", "Vision CNN")
    inspect_checkpoint("artifacts/models/momentum/checkpoint_latest.pt", "Momentum Transformer")
