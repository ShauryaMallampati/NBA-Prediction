"""
ESPN Data Scraper
Fetches injury reports, player stats, team stats, and advanced metrics from ESPN
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
import time
from typing import Dict, List, Optional
import re

class ESPNScraper:
    """Scraper for ESPN NBA data including injuries, stats, and team info"""
    
    def __init__(self):
        self.base_url = "https://www.espn.com/nba"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        self.team_mapping = self._get_team_mapping()
        
    def _get_team_mapping(self) -> Dict[str, Dict]:
        """Map team abbreviations to ESPN IDs and full names"""
        return {
            'ATL': {'id': 1, 'name': 'Atlanta Hawks', 'espn_name': 'hawks'},
            'BOS': {'id': 2, 'name': 'Boston Celtics', 'espn_name': 'celtics'},
            'BKN': {'id': 17, 'name': 'Brooklyn Nets', 'espn_name': 'nets'},
            'CHA': {'id': 30, 'name': 'Charlotte Hornets', 'espn_name': 'hornets'},
            'CHI': {'id': 4, 'name': 'Chicago Bulls', 'espn_name': 'bulls'},
            'CLE': {'id': 5, 'name': 'Cleveland Cavaliers', 'espn_name': 'cavaliers'},
            'DAL': {'id': 6, 'name': 'Dallas Mavericks', 'espn_name': 'mavericks'},
            'DEN': {'id': 7, 'name': 'Denver Nuggets', 'espn_name': 'nuggets'},
            'DET': {'id': 8, 'name': 'Detroit Pistons', 'espn_name': 'pistons'},
            'GSW': {'id': 9, 'name': 'Golden State Warriors', 'espn_name': 'warriors'},
            'HOU': {'id': 10, 'name': 'Houston Rockets', 'espn_name': 'rockets'},
            'IND': {'id': 11, 'name': 'Indiana Pacers', 'espn_name': 'pacers'},
            'LAC': {'id': 12, 'name': 'LA Clippers', 'espn_name': 'clippers'},
            'LAL': {'id': 13, 'name': 'Los Angeles Lakers', 'espn_name': 'lakers'},
            'MEM': {'id': 29, 'name': 'Memphis Grizzlies', 'espn_name': 'grizzlies'},
            'MIA': {'id': 14, 'name': 'Miami Heat', 'espn_name': 'heat'},
            'MIL': {'id': 15, 'name': 'Milwaukee Bucks', 'espn_name': 'bucks'},
            'MIN': {'id': 16, 'name': 'Minnesota Timberwolves', 'espn_name': 'timberwolves'},
            'NOP': {'id': 3, 'name': 'New Orleans Pelicans', 'espn_name': 'pelicans'},
            'NYK': {'id': 18, 'name': 'New York Knicks', 'espn_name': 'knicks'},
            'OKC': {'id': 25, 'name': 'Oklahoma City Thunder', 'espn_name': 'thunder'},
            'ORL': {'id': 19, 'name': 'Orlando Magic', 'espn_name': 'magic'},
            'PHI': {'id': 20, 'name': 'Philadelphia 76ers', 'espn_name': 'sixers'},
            'PHX': {'id': 21, 'name': 'Phoenix Suns', 'espn_name': 'suns'},
            'POR': {'id': 22, 'name': 'Portland Trail Blazers', 'espn_name': 'blazers'},
            'SAC': {'id': 23, 'name': 'Sacramento Kings', 'espn_name': 'kings'},
            'SAS': {'id': 24, 'name': 'San Antonio Spurs', 'espn_name': 'spurs'},
            'TOR': {'id': 28, 'name': 'Toronto Raptors', 'espn_name': 'raptors'},
            'UTA': {'id': 26, 'name': 'Utah Jazz', 'espn_name': 'jazz'},
            'WAS': {'id': 27, 'name': 'Washington Wizards', 'espn_name': 'wizards'},
        }
    
    def scrape_injury_report(self) -> pd.DataFrame:
        """Scrape current injury report from ESPN"""
        print("\n🏥 Scraping ESPN injury reports...")
        
        try:
            url = f"{self.base_url}/injuries"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            injuries = []
            
            # Find all injury sections
            injury_sections = soup.find_all('div', class_='ResponsiveTable')
            
            for section in injury_sections:
                # Get team name
                team_header = section.find_previous('div', class_='Table__Title')
                if not team_header:
                    continue
                    
                team_name = team_header.text.strip()
                
                # Find team abbreviation
                team_abbr = None
                for abbr, info in self.team_mapping.items():
                    if info['name'] in team_name:
                        team_abbr = abbr
                        break
                
                if not team_abbr:
                    continue
                
                # Parse injury table
                rows = section.find_all('tr')[1:]  # Skip header
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        player_name = cells[0].text.strip()
                        position = cells[1].text.strip()
                        injury_status = cells[2].text.strip()
                        injury_details = cells[3].text.strip()
                        
                        injuries.append({
                            'team': team_abbr,
                            'player_name': player_name,
                            'position': position,
                            'status': injury_status,
                            'details': injury_details,
                            'scraped_at': datetime.now().isoformat()
                        })
            
            df = pd.DataFrame(injuries)
            print(f"✅ Found {len(df)} injury reports")
            return df
            
        except Exception as e:
            print(f"❌ Error scraping injuries: {e}")
            return pd.DataFrame()
    
    def scrape_team_stats(self) -> pd.DataFrame:
        """Scrape team statistics from ESPN"""
        print("\n📊 Scraping ESPN team stats...")
        
        try:
            url = f"{self.base_url}/stats/team"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            team_stats = []
            
            # Find stats table
            table = soup.find('table', class_='Table')
            if not table:
                print("❌ Could not find stats table")
                return pd.DataFrame()
            
            rows = table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 10:
                    team_name = cells[0].text.strip()
                    
                    # Find team abbreviation
                    team_abbr = None
                    for abbr, info in self.team_mapping.items():
                        if info['name'] in team_name or abbr in team_name:
                            team_abbr = abbr
                            break
                    
                    if not team_abbr:
                        continue
                    
                    team_stats.append({
                        'team': team_abbr,
                        'games_played': self._safe_float(cells[1].text),
                        'ppg': self._safe_float(cells[2].text),
                        'rpg': self._safe_float(cells[3].text),
                        'apg': self._safe_float(cells[4].text),
                        'fg_pct': self._safe_float(cells[5].text),
                        'three_pt_pct': self._safe_float(cells[6].text),
                        'ft_pct': self._safe_float(cells[7].text),
                        'scraped_at': datetime.now().isoformat()
                    })
            
            df = pd.DataFrame(team_stats)
            print(f"✅ Scraped stats for {len(df)} teams")
            return df
            
        except Exception as e:
            print(f"❌ Error scraping team stats: {e}")
            return pd.DataFrame()
    
    def scrape_player_stats(self, limit: int = 100) -> pd.DataFrame:
        """Scrape top player statistics"""
        print(f"\n🏀 Scraping ESPN player stats (top {limit})...")
        
        try:
            url = f"{self.base_url}/stats/player"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            player_stats = []
            
            # Find stats table
            table = soup.find('table', class_='Table')
            if not table:
                print("❌ Could not find player stats table")
                return pd.DataFrame()
            
            rows = table.find_all('tr')[1:limit+1]  # Skip header, limit rows
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 12:
                    player_name = cells[0].text.strip()
                    team = cells[1].text.strip()
                    
                    player_stats.append({
                        'player_name': player_name,
                        'team': team,
                        'games_played': self._safe_float(cells[2].text),
                        'ppg': self._safe_float(cells[3].text),
                        'rpg': self._safe_float(cells[4].text),
                        'apg': self._safe_float(cells[5].text),
                        'fg_pct': self._safe_float(cells[6].text),
                        'three_pt_pct': self._safe_float(cells[7].text),
                        'ft_pct': self._safe_float(cells[8].text),
                        'mpg': self._safe_float(cells[9].text),
                        'scraped_at': datetime.now().isoformat()
                    })
            
            df = pd.DataFrame(player_stats)
            print(f"✅ Scraped stats for {len(df)} players")
            return df
            
        except Exception as e:
            print(f"❌ Error scraping player stats: {e}")
            return pd.DataFrame()
    
    def scrape_standings(self) -> pd.DataFrame:
        """Scrape current NBA standings"""
        print("\n📈 Scraping ESPN standings...")
        
        try:
            url = f"{self.base_url}/standings"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            standings = []
            
            # Find standings tables
            tables = soup.find_all('table', class_='Table')
            
            for table in tables[:2]:  # Eastern and Western conferences
                rows = table.find_all('tr')[1:]  # Skip header
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 9:
                        team_name = cells[0].text.strip()
                        
                        # Find team abbreviation
                        team_abbr = None
                        for abbr, info in self.team_mapping.items():
                            if info['name'] in team_name or abbr in team_name:
                                team_abbr = abbr
                                break
                        
                        if not team_abbr:
                            continue
                        
                        standings.append({
                            'team': team_abbr,
                            'wins': self._safe_int(cells[1].text),
                            'losses': self._safe_int(cells[2].text),
                            'win_pct': self._safe_float(cells[3].text),
                            'games_back': cells[4].text.strip(),
                            'home_record': cells[5].text.strip(),
                            'away_record': cells[6].text.strip(),
                            'conference_record': cells[7].text.strip(),
                            'last_10': cells[8].text.strip(),
                            'scraped_at': datetime.now().isoformat()
                        })
            
            df = pd.DataFrame(standings)
            print(f"✅ Scraped standings for {len(df)} teams")
            return df
            
        except Exception as e:
            print(f"❌ Error scraping standings: {e}")
            return pd.DataFrame()
    
    def _safe_float(self, text: str) -> Optional[float]:
        """Safely convert text to float"""
        try:
            return float(text.strip().replace('%', ''))
        except:
            return None
    
    def _safe_int(self, text: str) -> Optional[int]:
        """Safely convert text to int"""
        try:
            return int(text.strip())
        except:
            return None
    
    def save_all_data(self, output_dir: str = "data/espn"):
        """Scrape and save all ESPN data"""
        print("\n" + "="*80)
        print("ESPN DATA SCRAPER - COMPREHENSIVE DATA COLLECTION")
        print("="*80)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Scrape injuries
        injuries_df = self.scrape_injury_report()
        if not injuries_df.empty:
            injuries_path = output_path / f"injuries_{today}.csv"
            injuries_df.to_csv(injuries_path, index=False)
            print(f"✅ Saved injuries to {injuries_path}")
        
        time.sleep(2)  # Be nice to ESPN servers
        
        # Scrape team stats
        team_stats_df = self.scrape_team_stats()
        if not team_stats_df.empty:
            team_stats_path = output_path / f"team_stats_{today}.csv"
            team_stats_df.to_csv(team_stats_path, index=False)
            print(f"✅ Saved team stats to {team_stats_path}")
        
        time.sleep(2)
        
        # Scrape player stats
        player_stats_df = self.scrape_player_stats(limit=100)
        if not player_stats_df.empty:
            player_stats_path = output_path / f"player_stats_{today}.csv"
            player_stats_df.to_csv(player_stats_path, index=False)
            print(f"✅ Saved player stats to {player_stats_path}")
        
        time.sleep(2)
        
        # Scrape standings
        standings_df = self.scrape_standings()
        if not standings_df.empty:
            standings_path = output_path / f"standings_{today}.csv"
            standings_df.to_csv(standings_path, index=False)
            print(f"✅ Saved standings to {standings_path}")
        
        print("\n" + "="*80)
        print("✅ ESPN DATA SCRAPING COMPLETE!")
        print("="*80)
        
        return {
            'injuries': injuries_df,
            'team_stats': team_stats_df,
            'player_stats': player_stats_df,
            'standings': standings_df
        }


if __name__ == "__main__":
    scraper = ESPNScraper()
    data = scraper.save_all_data()
    
    print("\n📊 Summary:")
    print(f"  - Injuries: {len(data['injuries'])} reports")
    print(f"  - Team Stats: {len(data['team_stats'])} teams")
    print(f"  - Player Stats: {len(data['player_stats'])} players")
    print(f"  - Standings: {len(data['standings'])} teams")
