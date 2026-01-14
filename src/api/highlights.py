"""
Client for the Basketball Highlights API (api.highlightly.net).
Used to fetch video clips for the Vision CNN model.

Provides both async and sync interfaces.
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional
import urllib.request
import urllib.parse

# Use httpx for async HTTP requests
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    import requests

logger = logging.getLogger(__name__)


class HighlightsAPI:
    BASE_URL = "https://api.highlightly.net"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HIGHLIGHTS_API_KEY")
        if not self.api_key:
            logger.warning("⚠️ No Highlights API key found. Set HIGHLIGHTS_API_KEY env var.")
            
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def get_highlights_async(self, search: Optional[str] = None) -> List[Dict]:
        """Async: Get all highlights or search by query"""
        if not HTTPX_AVAILABLE:
            return await asyncio.to_thread(self.get_highlights, search)
        
        endpoint = f"{self.BASE_URL}/highlights"
        params = {}
        if search:
            params['search'] = search
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, headers=self._get_headers(), params=params)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch highlights: {e}")
            return []

    def get_highlights(self, search: Optional[str] = None) -> List[Dict]:
        """Sync: Get all highlights or search by query"""
        endpoint = f"{self.BASE_URL}/highlights"
        params = {}
        if search:
            params['search'] = search
            
        try:
            import requests
            response = requests.get(endpoint, headers=self._get_headers(), params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch highlights: {e}")
            return []

    async def get_by_team_async(self, team_name: str) -> List[Dict]:
        """Async: Get highlights for a specific team"""
        if not HTTPX_AVAILABLE:
            return await asyncio.to_thread(self.get_by_team, team_name)
        
        safe_name = urllib.parse.quote(team_name)
        endpoint = f"{self.BASE_URL}/highlights/team/{safe_name}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch team highlights: {e}")
            return []

    def get_by_team(self, team_name: str) -> List[Dict]:
        """Sync: Get highlights for a specific team"""
        safe_name = urllib.parse.quote(team_name)
        endpoint = f"{self.BASE_URL}/highlights/team/{safe_name}"
        
        try:
            import requests
            response = requests.get(endpoint, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch team highlights: {e}")
            return []

    async def get_by_player_async(self, player_name: str) -> List[Dict]:
        """Async: Get highlights for a specific player"""
        if not HTTPX_AVAILABLE:
            return await asyncio.to_thread(self.get_by_player, player_name)
        
        safe_name = urllib.parse.quote(player_name)
        endpoint = f"{self.BASE_URL}/highlights/player/{safe_name}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(endpoint, headers=self._get_headers())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch player highlights: {e}")
            return []

    def get_by_player(self, player_name: str) -> List[Dict]:
        """Sync: Get highlights for a specific player"""
        safe_name = urllib.parse.quote(player_name)
        endpoint = f"{self.BASE_URL}/highlights/player/{safe_name}"
        
        try:
            import requests
            response = requests.get(endpoint, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch player highlights: {e}")
            return []

    def download_video(self, url: str, save_path: Path) -> bool:
        """Download video file from URL"""
        try:
            logger.info(f"Downloading video from {url}...")
            urllib.request.urlretrieve(url, save_path)
            logger.info(f"✅ Saved to {save_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to download video: {e}")
            return False


# Global instance
highlights_api = HighlightsAPI()
