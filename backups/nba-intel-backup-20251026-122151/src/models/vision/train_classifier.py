from __future__ import annotations
import torch, pathlib
from torch import nn
from torch.utils.data import DataLoader
from torchvision.models import mobilenet_v3_small
from .dataset import ClipDataset
from src.common.hardware import pick_device

DEVICE = pick_device("mps")
INDEX = "artifacts/vision/clips.parquet"
OUT = pathlib.Path("artifacts/models").resolve()
OUT.mkdir(parents=True, exist_ok=True)

def main() -> None:
    ds = ClipDataset(INDEX)
    if len(ds) == 0:
        print("No clips indexed. Use POST /game/{game_id}/clips/index to add local MP4s.")
    dl = DataLoader(ds, batch_size=64, shuffle=True)
    model = mobilenet_v3_small(weights=None)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, 5)
    model.to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=8e-4)
    ce = nn.CrossEntropyLoss()
    model.train()
    for epoch in range(1):
        for x, y in dl:
            x, y = x.to(DEVICE), y.to(DEVICE)
            logits = model(x)
            loss = ce(logits, y)
            opt.zero_grad(); loss.backward(); opt.step()
    torch.jit.script(model.cpu()).save(str(OUT / "vision_mnv3.pt"))

if __name__ == "__main__":
    main()
