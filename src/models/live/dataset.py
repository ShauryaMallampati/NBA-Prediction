from __future__ import annotations
import torch, pandas as pd
from torch.utils.data import Dataset

class LiveSeqDataset(Dataset):
    def __init__(self, parquet_path: str):
        df = pd.read_parquet(parquet_path)
        self.gids = sorted(df["game_id"].unique())
        self.groups = {g: torch.tensor(df[df.game_id == g][["score_diff"]].values, dtype=torch.float32) for g in self.gids}
        self.targets = {g: torch.tensor(df[df.game_id == g]["winner"].iloc[0], dtype=torch.float32) for g in self.gids}

    def __len__(self): return len(self.gids)
    def __getitem__(self, idx):
        g = self.gids[idx]
        return self.groups[g], torch.tensor(self.targets[g]).view(1)
