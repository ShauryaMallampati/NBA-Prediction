from __future__ import annotations
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import torch
from torch import nn
from torch_geometric.nn import SAGEConv
from src.models.chemistry.graph_utils import build_lineup_graph
from src.common.hardware import pick_device

DEVICE = pick_device("mps")
EDGES = "artifacts/chemistry/lineup_edges.parquet"
OUT = Path("artifacts/models").resolve()
OUT.mkdir(parents=True, exist_ok=True)

class SAGE(torch.nn.Module):
    def __init__(self, in_dim=8, hidden=96):
        super().__init__()
        self.conv1 = SAGEConv(in_dim, hidden)
        self.conv2 = SAGEConv(hidden, hidden)
        self.lin = nn.Linear(hidden * 2, 1)  # Concatenate source and target embeddings

    def forward(self, x, edge_index):
        # Get node embeddings
        h = torch.relu(self.conv1(x, edge_index))
        h = torch.relu(self.conv2(h, edge_index))
        
        # Get edge embeddings by concatenating source and target node embeddings
        src, dst = edge_index
        edge_emb = torch.cat([h[src], h[dst]], dim=1)
        return self.lin(edge_emb)

def main() -> None:
    print(f"\n{'='*60}")
    print(f"🏀 Training GraphSAGE Chemistry Model")
    print(f"{'='*60}")
    print(f"Device: {DEVICE}")
    print(f"Edges file: {EDGES}")
    print(f"Output dir: {OUT}\n")
    
    data = build_lineup_graph(EDGES)
    print(f"✅ Loaded graph data")
    print(f"   Nodes: {data.num_nodes}")
    print(f"   Edges: {data.num_edges // 2} (bidirectional)")
    print(f"   Features: {data.x.shape[1]}\n")
    
    model = SAGE(in_dim=data.x.size(1), hidden=96).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    mse = nn.MSELoss()
    
    print(f"🎯 Starting training (10 epochs)...\n")
    best_loss = float('inf')
    
    for epoch in range(10):
        model.train()
        opt.zero_grad()
        pred = model(data.x.to(DEVICE), data.edge_index.to(DEVICE)).squeeze()
        loss = mse(pred, data.y.to(DEVICE))
        loss.backward()
        opt.step()
        
        # Log every 2 epochs
        if epoch == 0 or (epoch + 1) % 2 == 0:
            print(f"Epoch {epoch+1:2d}/10 | Loss: {float(loss):.6f}")
        
        if float(loss) < best_loss:
            best_loss = float(loss)
    
    print(f"\n✅ Training complete! Best loss: {best_loss:.6f}")
    
    # Save model
    out_path = OUT / "chemistry_sage.pt"
    torch.save(model.state_dict(), out_path)
    print(f"💾 Model saved to: {out_path}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
