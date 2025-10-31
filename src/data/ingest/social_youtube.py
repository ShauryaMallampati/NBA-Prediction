from __future__ import annotations
import os, httpx, pathlib, json
from src.common.validators import require_keys

OUT = pathlib.Path("data/raw/youtube").resolve()

def search(query: str, key: str) -> dict:
    url = "https://www.googleapis.com/youtube/v3/search"
    r = httpx.get(url, params={"part": "snippet", "q": query, "type": "video", "maxResults": 25, "key": key}, timeout=20.0)
    r.raise_for_status()
    return r.json()

def main() -> None:
    require_keys(["YOUTUBE_API_KEY"])
    OUT.mkdir(parents=True, exist_ok=True)
    data = search("NBA highlights", os.environ["YOUTUBE_API_KEY"])
    (OUT / "seed.json").write_text(json.dumps(data))

if __name__ == "__main__":
    main()
