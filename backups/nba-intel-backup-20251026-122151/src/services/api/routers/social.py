from __future__ import annotations
import pathlib, pandas as pd
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

@router.get("/social/team")
def team_social(date: str = Query(...)):
    path = pathlib.Path("artifacts/social/team_social.parquet")
    if not path.exists(): raise HTTPException(400, "Run make social-build or enable sentiment.")
    df = pd.read_parquet(path)
    return {"date": date, "teams": df.to_dict("records")}
