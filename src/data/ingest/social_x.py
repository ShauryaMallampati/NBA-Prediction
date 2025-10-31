from __future__ import annotations
import os, pathlib, httpx, json, time
from src.common.validators import require_keys

OUT = pathlib.Path("data/raw/x").resolve()

def search(query: str, bearer: str) -> dict:
    url = "https://api.x.com/2/tweets/search/recent"
    r = httpx.get(url, params={"query": query, "max_results": 50},
                  headers={"Authorization": f"Bearer {bearer}"}, timeout=20.0)
    r.raise_for_status()
    return r.json()

def main() -> None:
    require_keys(["X_BEARER_TOKEN"])
    OUT.mkdir(parents=True, exist_ok=True)
    data = search("NBA (game OR injury OR lineup) lang:en -is:retweet", os.environ["X_BEARER_TOKEN"])
    (OUT / "seed.json").write_text(json.dumps(data))
    time.sleep(1.0)

if __name__ == "__main__":
    main()
