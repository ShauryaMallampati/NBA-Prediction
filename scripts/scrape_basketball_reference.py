"""
Basketball-Reference Advanced Stats Scraper
More reliable alternative to NBA Stats API which is timing out.
Scrapes all advanced metrics directly from Basketball-Reference HTML.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class BasketballReferenceScraper:
    """Scraper for Basketball-Reference (more reliable than NBA Stats API)"""
    
    def __init__(self):
        self.base_url = "https://www.basketball-reference.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.team_mapping = self._get_team_mapping()
        
    def _get_team_mapping(self):
        """Map team abbreviations to Basketball-Reference codes"""
        return {
            'ATL': 'ATL', 'BOS': 'BOS', 'BKN': 'BRK', 'CHA': 'CHO', 'CHI': 'CHI',
            'CLE': 'CLE', 'DAL': 'DAL', 'DEN': 'DEN', 'DET': 'DET', 'GSW': 'GSW',
            'HOU': 'HOU', 'IND': 'IND', 'LAC': 'LAC', 'LAL': 'LAL', 'MEM': 'MEM',
            'MIA': 'MIA', 'MIL': 'MIL', 'MIN': 'MIN', 'NOP': 'NOP', 'NYK': 'NYK',
            'OKC': 'OKC', 'ORL': 'ORL', 'PHI': 'PHI', 'PHX': 'PHO', 'POR': 'POR',
            'SAC': 'SAC', 'SAS': 'SAS', 'TOR': 'TOR', 'UTA': 'UTA', 'WAS': 'WAS'
        }
    
    def scrape_team_stats(self, season='2025'):
        """Scrape comprehensive team stats from Basketball-Reference"""
        print(f"\n📊 Scraping Team Stats for {season} season...")
        
        try:
            url = f"{self.base_url}/leagues/NBA_{season}.html"
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all stat tables
            tables = soup.find_all('table', {'class': 'stats_table'})
            
            all_stats = {}
            
            for table in tables:
                table_id = table.get('id', '')
                if not table_id:
                    continue
                    
                print(f"  Processing table: {table_id}")
                
                # Extract headers
                headers = []
                header_row = table.find('thead').find_all('tr')[-1]
                for th in header_row.find_all('th'):
                    header = th.get('data-stat', th.text.strip())
                    if header and header not in ['ranker', 'DUMMY']:
                        headers.append(header)
                
                # Extract rows
                rows = []
                tbody = table.find('tbody')
                if tbody:
                    for tr in tbody.find_all('tr', class_=lambda x: x != 'thead'):
                        if 'class' in tr.attrs and 'thead' in tr.attrs['class']:
                            continue
                        
                        row_data = {}
                        for td in tr.find_all(['td', 'th']):
                            stat = td.get('data-stat')
                            if stat:
                                row_data[stat] = td.text.strip()
                        
                        if row_data and 'team_name' in row_data:
                            rows.append(row_data)
                
                if rows:
                    df = pd.DataFrame(rows)
                    
                    # Store by table type
                    if table_id not in all_stats:
                        all_stats[table_id] = df
                    
                time.sleep(1)  # Be nice to the server
            
            # Merge all tables
            if all_stats:
                # Start with first table
                merged = list(all_stats.values())[0]
                
                # Merge remaining tables
                for table_name, df in list(all_stats.items())[1:]:
                    if 'team_name' in df.columns and 'team_name' in merged.columns:
                        merged = merged.merge(df, on='team_name', how='outer', suffixes=('', f'_{table_name}'))
                
                # Map to standard abbreviations
                abbr_map = {v: k for k, v in self.team_mapping.items()}
                if 'team_name' in merged.columns:
                    # Extract abbreviation from team name or use mapping
                    merged['TEAM_ABBR'] = merged['team_name'].apply(
                        lambda x: abbr_map.get(x, x[:3].upper())
                    )
                
                print(f"✅ Scraped {len(merged)} teams with {len(merged.columns)} columns")
                return merged
            else:
                print("❌ No tables found")
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error scraping team stats: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def scrape_advanced_stats(self, season='2025'):
        """Scrape advanced team statistics"""
        print(f"\n📈 Scraping Advanced Stats for {season}...")
        
        try:
            url = f"{self.base_url}/leagues/NBA_{season}.html"
            response = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find advanced stats table (usually has 'advanced' in the comment)
            comments = soup.find_all(string=lambda text: isinstance(text, str) and 'advanced' in text.lower())
            
            for comment in comments:
                # Parse the commented HTML
                try:
                    comment_soup = BeautifulSoup(comment, 'html.parser')
                    table = comment_soup.find('table')
                    
                    if table:
                        df = pd.read_html(str(table))[0]
                        
                        # Clean up multi-level columns
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = ['_'.join(col).strip() for col in df.columns.values]
                        
                        # Remove asterisks and clean team names
                        if 'Team' in df.columns:
                            df['Team'] = df['Team'].str.replace('*', '', regex=False)
                            df['TEAM_ABBR'] = df['Team'].apply(self._map_team_name)
                        
                        print(f"✅ Scraped advanced stats: {len(df)} teams, {len(df.columns)} columns")
                        return df
                except:
                    continue
            
            print("⚠️  Advanced stats table not found in comments, trying direct scrape...")
            
            # Try direct table scrape
            tables = pd.read_html(url)
            for df in tables:
                if len(df) > 25 and len(df.columns) > 15:  # Likely the team stats table
                    if 'Team' in df.columns or 'Tm' in df.columns:
                        team_col = 'Team' if 'Team' in df.columns else 'Tm'
                        df['TEAM_ABBR'] = df[team_col].apply(self._map_team_name)
                        print(f"✅ Scraped stats: {len(df)} teams, {len(df.columns)} columns")
                        return df
            
            print("❌ Could not find advanced stats table")
            return pd.DataFrame()
            
        except Exception as e:
            print(f"❌ Error scraping advanced stats: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def _map_team_name(self, team_name):
        """Map Basketball-Reference team name to abbreviation"""
        if not team_name or pd.isna(team_name):
            return None
        
        team_name = str(team_name).replace('*', '').strip()
        
        # Direct mapping
        abbr_map = {v: k for k, v in self.team_mapping.items()}
        if team_name in abbr_map:
            return abbr_map[team_name]
        
        # Name-based mapping
        name_map = {
            'Atlanta Hawks': 'ATL', 'Boston Celtics': 'BOS', 'Brooklyn Nets': 'BKN',
            'Charlotte Hornets': 'CHA', 'Chicago Bulls': 'CHI', 'Cleveland Cavaliers': 'CLE',
            'Dallas Mavericks': 'DAL', 'Denver Nuggets': 'DEN', 'Detroit Pistons': 'DET',
            'Golden State Warriors': 'GSW', 'Houston Rockets': 'HOU', 'Indiana Pacers': 'IND',
            'Los Angeles Clippers': 'LAC', 'Los Angeles Lakers': 'LAL', 'Memphis Grizzlies': 'MEM',
            'Miami Heat': 'MIA', 'Milwaukee Bucks': 'MIL', 'Minnesota Timberwolves': 'MIN',
            'New Orleans Pelicans': 'NOP', 'New York Knicks': 'NYK', 'Oklahoma City Thunder': 'OKC',
            'Orlando Magic': 'ORL', 'Philadelphia 76ers': 'PHI', 'Phoenix Suns': 'PHX',
            'Portland Trail Blazers': 'POR', 'Sacramento Kings': 'SAC', 'San Antonio Spurs': 'SAS',
            'Toronto Raptors': 'TOR', 'Utah Jazz': 'UTA', 'Washington Wizards': 'WAS'
        }
        
        return name_map.get(team_name, team_name[:3].upper())
    
    def scrape_all_stats(self, season='2025'):
        """Scrape all available stats"""
        print("\n" + "="*80)
        print("BASKETBALL-REFERENCE COMPREHENSIVE STATS SCRAPER")
        print("="*80)
        
        all_dfs = []
        
        # 1. Basic team stats
        basic_stats = self.scrape_team_stats(season)
        if not basic_stats.empty:
            all_dfs.append(basic_stats)
        
        time.sleep(2)
        
        # 2. Advanced stats
        advanced_stats = self.scrape_advanced_stats(season)
        if not advanced_stats.empty:
            all_dfs.append(advanced_stats)
        
        # Merge all dataframes
        if all_dfs:
            print(f"\n🔄 Merging {len(all_dfs)} datasets...")
            
            merged = all_dfs[0]
            for df in all_dfs[1:]:
                if 'TEAM_ABBR' in df.columns and 'TEAM_ABBR' in merged.columns:
                    merged = merged.merge(df, on='TEAM_ABBR', how='outer', suffixes=('', '_dup'))
            
            # Remove duplicate columns
            merged = merged.loc[:, ~merged.columns.duplicated()]
            
            # Save to file
            output_dir = Path('data/advanced_stats')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            date_str = datetime.now().strftime('%Y-%m-%d')
            output_file = output_dir / f'bball_ref_stats_{date_str}.csv'
            
            merged.to_csv(output_file, index=False)
            
            print(f"\n✅ SCRAPING COMPLETE!")
            print(f"   Teams: {len(merged)}")
            print(f"   Features: {len(merged.columns)}")
            print(f"   Saved to: {output_file}")
            
            return merged
        else:
            print("\n❌ No data scraped")
            return pd.DataFrame()


def main():
    """Main execution"""
    scraper = BasketballReferenceScraper()
    df = scraper.scrape_all_stats(season='2025')
    
    if not df.empty:
        print("\n📊 Sample of scraped data:")
        print(df[['TEAM_ABBR'] + [col for col in df.columns if col != 'TEAM_ABBR'][:5]].head())
        return 0
    else:
        print("\n❌ Failed to scrape data")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
