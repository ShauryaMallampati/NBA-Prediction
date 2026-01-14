"""
Client for the Basketball Highlights API (api.highlightly.net).
Used to fetch video clips for the Vision CNN model.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
import urllib.parse
import httpx
import aiofiles

logger = logging.getLogger(__name__)

class HighlightsAPI:
    BASE_URL = "https://api.highlightly.net"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HIGHLIGHTS_API_KEY")
        if not self.api_key:
            logger.warning("⚠️ No Highlights API key found. Set HIGHLIGHTS_API_KEY env var.")
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def close(self):
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
            
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def get_highlights(self, search: Optional[str] = None) -> List[Dict]:
        """Get all highlights or search by query"""
        endpoint = f"{self.BASE_URL}/highlights"
        params = {}
        if search:
            params['search'] = search
            
        try:
            response = await self.client.get(endpoint, headers=self._get_headers(), params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch highlights: {e}")
            return []

    async def get_by_team(self, team_name: str) -> List[Dict]:
        """Get highlights for a specific team"""
        # URL encode the team name
        safe_name = urllib.parse.quote(team_name)
        endpoint = f"{self.BASE_URL}/highlights/team/{safe_name}"
        
        try:
            response = await self.client.get(endpoint, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch team highlights: {e}")
            return []

    async def get_by_player(self, player_name: str) -> List[Dict]:
        """Get highlights for a specific player"""
        safe_name = urllib.parse.quote(player_name)
        endpoint = f"{self.BASE_URL}/highlights/player/{safe_name}"
        
        try:
            response = await self.client.get(endpoint, headers=self._get_headers())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch player highlights: {e}")
            return []

    async def download_video(self, url: str, save_path: Path) -> bool:
        """Download video file from URL"""
        try:
            logger.info(f"Downloading video from {url}...")
            async with self.client.stream("GET", url) as response:
                response.raise_for_status()
                async with aiofiles.open(save_path, 'wb') as f:
                    async for chunk in response.aiter_bytes():
                        await f.write(chunk)
            logger.info(f"✅ Saved to {save_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to download video: {e}")
            return False

# Global instance
highlights_api = HighlightsAPI()
