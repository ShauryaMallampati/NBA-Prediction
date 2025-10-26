from __future__ import annotations
import pandas as pd, torch
from torch_geometric.data import Data

def build_lineup_graph(edges_path: str) -> Data:
    df = pd.read_parquet(edges_path)
    nodes = sorted(set(df["u"]).union(set(df["v"])))
    idx = {n: i for i, n in enumerate(nodes)}
    edge_index = torch.tensor([
        [idx[u] for u in df["u"]],
        [idx[v] for v in df["v"]]
    ], dtype=torch.long)
    x = torch.randn(len(nodes), 8)
    y = torch.tensor((df["assists"] / (df["co_min"] + 1e-6)).values, dtype=torch.float32)
    return Data(x=x, edge_index=edge_index, y=y, nodes=nodes)
