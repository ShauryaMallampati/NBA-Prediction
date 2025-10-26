from __future__ import annotations
import os, sys
from typing import Iterable

class RealDataGuard(Exception):
    """Raised when real-data requirements are not satisfied."""

def require_keys(keys: Iterable[str]) -> None:
    missing = [k for k in keys if not os.getenv(k)]
    require_real = os.getenv("REQUIRE_REAL_DATA", "true").lower() == "true"
    allow_mock = os.getenv("ALLOW_MOCK_DATA", "false").lower() == "true"
    if require_real and missing:
        checklist = "\n".join(f"- Set {k} (see KEYS.md)" for k in missing)
        raise RealDataGuard(
            "Real-data mode enabled but required keys are missing:\n"
            f"{checklist}\nSet ALLOW_MOCK_DATA=true to continue with mock CSVs."
        )
    if missing and not require_real and not allow_mock:
        print(f"[WARN] Missing keys: {missing}", file=sys.stderr)

def guard_mock_allowed() -> None:
    """Abort if mock generation attempted while mock not allowed."""
    allow_mock = os.getenv("ALLOW_MOCK_DATA", "false").lower() == "true"
    require_real = os.getenv("REQUIRE_REAL_DATA", "true").lower() == "true"
    if require_real and not allow_mock:
        raise RealDataGuard("Mock generation attempted while REQUIRE_REAL_DATA=true and ALLOW_MOCK_DATA=false.")
