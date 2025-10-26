from __future__ import annotations
import pathlib, pandas as pd
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

@router.get("/predictions")
def get_predictions(date: str = Query(..., pattern=r"\d{4}-\d{2}-\d{2}")):
    feats_path = pathlib.Path("artifacts/features/pregame.parquet")
    model_path = pathlib.Path("artifacts/models/pregame_lgbm_calibrated.joblib")
    if not feats_path.exists() or not model_path.exists():
        raise HTTPException(400, "Artifacts missing. Run make data and make train-pregame.")
    import joblib
    calib = joblib.load(model_path)
    df = pd.read_parquet(feats_path)
    df = df[df["date"] == date] if "date" in df.columns else df
    games = []
    if df.empty:
        return {"date": date, "games": games}
    X = df[["elo_home", "elo_away", "home_adv_flag"]]
    p = calib.predict_proba(X)[:, 1]
    for row, prob in zip(df.to_dict("records"), p):
        games.append({
            "game_id": row["game_id"],
            "home": row["home"], "away": row["away"],
            "p_home": float(prob),
            "top_features": ["elo_home", "elo_away", "home_adv_flag"]
        })
    return {"date": date, "games": games}
