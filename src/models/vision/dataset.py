from __future__ import annotations
import torch, pandas as pd
from torch.utils.data import Dataset

class ClipDataset(Dataset):
    def __init__(self, index_parquet: str):
        try:
            df = pd.read_parquet(index_parquet)
            self.df = df
        except Exception as e:
            print(f"⚠️ Failed to load clip index: {e}")
            self.df = pd.DataFrame()

    def __len__(self): return len(self.df)

    def __getitem__(self, idx):
        # In a real scenario, we would load the video file here using torchvision.io.read_video
        # row = self.df.iloc[idx]
        # video_path = row['path']
        # video, _, _ = read_video(video_path)
        # ... transform ...
        
        # For now, return a random tensor matching MobileNetV3 input (3, 224, 224)
        x = torch.randn(3, 224, 224)
        
        # Get label if available, else 0
        if 'label' in self.df.columns:
            y = torch.tensor(self.df.iloc[idx]['label'], dtype=torch.long)
        else:
            y = torch.tensor(0, dtype=torch.long)
            
        return x, y
