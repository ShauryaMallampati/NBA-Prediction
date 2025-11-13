from __future__ import annotations
import pandas as pd, torch
from torch_geometric.data import Data

def build_lineup_graph(edges_path: str) -> Data:
    """Build graph from player chemistry edges"""
    df = pd.read_parquet(edges_path)
    
    # Get unique nodes (players)
    nodes = sorted(set(df["player1_id"]).union(set(df["player2_id"])))
    idx = {n: i for i, n in enumerate(nodes)}
    
    # Create edge index (bidirectional)
    src_fwd = [idx[u] for u in df["player1_id"]]
    dst_fwd = [idx[v] for v in df["player2_id"]]
    src_bwd = [idx[v] for v in df["player2_id"]]
    dst_bwd = [idx[u] for u in df["player1_id"]]
    
    # Stack as [2, num_edges] tensor
    edge_index = torch.tensor([src_fwd + src_bwd, dst_fwd + dst_bwd], dtype=torch.long)
    
    # Create node features (8 dimensions)
    # In production, these would be actual player stats
    x = torch.randn(len(nodes), 8)
    
    # Target: chemistry scores (duplicate for bidirectional edges)
    y_forward = torch.tensor(df["chemistry_score"].values, dtype=torch.float32)
    y_backward = y_forward.clone()
    y = torch.cat([y_forward, y_backward])
    
    return Data(x=x, edge_index=edge_index, y=y, nodes=nodes)
