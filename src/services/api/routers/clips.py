from __future__ import annotations
import asyncio
import pathlib
import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.post("/game/{game_id}/clips/index")
async def index_clips(game_id: str, filepath: str):
    idx = pathlib.Path("artifacts/vision/clips.parquet")
    if not pathlib.Path(filepath).exists():
        raise HTTPException(400, "File path does not exist")
    
    # Use asyncio.to_thread to avoid blocking the event loop
    df = await asyncio.to_thread(pd.read_parquet, idx)
    df.loc[len(df)] = {"game_id": game_id, "filepath": filepath, "start_s": 0, "end_s": 5, "label": "unknown"}
    await asyncio.to_thread(df.to_parquet, idx, index=False)
    return {"ok": True}

@router.get("/game/{game_id}/clips")
async def list_clips(game_id: str):
    idx = pathlib.Path("artifacts/vision/clips.parquet")
    if not idx.exists():
        raise HTTPException(400, "No clip index. Run make data or index via API.")
    
    # Use asyncio.to_thread to avoid blocking the event loop
    df = await asyncio.to_thread(pd.read_parquet, idx)
    return {"clips": df[df.game_id == game_id].to_dict("records")}
