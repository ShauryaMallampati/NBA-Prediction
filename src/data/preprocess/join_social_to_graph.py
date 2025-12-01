from __future__ import annotations
import pathlib, pandas as pd
IN = pathlib.Path("artifacts/social").resolve()
OUT = pathlib.Path("artifacts/chemistry").resolve()

def main() -> None:
    path = IN / "team_social.parquet"
    if not path.exists(): return
    social = pd.read_parquet(path)
    social.to_parquet(OUT / "social_team.parquet", index=False)

if __name__ == "__main__":
    main()
