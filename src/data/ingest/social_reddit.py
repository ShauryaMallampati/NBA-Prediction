from __future__ import annotations
import os, base64, httpx, pathlib, json
from src.common.validators import require_keys

OUT = pathlib.Path("data/raw/reddit").resolve()

def token(cid: str, secret: str) -> str:
    auth = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    r = httpx.post("https://www.reddit.com/api/v1/access_token",
                   data={"grant_type": "client_credentials"},
                   headers={"Authorization": f"Basic {auth}", "User-Agent": "nba-intel/0.1"})
    r.raise_for_status()
    return r.json()["access_token"]

def search_bball(tok: str) -> dict:
    r = httpx.get("https://oauth.reddit.com/r/nba/new",
                  headers={"Authorization": f"bearer {tok}", "User-Agent": "nba-intel/0.1"},
                  params={"limit": 50})
    r.raise_for_status()
    return r.json()

def main() -> None:
    require_keys(["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"])
    OUT.mkdir(parents=True, exist_ok=True)
    tok = token(os.environ["REDDIT_CLIENT_ID"], os.environ["REDDIT_CLIENT_SECRET"])
    (OUT / "seed.json").write_text(json.dumps(search_bball(tok)))

if __name__ == "__main__":
    main()
