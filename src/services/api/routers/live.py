from __future__ import annotations
import asyncio
import pathlib
import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/game/{game_id}/live")
async def live_stream(game_id: str):
    seq_path = pathlib.Path("artifacts/features/live_sequences.parquet")
    model_path = pathlib.Path("artifacts/models/live_gru_winprob.pt")
    if not seq_path.exists() or not model_path.exists():
        raise HTTPException(400, "Live artifacts missing. Run make data and make train-live.")
    import torch
    
    # Load model and data off the event loop to avoid blocking
    model = await asyncio.to_thread(torch.jit.load, str(model_path))
    df = await asyncio.to_thread(pd.read_parquet, seq_path)
    
    df = df[df.game_id == game_id].sort_values("t")
    if df.empty: 
        return {"game_id": game_id, "winprob": []}
    x = torch.tensor(df[["score_diff"]].values, dtype=torch.float32).unsqueeze(0)
    p = float(model(x).detach().numpy().squeeze())
    return {"game_id": game_id, "p_home": p}
