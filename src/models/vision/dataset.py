from __future__ import annotations
import torch, pandas as pd
from torch.utils.data import Dataset

class ClipDataset(Dataset):
    def __init__(self, index_parquet: str):
        df = pd.read_parquet(index_parquet)
        self.df = df
    def __len__(self): return len(self.df)
    def __getitem__(self, idx):
        x = torch.randn(3, 224, 224)
        y = torch.tensor(0)
        return x, y
