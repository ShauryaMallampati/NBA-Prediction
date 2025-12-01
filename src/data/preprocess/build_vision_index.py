from __future__ import annotations
import pathlib, pandas as pd
OUT = pathlib.Path("artifacts/vision").resolve()
OUT.mkdir(parents=True, exist_ok=True)

def main() -> None:
    pd.DataFrame(columns=["game_id","filepath","start_s","end_s","label"]).to_parquet(OUT / "clips.parquet", index=False)

if __name__ == "__main__":
    main()
