from __future__ import annotations
import pathlib, pandas as pd
from fastapi import APIRouter, HTTPException
router = APIRouter()

@router.post("/game/{game_id}/clips/index")
def index_clips(game_id: str, filepath: str):
    idx = pathlib.Path("artifacts/vision/clips.parquet")
    if not pathlib.Path(filepath).exists():
        raise HTTPException(400, "File path does not exist")
    df = pd.read_parquet(idx)
    df.loc[len(df)] = {"game_id": game_id, "filepath": filepath, "start_s": 0, "end_s": 5, "label": "unknown"}
    df.to_parquet(idx, index=False)
    return {"ok": True}

@router.get("/game/{game_id}/clips")
def list_clips(game_id: str):
    idx = pathlib.Path("artifacts/vision/clips.parquet")
    if not idx.exists():
        raise HTTPException(400, "No clip index. Run make data or index via API.")
    df = pd.read_parquet(idx)
    return {"clips": df[df.game_id == game_id].to_dict("records")}
