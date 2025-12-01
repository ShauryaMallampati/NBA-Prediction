from __future__ import annotations
import pathlib, pandas as pd
from src.common.validators import guard_mock_allowed

OUT = pathlib.Path("artifacts/chemistry").resolve()
OUT.mkdir(parents=True, exist_ok=True)

def main() -> None:
    guard_mock_allowed()
    edges = pd.DataFrame([
        {"u":"LAL:LeBron","v":"LAL:AD","co_min":500,"assists":120},
        {"u":"GSW:Steph","v":"GSW:Klay","co_min":600,"assists":180},
    ])
    edges.to_parquet(OUT / "lineup_edges.parquet", index=False)

if __name__ == "__main__":
    main()
