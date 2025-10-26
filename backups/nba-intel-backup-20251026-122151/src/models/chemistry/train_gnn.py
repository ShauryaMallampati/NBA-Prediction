from __future__ import annotations
import torch, pathlib
from torch import nn
from torch_geometric.nn import SAGEConv
from .graph_utils import build_lineup_graph
from src.common.hardware import pick_device
from src.common.validators import guard_mock_allowed

DEVICE = pick_device("mps")
EDGES = "artifacts/chemistry/lineup_edges.parquet"
OUT = pathlib.Path("artifacts/models").resolve()
OUT.mkdir(parents=True, exist_ok=True)

class SAGE(torch.nn.Module):
    def __init__(self, in_dim=8, hidden=96):
        super().__init__()
        self.conv1 = SAGEConv(in_dim, hidden)
        self.conv2 = SAGEConv(hidden, hidden)
        self.lin = nn.Linear(hidden, 1)

    def forward(self, x, edge_index):
        h = torch.relu(self.conv1(x, edge_index))
        h = torch.relu(self.conv2(h, edge_index))
        return self.lin(h)

def main() -> None:
    guard_mock_allowed()
    data = build_lineup_graph(EDGES)
    model = SAGE(in_dim=data.x.size(1), hidden=96).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    mse = nn.MSELoss()
    for epoch in range(10):
        model.train(); opt.zero_grad()
        pred = model(data.x.to(DEVICE), data.edge_index.to(DEVICE)).squeeze()
        y = torch.zeros_like(pred)
        loss = mse(pred, y)
        loss.backward(); opt.step()
        if epoch % 5 == 0: print("epoch", epoch, "loss", float(loss))
    torch.jit.script(model.cpu()).save(str(OUT / "chemistry_sage.pt"))

if __name__ == "__main__":
    main()
