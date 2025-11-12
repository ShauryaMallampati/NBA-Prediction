"""
ESPN Stats Scraper - Alternative reliable source for NBA stats
Scrapes team and player statistics from ESPN.com
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from pathlib import Path
import json
import warnings
warnings.filterwarnings('ignore')

class ESPNStatsScraper:
    """Scraper for ESPN NBA statistics"""
    
    def __init__(self):
        self.base_url = "https://www.espn.com/nba"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.team_mapping = self._get_team_mapping()
    
    def _get_team_mapping(self):
        """Map team names to abbreviations"""
        return {
            'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN',
            'Charlotte Hornets': 'CHA', 'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
            'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN', 'Detroit Pistons': 'DET',
            'Golden State Warriors': 'GSW', 'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
            'LA Clippers': 'LAC', 'Los Angeles Lakers': 'LAL', 'Memphis Grizzlies': 'MEM',
            'Miami Heat': 'MIA', 'Milwaukee Bucks': 'MIL', 'Minnesota Timberwolves': 'MIN',
            'New Orleans Pelicans': 'NOP', 'New York Knicks': 'NYK', 'Oklahoma City Thunder': 'OKC',
            'Orlando Magic': 'ORL', 'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHX',
            'Portland Trail Blazers': 'POR', 'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SAS',
            'Toronto Raptors': 'TOR', 'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS'
        }
    
    def scrape_team_stats(self):
        """Scrape team statistics from ESPN"""
        print("\n📊 Scraping ESPN Team Stats...")
        
        try:
            url = f"{self.base_url}/stats/team"
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find stat tables
            tables = soup.find_all('table', {'class': 'Table'})
            
            if tables:
                # Usually first table has team names, second has stats
                dfs = pd.read_html(str(response.content))
                
                if len(dfs) >= 2:
                    # Merge team names with stats
                    teams_df = dfs[0]
                    stats_df = dfs[1]
                    
                    if len(teams_df) == len(stats_df):
                        merged = pd.concat([teams_df, stats_df], axis=1)
                        
                        # Map to abbreviations
                        if 'Team' in merged.columns:
                            merged['TEAM_ABBR'] = merged['Team'].map(self.team_mapping)
                        
                        print(f"✅ Scraped {len(merged)} teams, {len(merged.columns)} columns")
                        return merged
            
            print("⚠️  Could not parse ESPN stats tables")
            return pd.DataFrame()
            
        except Exception as e:
            print(f"❌ Error scraping ESPN stats: {e}")
            return pd.DataFrame()
    
    def scrape_standings(self):
        """Scrape current standings"""
        print("\n🏆 Scraping ESPN Standings...")
        
        try:
            url = f"{self.base_url}/standings"
            response = requests.get(url, headers=self.headers, timeout=15)
            
            # Parse standings tables
            dfs = pd.read_html(response.content)
            
            all_standings = []
            for df in dfs:
                if 'W' in df.columns and 'L' in df.columns:
                    # Map team names
                    if df.columns[0] in ['Team', 'Tm']:
                        team_col = df.columns[0]
                        df['TEAM_ABBR'] = df[team_col].map(self.team_mapping)
                        all_standings.append(df)
            
            if all_standings:
                # Concatenate all standings
                standings = pd.concat(all_standings, ignore_index=True)
                print(f"✅ Scraped standings for {len(standings)} teams")
                return standings
            
            print("⚠️  No standings data found")
            return pd.DataFrame()
            
        except Exception as e:
            print(f"❌ Error scraping standings: {e}")
            return pd.DataFrame()
    
    def scrape_all_stats(self):
        """Scrape all available ESPN stats"""
        print("\n" + "="*80)
        print("ESPN COMPREHENSIVE STATS SCRAPER")
        print("="*80)
        
        all_dfs = []
        
        # 1. Team stats
        team_stats = self.scrape_team_stats()
        if not team_stats.empty:
            all_dfs.append(team_stats)
        
        time.sleep(2)
        
        # 2. Standings
        standings = self.scrape_standings()
        if not standings.empty:
            all_dfs.append(standings)
        
        # Merge all
        if all_dfs:
            print(f"\n🔄 Merging {len(all_dfs)} datasets...")
            
            merged = all_dfs[0]
            for df in all_dfs[1:]:
                if 'TEAM_ABBR' in df.columns and 'TEAM_ABBR' in merged.columns:
                    merged = merged.merge(df, on='TEAM_ABBR', how='outer', suffixes=('', '_dup'))
            
            # Remove duplicates
            merged = merged.loc[:, ~merged.columns.duplicated()]
            
            # Save
            output_dir = Path('data/advanced_stats')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            date_str = datetime.now().strftime('%Y-%m-%d')
            output_file = output_dir / f'espn_stats_{date_str}.csv'
            
            merged.to_csv(output_file, index=False)
            
            print(f"\n✅ ESPN SCRAPING COMPLETE!")
            print(f"   Teams: {len(merged)}")
            print(f"   Features: {len(merged.columns)}")
            print(f"   Saved to: {output_file}")
            
            return merged
        else:
            print("\n❌ No ESPN data scraped")
            return pd.DataFrame()


def main():
    """Main execution"""
    scraper = ESPNStatsScraper()
    df = scraper.scrape_all_stats()
    
    if not df.empty:
        print("\n📊 Sample columns:", df.columns.tolist()[:10])
        return 0
    else:
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
