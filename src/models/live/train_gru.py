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
from src.models.live.model import GRUWinProb
from src.common.hardware import pick_device

# Define constants
DEVICE = pick_device("mps")
DATA = Path("data/live_sequences.parquet")
OUT = Path("artifacts/models")
OUT.mkdir(parents=True, exist_ok=True)

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
    
    from tqdm import tqdm
    
    # Use tqdm for epoch progress
    epoch_pbar = tqdm(range(50), desc="Training Epochs", unit="epoch")
    
    for epoch in epoch_pbar:
        total_loss = 0
        num_batches = 0
        
        # Use tqdm for batch progress (optional, might be too fast for small datasets)
        # batch_pbar = tqdm(dl, desc=f"Epoch {epoch+1}", leave=False)
        
        for x, y in dl:
            x, y = x.to(DEVICE), y.to(DEVICE)
            p = model(x)
            loss = bce(p, y)
            opt.zero_grad(); loss.backward(); opt.step()
            total_loss += loss.item()
            num_batches += 1
        
        avg_loss = total_loss / num_batches
        
        # Update progress bar description with loss
        epoch_pbar.set_postfix({"Loss": f"{avg_loss:.4f}"})
    
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
