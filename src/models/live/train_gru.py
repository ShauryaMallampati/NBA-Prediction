from __future__ import annotations
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import torch
from torch import nn
from torch.utils.data import DataLoader
from src.models.live.dataset import LiveSeqDataset
from src.common.hardware import pick_device

DEVICE = pick_device("mps")
DATA = "artifacts/features/live_sequences.parquet"
OUT = Path("artifacts/models").resolve()
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
    print("\n" + "="*80)
    print("TRAINING GRU MODEL FOR LIVE WIN PROBABILITY")
    print("="*80)
    
    print("\n📊 Loading dataset...")
    ds = LiveSeqDataset(DATA)
    print(f"✅ Loaded {len(ds)} games")
    
    dl = DataLoader(ds, batch_size=32, shuffle=True, collate_fn=lambda b: (
        nn.utils.rnn.pad_sequence([x[0] for x in b], batch_first=True),
        torch.stack([x[1] for x in b]).float()
    ))
    
    print(f"\n🔧 Initializing model...")
    model = GRUWinProb().to(DEVICE)
    print(f"✅ Model on device: {DEVICE}")
    
    opt = torch.optim.Adam(model.parameters(), lr=1.5e-3)
    bce = nn.BCELoss()
    
    print(f"\n🚀 Training for 50 epochs...")
    model.train()
    for epoch in range(50):
        total_loss = 0
        num_batches = 0
        for x, y in dl:
            x, y = x.to(DEVICE), y.to(DEVICE)
            p = model(x)
            loss = bce(p, y)
            opt.zero_grad(); loss.backward(); opt.step()
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / num_batches
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"   Epoch {epoch + 1}/50 - Loss: {avg_loss:.4f}")
    
    print(f"\n💾 Saving model...")
    model_path = OUT / "live_gru_winprob.pt"
    torch.jit.script(model.cpu()).save(str(model_path))
    print(f"✅ Model saved to {model_path}")
    
    print("\n" + "="*80)
    print("✅ TRAINING COMPLETE!")
    print("="*80)
    print("\n▶️  Next steps:")
    print("   1. Integrate model into app/live/page.tsx")
    print("   2. Set up real-time data fetching")
    print("   3. Test live predictions during games")

if __name__ == "__main__":
    main()
