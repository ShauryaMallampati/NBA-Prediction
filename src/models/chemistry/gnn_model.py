"""
Chemistry GNN Model - Alias for compatibility.

The actual implementation is in train_gnn.py as the SAGE class.
This module re-exports it as ChemistryGNN for consistency with
the streaming_world_model_eval.py imports.
"""

from pathlib import Path
import torch
from torch import nn

try:
    from torch_geometric.nn import SAGEConv
    TORCH_GEOMETRIC_AVAILABLE = True
except ImportError:
    TORCH_GEOMETRIC_AVAILABLE = False
    SAGEConv = None


class ChemistryGNN(torch.nn.Module):
    """
    GraphSAGE-based Chemistry model for player lineup synergy prediction.
    
    Predicts the "chemistry score" between players based on their
    historical performance when playing together.
    """
    
    def __init__(self, in_dim=8, hidden=96):
        super().__init__()
        if not TORCH_GEOMETRIC_AVAILABLE:
            raise ImportError("torch_geometric is required for ChemistryGNN")
        
        self.conv1 = SAGEConv(in_dim, hidden)
        self.conv2 = SAGEConv(hidden, hidden)
        self.lin = nn.Linear(hidden * 2, 1)

    def forward(self, x, edge_index):
        # Get node embeddings
        h = torch.relu(self.conv1(x, edge_index))
        h = torch.relu(self.conv2(h, edge_index))
        
        # Get edge embeddings by concatenating source and target node embeddings
        src, dst = edge_index
        edge_emb = torch.cat([h[src], h[dst]], dim=1)
        return self.lin(edge_emb)
    
    @classmethod
    def load(cls, path: Path = None, device: str = "cpu"):
        """Load a trained ChemistryGNN model."""
        if path is None:
            path = Path("artifacts/models/chemistry_sage.pt")
        
        model = cls()
        if path.exists():
            model.load_state_dict(torch.load(path, map_location=device))
        return model


# Alias for backward compatibility
SAGE = ChemistryGNN
