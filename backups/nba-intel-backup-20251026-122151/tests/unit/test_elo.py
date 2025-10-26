from src.models.pregame.elo import add_elo_features
import pandas as pd

def test_elo_shapes():
    df = pd.DataFrame([{"game_id":"g1","date":"2024-10-25","home":"LAL","away":"GSW","home_pts":100,"away_pts":90}])
    out = add_elo_features(df)
    assert "elo_p_home" in out.columns
