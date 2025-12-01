from __future__ import annotations
import pathlib, pandas as pd, numpy as np
from src.common.validators import guard_mock_allowed

OUT = pathlib.Path("artifacts/features").resolve()

def main() -> None:
    guard_mock_allowed()
    seqs = []
    for gid in ["g1", "g2"]:
        for t in range(1, 101):
            seqs.append({"game_id": gid, "t": t, "score_diff": np.random.randint(-15, 15), "fouls_h": 3, "fouls_a": 2})
    pd.DataFrame(seqs).to_parquet(OUT / "live_sequences.parquet", index=False)

if __name__ == "__main__":
    main()
