from __future__ import annotations
import pandas as pd

def add_elo_features(games: pd.DataFrame) -> pd.DataFrame:
    elo_df = pd.DataFrame({"game_id": games["game_id"], "elo_home": 1500.0, "elo_away": 1500.0})
    merged = games.merge(elo_df, on="game_id", how="left")
    merged["elo_p_home"] = 1.0 / (1.0 + 10 ** (-(merged["elo_home"] + 60.0 - merged["elo_away"]) / 400))
    return merged
