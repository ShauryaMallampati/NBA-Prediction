from __future__ import annotations
import pathlib

ROOT = pathlib.Path(".").resolve()
DATA = ROOT / "data"
ARTIFACTS = ROOT / "artifacts"
(DATA / "raw").mkdir(parents=True, exist_ok=True)
(ARTIFACTS / "features").mkdir(parents=True, exist_ok=True)
