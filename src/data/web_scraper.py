"""
Web Scraper for Injury Reports and News
Scrapes public sources (no API key needed!)
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

class InjuryScraper:
    """Scrape injury reports from public sources"""
    
    def __init__(self):
        self.cache_dir = Path("data/injuries")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def scrape_espn_injuries(self) -> pd.DataFrame:
        """
        Scrape injury data from ESPN (public, no login required)
        Note: This is for educational purposes. Check ESPN's robots.txt
        """
        url = "https://www.espn.com/nba/injuries"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Parse injury table (structure may change)
            injuries = []
            
            # ESPN typically uses tables for injury reports
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        injuries.append({
                            'player': cols[0].text.strip(),
                            'team': cols[1].text.strip() if len(cols) > 1 else '',
                            'status': cols[2].text.strip() if len(cols) > 2 else '',
                            'injury': cols[3].text.strip() if len(cols) > 3 else ''
                        })
            
            df = pd.DataFrame(injuries)
            
            # Cache
            cache_file = self.cache_dir / "espn_injuries.parquet"
            df.to_parquet(cache_file)
            
            logger.info(f"✅ Scraped {len(df)} injury reports")
            return df
            
        except Exception as e:
            logger.error(f"Failed to scrape ESPN injuries: {e}")
            return pd.DataFrame()
    
    def get_cached_injuries(self) -> pd.DataFrame:
        """Load cached injury data"""
        cache_file = self.cache_dir / "espn_injuries.parquet"
        if cache_file.exists():
            return pd.read_parquet(cache_file)
        return pd.DataFrame()

# Global instance
injury_scraper = InjuryScraper()
