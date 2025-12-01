from __future__ import annotations
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import torch
from torch import nn
from torch.utils.data import DataLoader
from src.models.vision.dataset import ClipDataset
from src.models.vision.model import get_vision_model
from src.common.hardware import pick_device
import time
import datetime

DEVICE = pick_device("mps")
INDEX = "artifacts/vision/clips.parquet"
OUT = Path("artifacts/models").resolve()
OUT.mkdir(parents=True, exist_ok=True)

def main() -> None:
    start_time = time.time()
    print("\n==============================")
    print("👁️ TRAINING VISION CNN MODEL")
    print("==============================")
    print(f"[START] {datetime.datetime.now().isoformat()}")
    ds = ClipDataset(INDEX)
    if len(ds) == 0:
        print("No clips indexed. Use POST /game/{game_id}/clips/index to add local MP4s.")
    print(f"   Dataset size: {len(ds)}")
    dl = DataLoader(ds, batch_size=64, shuffle=True)
    print("⏳ Loading/Downloading Vision Model (MobileNetV3 Large)...")
    model = get_vision_model()
    print("✅ Model loaded")
    model.to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=8e-4)
    ce = nn.CrossEntropyLoss()
    model.train()
    from tqdm import tqdm
    import sys
    print(f"\n🚀 Training Vision Model...")
    epochs = 5 # Increased from 1 for better demo
    for epoch in range(epochs):
        print(f"\nEpoch {epoch+1}/{epochs} [{datetime.datetime.now().isoformat()}]")
        sys.stdout.flush()
        batch_pbar = tqdm(dl, desc="Processing Batches", unit="batch", file=sys.stdout)
        epoch_loss = 0
        batches = 0
        batch_start = time.time()
        for batch_idx, (x, y) in enumerate(batch_pbar):
            batch_time_start = time.time()
            print(f"[BATCH {batch_idx+1} START] {datetime.datetime.now().isoformat()}")
            x, y = x.to(DEVICE), y.to(DEVICE)
            logits = model(x)
            loss = ce(logits, y)
            opt.zero_grad(); loss.backward(); opt.step()
            epoch_loss += loss.item()
            batches += 1
            batch_pbar.set_postfix({"Loss": f"{loss.item():.4f}"})
            # Extra verbose logs
            print(f"Batch {batch_idx+1}: Loss={loss.item():.4f} | Device={DEVICE}")
            if torch.cuda.is_available():
                print(f"   CUDA Memory Allocated: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
            print(f"   Batch Time: {time.time()-batch_time_start:.2f}s")
            print(f"[BATCH {batch_idx+1} END] {datetime.datetime.now().isoformat()}")
            # Heartbeat every second
            heartbeat_start = time.time()
            while time.time() - heartbeat_start < 1:
                print(f"[HEARTBEAT] Training Vision CNN... {datetime.datetime.now().isoformat()}")
                time.sleep(1)
    print(f"\n💾 Saving Vision Model after {epochs} epochs...")
    torch.jit.script(model.cpu()).save(str(OUT / "vision_mnv3.pt"))
    print(f"✅ Saved to {OUT / 'vision_mnv3.pt'}")
    print(f"Total Training Time: {time.time()-start_time:.2f}s [{datetime.datetime.now().isoformat()}]")

if __name__ == "__main__":
    main()
