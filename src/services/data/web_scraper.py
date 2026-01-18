"""
Robust Web Scraper for NBA Injuries and News.
Acts as an augmentation layer to RapidAPI, ensuring fresh data between games.
"""

import requests
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class NBAWebScraper:
    """Scrapes public NBA data sources for real-time updates."""
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_injuries(self, team_name: str = None) -> List[Dict]:
        """Scrape partial injury report from CBS Sports."""
        url = "https://www.cbssports.com/nba/injuries/"
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200: return []
            soup = BeautifulSoup(response.content, 'html.parser')
            injuries = []
            
            # Simple row parser for demo
            for row in soup.find_all('tr', class_='TableBase-bodyTr'):
                cols = row.find_all('td')
                if len(cols) >= 4:
                    injuries.append({
                        "player": cols[0].get_text(strip=True),
                        "status": cols[3].get_text(strip=True),
                        "source": "CBS Scrape"
                    })
            
            if team_name:
                return [i for i in injuries if team_name.lower() in str(i).lower()]
            return injuries
        except:
            return []

    def get_team_news(self, team_name: str) -> List[Dict]:
        """Scrape news from ESPN search for now (more robust than team pages)."""
        slug = team_name.lower().replace(" ", "-")
        url = f"https://www.espn.com/search/_/q/{slug}"
        news = []
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            for link in soup.find_all('a', href=True):
                if '/nba/story' in link['href']:
                    news.append({
                        "headline": link.get_text(strip=True), 
                        "link": link['href'],
                        "team": team_name,
                        "source": "ESPN"
                    })
                    if len(news) >= 3: break
            
            # Save to Memory
            if news:
                self.save_to_memory(news, f"news_{slug}")
                
            return news
        except Exception as e:
            logger.error(f"News scrape failed: {e}")
            return []

    def save_to_memory(self, data: List[Dict], prefix: str):
        """Save data to local JSON and Supabase (Memory)."""
        # 1. Local File
        import json
        import os
        from pathlib import Path
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mem_dir = Path("data/news_archive")
            mem_dir.mkdir(parents=True, exist_ok=True)
            
            filename = mem_dir / f"{prefix}_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
                
            # 2. Supabase Backend
            try:
                from src.common.supabase_client import get_supabase_client
                client = get_supabase_client()
                client.insert_news(data)
            except Exception as e:
                logger.warning(f"Supabase memory save failed: {e}")
                
        except Exception as e:
            logger.error(f"Local memory save failed: {e}")

nba_scraper = NBAWebScraper()
