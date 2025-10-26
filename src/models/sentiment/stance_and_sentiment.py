from __future__ import annotations
import pathlib, pandas as pd
from src.common.validators import guard_mock_allowed

OUT = pathlib.Path("artifacts/social").resolve()

def main() -> None:
    guard_mock_allowed()
    df = pd.DataFrame([{"team":"LAL","stance":0.15},{"team":"GSW","stance":-0.05}])
    df.to_parquet(OUT / "stance.parquet", index=False)
    print("Saved stance aggregates.")

if __name__ == "__main__":
    main()
