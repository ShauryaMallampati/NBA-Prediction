from __future__ import annotations
import pathlib, pandas as pd
from src.common.validators import guard_mock_allowed

OUT = pathlib.Path("artifacts/social").resolve()
OUT.mkdir(parents=True, exist_ok=True)

def main() -> None:
    guard_mock_allowed()
    df = pd.DataFrame([
        {"team":"LAL","sent_mean":0.12,"sent_std":0.35,"buzz_z95":2.1},
        {"team":"GSW","sent_mean":-0.05,"sent_std":0.28,"buzz_z95":1.3},
    ])
    df.to_parquet(OUT / "team_social.parquet", index=False)

if __name__ == "__main__":
    main()
