from __future__ import annotations
import torch, pathlib
from torch import nn
from torch.utils.data import DataLoader
from .dataset import LiveSeqDataset
from src.common.hardware import pick_device

DEVICE = pick_device("mps")
DATA = "artifacts/features/live_sequences.parquet"
OUT = pathlib.Path("artifacts/models").resolve()
OUT.mkdir(parents=True, exist_ok=True)

class GRUWinProb(nn.Module):
    def __init__(self, input_size=1, hidden=96):
        super().__init__()
        self.gru = nn.GRU(input_size, hidden, batch_first=True)
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x):
        out, _ = self.gru(x)
        logits = self.fc(out[:, -1, :])
        return torch.sigmoid(logits)

def main() -> None:
    ds = LiveSeqDataset(DATA)
    dl = DataLoader(ds, batch_size=32, shuffle=True, collate_fn=lambda b: (
        nn.utils.rnn.pad_sequence([x[0] for x in b], batch_first=True),
        torch.stack([x[1] for x in b]).float()
    ))
    model = GRUWinProb().to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=1.5e-3)
    bce = nn.BCELoss()
    model.train()
    for epoch in range(3):
        for x, y in dl:
            x, y = x.to(DEVICE), y.to(DEVICE)
            p = model(x)
            loss = bce(p, y)
            opt.zero_grad(); loss.backward(); opt.step()
        print(f"epoch {epoch} loss {loss.item():.4f}")
    torch.jit.script(model.cpu()).save(str(OUT / "live_gru_winprob.pt"))

if __name__ == "__main__":
    main()
