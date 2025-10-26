"""Audit API keys and test connectivity."""

import sys
from typing import Dict, Tuple

import httpx

from src.common.config import settings
from src.common.logger import setup_logger

logger = setup_logger(__name__)


def test_nba_stats_api() -> Tuple[bool, str]:
    """Test NBA Stats API connectivity."""
    if not settings.nba_stats_api_key:
        return False, "Key not set"

    try:
        # Test with RapidAPI endpoint
        response = httpx.get(
            "https://api-nba-v1.p.rapidapi.com/status",
            headers={
                "X-RapidAPI-Key": settings.nba_stats_api_key,
                "X-RapidAPI-Host": "api-nba-v1.p.rapidapi.com",
            },
            timeout=10,
        )
        if response.status_code == 200:
            return True, "Connected"
        return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]


def test_ors_api() -> Tuple[bool, str]:
    """Test OpenRouteService API."""
    if not settings.ors_api_key:
        return False, "Key not set"

    try:
        response = httpx.get(
            f"https://api.openrouteservice.org/v2/directions/driving-car?api_key={settings.ors_api_key}&start=8.681495,49.41461&end=8.687872,49.420318",
            timeout=10,
        )
        if response.status_code == 200:
            return True, "Connected"
        return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]


def test_twitter_api() -> Tuple[bool, str]:
    """Test Twitter API v2."""
    if not settings.x_bearer_token:
        return False, "Key not set"

    try:
        response = httpx.get(
            "https://api.twitter.com/2/tweets/search/recent?query=NBA&max_results=10",
            headers={"Authorization": f"Bearer {settings.x_bearer_token}"},
            timeout=10,
        )
        if response.status_code == 200:
            return True, "Connected"
        return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]


def test_reddit_api() -> Tuple[bool, str]:
    """Test Reddit API."""
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        return False, "Keys not set"

    try:
        response = httpx.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(settings.reddit_client_id, settings.reddit_client_secret),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": "nba-intel/0.1"},
            timeout=10,
        )
        if response.status_code == 200:
            return True, "Connected"
        return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]


def test_youtube_api() -> Tuple[bool, str]:
    """Test YouTube Data API."""
    if not settings.youtube_api_key:
        return False, "Key not set"

    try:
        response = httpx.get(
            f"https://www.googleapis.com/youtube/v3/search?part=snippet&q=NBA&key={settings.youtube_api_key}&maxResults=1",
            timeout=10,
        )
        if response.status_code == 200:
            return True, "Connected"
        return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)[:50]


def run_audit() -> None:
    """Run full API key audit."""
    print("\n" + "=" * 70)
    print("NBA INTELLIGENCE PLATFORM - API KEY AUDIT")
    print("=" * 70 + "\n")

    tests: Dict[str, Tuple[bool, str]] = {
        "NBA Stats API": test_nba_stats_api(),
        "OpenRouteService": test_ors_api(),
    }

    if settings.enable_sentiment:
        tests.update(
            {
                "Twitter/X API": test_twitter_api(),
                "Reddit API": test_reddit_api(),
                "YouTube API": test_youtube_api(),
            }
        )

    # Print results
    all_passed = True
    for name, (passed, message) in tests.items():
        status = "✓" if passed else "✗"
        color = "\033[92m" if passed else "\033[91m"
        reset = "\033[0m"
        print(f"{color}{status}{reset} {name:25} {message}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 70)

    if all_passed:
        print("✓ All API keys validated successfully!")
        print("=" * 70 + "\n")
        sys.exit(0)
    else:
        print("✗ Some API keys are missing or invalid.")
        print("  See KEYS.md for instructions on obtaining keys.")
        print("=" * 70 + "\n")
        if settings.require_real_data:
            sys.exit(1)


if __name__ == "__main__":
    run_audit()
