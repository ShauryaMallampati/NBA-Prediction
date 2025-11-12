"""
Comprehensive NBA Advanced Stats Scraper using nba_api
Fetches ALL available stats including:
- Advanced team metrics (offensive/defensive rating, pace, net rating)
- Player advanced stats (PER, TS%, usage rate)
- Four Factors (eFG%, TOV%, ORB%, FT Rate)
- Defensive stats (opponent stats)
- Clutch stats
- Recent form metrics
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import time
from typing import Dict
from nba_api.stats.endpoints import (
    leaguedashteamstats,
    leaguedashplayerstats,
    leaguedashteamclutch
)
from requests.exceptions import ReadTimeout, ConnectionError
import warnings
warnings.filterwarnings('ignore')

class AdvancedStatsScraper:
    """Scraper for comprehensive NBA advanced statistics"""
    
    def __init__(self):
        self.team_mapping = self._get_team_mapping()
        
    def _get_team_mapping(self) -> Dict:
        """Map team abbreviations to IDs"""
        return {
            'ATL': {'id': 1610612737, 'name': 'Atlanta Hawks'},
            'BOS': {'id': 1610612738, 'name': 'Boston Celtics'},
            'BKN': {'id': 1610612751, 'name': 'Brooklyn Nets'},
            'CHA': {'id': 1610612766, 'name': 'Charlotte Hornets'},
            'CHI': {'id': 1610612741, 'name': 'Chicago Bulls'},
            'CLE': {'id': 1610612739, 'name': 'Cleveland Cavaliers'},
            'DAL': {'id': 1610612742, 'name': 'Dallas Mavericks'},
            'DEN': {'id': 1610612743, 'name': 'Denver Nuggets'},
            'DET': {'id': 1610612765, 'name': 'Detroit Pistons'},
            'GSW': {'id': 1610612744, 'name': 'Golden State Warriors'},
            'HOU': {'id': 1610612745, 'name': 'Houston Rockets'},
            'IND': {'id': 1610612754, 'name': 'Indiana Pacers'},
            'LAC': {'id': 1610612746, 'name': 'LA Clippers'},
            'LAL': {'id': 1610612747, 'name': 'Los Angeles Lakers'},
            'MEM': {'id': 1610612763, 'name': 'Memphis Grizzlies'},
            'MIA': {'id': 1610612748, 'name': 'Miami Heat'},
            'MIL': {'id': 1610612749, 'name': 'Milwaukee Bucks'},
            'MIN': {'id': 1610612750, 'name': 'Minnesota Timberwolves'},
            'NOP': {'id': 1610612740, 'name': 'New Orleans Pelicans'},
            'NYK': {'id': 1610612752, 'name': 'New York Knicks'},
            'OKC': {'id': 1610612760, 'name': 'Oklahoma City Thunder'},
            'ORL': {'id': 1610612753, 'name': 'Orlando Magic'},
            'PHI': {'id': 1610612755, 'name': 'Philadelphia 76ers'},
            'PHX': {'id': 1610612756, 'name': 'Phoenix Suns'},
            'POR': {'id': 1610612757, 'name': 'Portland Trail Blazers'},
            'SAC': {'id': 1610612758, 'name': 'Sacramento Kings'},
            'SAS': {'id': 1610612759, 'name': 'San Antonio Spurs'},
            'TOR': {'id': 1610612761, 'name': 'Toronto Raptors'},
            'UTA': {'id': 1610612762, 'name': 'Utah Jazz'},
            'WAS': {'id': 1610612764, 'name': 'Washington Wizards'},
        }
    
    def scrape_advanced_stats(self, measure_type='Advanced') -> pd.DataFrame:
        """Scrape advanced team stats with retry logic"""
        print(f"\n📊 Scraping {measure_type} Team Stats...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                stats = leaguedashteamstats.LeagueDashTeamStats(
                    measure_type_detailed_defense=measure_type,
                    season='2024-25',
                    season_type_all_star='Regular Season',
                    per_mode_detailed='PerGame',
                    timeout=60  # Increase timeout to 60 seconds
                )
                
                time.sleep(2)  # Rate limiting
                df = stats.get_data_frames()[0]
                
                # Map team IDs to abbreviations
                team_id_to_abbr = {info['id']: abbr for abbr, info in self.team_mapping.items()}
                df['TEAM_ABBR'] = df['TEAM_ID'].map(team_id_to_abbr)
                
                print(f"✅ Scraped {measure_type} stats for {len(df)} teams ({len(df.columns)} columns)")
                
                return df
                
            except (ReadTimeout, ConnectionError) as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"⚠️  Timeout, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Error scraping {measure_type} stats after {max_retries} attempts: {e}")
                    return pd.DataFrame()
            except Exception as e:
                print(f"❌ Error scraping {measure_type} stats: {e}")
                return pd.DataFrame()
    
    def scrape_last_n_games(self, n_games: int) -> pd.DataFrame:
        """Scrape recent form (last N games) with retry logic"""
        print(f"\n📈 Scraping Last {n_games} Games Stats...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                stats = leaguedashteamstats.LeagueDashTeamStats(
                    measure_type_detailed_defense='Base',
                    season='2024-25',
                    season_type_all_star='Regular Season',
                    per_mode_detailed='PerGame',
                    last_n_games=n_games,
                    timeout=60
                )
                
                time.sleep(2)
                df = stats.get_data_frames()[0]
                
                # Map team IDs and rename columns
                team_id_to_abbr = {info['id']: abbr for abbr, info in self.team_mapping.items()}
                df['TEAM_ABBR'] = df['TEAM_ID'].map(team_id_to_abbr)
                
                # Add suffix to distinguish from full season stats
                cols_to_rename = [col for col in df.columns if col not in ['TEAM_ID', 'TEAM_NAME', 'TEAM_ABBR']]
                df = df.rename(columns={col: f"{col}_L{n_games}" for col in cols_to_rename})
                
                print(f"✅ Scraped Last {n_games} games stats for {len(df)} teams")
                
                return df
                
            except (ReadTimeout, ConnectionError) as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"⚠️  Timeout, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Error scraping last {n_games} games after {max_retries} attempts: {e}")
                    return pd.DataFrame()
            except Exception as e:
                print(f"❌ Error scraping last {n_games} games: {e}")
                return pd.DataFrame()
    
    def scrape_clutch_stats(self) -> pd.DataFrame:
        """Scrape clutch time stats with retry logic"""
        print("\n⏱️  Scraping Clutch Stats...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                stats = leaguedashteamclutch.LeagueDashTeamClutch(
                    ahead_behind='Ahead or Behind',
                    clutch_time='Last 5 Minutes',
                    point_diff=5,
                    season='2024-25',
                    season_type_all_star='Regular Season',
                    per_mode_detailed='PerGame',
                    timeout=60
                )
                
                time.sleep(2)
                df = stats.get_data_frames()[0]
                
                # Map team IDs
                team_id_to_abbr = {info['id']: abbr for abbr, info in self.team_mapping.items()}
                df['TEAM_ABBR'] = df['TEAM_ID'].map(team_id_to_abbr)
                
                # Rename columns
                rename_map = {col: f'CLUTCH_{col}' for col in df.columns 
                             if col not in ['TEAM_ID', 'TEAM_NAME', 'TEAM_ABBR']}
                df.rename(columns=rename_map, inplace=True)
                
                print(f"✅ Scraped clutch stats for {len(df)} teams")
                
                return df
                
            except (ReadTimeout, ConnectionError) as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"⚠️  Timeout, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Error scraping clutch stats after {max_retries} attempts: {e}")
                    return pd.DataFrame()
            except Exception as e:
                print(f"❌ Error scraping clutch stats: {e}")
                return pd.DataFrame()
    
    def scrape_player_advanced_stats(self) -> pd.DataFrame:
        """Scrape player advanced stats with retry logic"""
        print("\n🏀 Scraping Player Advanced Stats...")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                stats = leaguedashplayerstats.LeagueDashPlayerStats(
                    measure_type_detailed_defense='Advanced',
                    season='2024-25',
                    season_type_all_star='Regular Season',
                    per_mode_detailed='PerGame',
                    timeout=60
                )
                
                time.sleep(2)
                df = stats.get_data_frames()[0]
                
                # Map team IDs
                team_id_to_abbr = {info['id']: abbr for abbr, info in self.team_mapping.items()}
                df['TEAM_ABBR'] = df['TEAM_ID'].map(team_id_to_abbr)
                
                print(f"✅ Scraped advanced stats for {len(df)} players")
                
                return df
                
            except (ReadTimeout, ConnectionError) as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"⚠️  Timeout, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Error scraping player advanced stats after {max_retries} attempts: {e}")
                    return pd.DataFrame()
            except Exception as e:
                print(f"❌ Error scraping player advanced stats: {e}")
                return pd.DataFrame()
    
    def aggregate_team_player_stats(self, player_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate player stats to team level"""
        print("\n🔄 Aggregating player stats to team level...")
        
        if player_df.empty:
            return pd.DataFrame()
        
        # Select numeric columns for aggregation
        numeric_cols = player_df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        numeric_cols = [col for col in numeric_cols if col not in ['TEAM_ID', 'PLAYER_ID']]
        
        # Group by team and calculate mean
        team_agg = player_df.groupby('TEAM_ABBR')[numeric_cols].mean().reset_index()
        
        # Rename columns
        rename_map = {col: f'TEAM_AVG_{col}' for col in team_agg.columns if col != 'TEAM_ABBR'}
        team_agg.rename(columns=rename_map, inplace=True)
        
        print(f"✅ Aggregated stats for {len(team_agg)} teams")
        
        return team_agg
    
    def save_all_advanced_stats(self, output_dir: str = "data/advanced_stats"):
        """Scrape and save all advanced statistics"""
        
        print("\n" + "="*80)
        print("COMPREHENSIVE ADVANCED STATS SCRAPER")
        print("="*80)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        all_stats = {}
        
        # 1. Advanced Team Stats
        print("\n" + "="*80)
        advanced_df = self.scrape_advanced_stats('Advanced')
        if not advanced_df.empty:
            path = output_path / f"team_advanced_{today}.csv"
            advanced_df.to_csv(path, index=False)
            all_stats['advanced'] = advanced_df
            print(f"✅ Saved: {path}")
        time.sleep(2)
        
        # 2. Four Factors
        print("\n" + "="*80)
        four_factors_df = self.scrape_advanced_stats('Four Factors')
        if not four_factors_df.empty:
            path = output_path / f"four_factors_{today}.csv"
            four_factors_df.to_csv(path, index=False)
            all_stats['four_factors'] = four_factors_df
            print(f"✅ Saved: {path}")
        time.sleep(2)
        
        # 3. Opponent Stats (Defense)
        print("\n" + "="*80)
        opponent_df = self.scrape_advanced_stats('Opponent')
        if not opponent_df.empty:
            path = output_path / f"opponent_stats_{today}.csv"
            opponent_df.to_csv(path, index=False)
            all_stats['opponent'] = opponent_df
            print(f"✅ Saved: {path}")
        time.sleep(2)
        
        # 4. Misc Stats
        print("\n" + "="*80)
        misc_df = self.scrape_advanced_stats('Misc')
        if not misc_df.empty:
            path = output_path / f"misc_stats_{today}.csv"
            misc_df.to_csv(path, index=False)
            all_stats['misc'] = misc_df
            print(f"✅ Saved: {path}")
        time.sleep(2)
        
        # 5. Clutch Stats
        print("\n" + "="*80)
        clutch_df = self.scrape_clutch_stats()
        if not clutch_df.empty:
            path = output_path / f"clutch_{today}.csv"
            clutch_df.to_csv(path, index=False)
            all_stats['clutch'] = clutch_df
            print(f"✅ Saved: {path}")
        time.sleep(2)
        
        # 6. Recent Form (Last 5, 10, 15 games)
        for n_games in [5, 10, 15]:
            print("\n" + "="*80)
            form_df = self.scrape_last_n_games(n_games)
            if not form_df.empty:
                path = output_path / f"last_{n_games}_games_{today}.csv"
                form_df.to_csv(path, index=False)
                all_stats[f'last_{n_games}'] = form_df
                print(f"✅ Saved: {path}")
                time.sleep(2)
        
        # 7. Player Advanced Stats
        print("\n" + "="*80)
        player_df = self.scrape_player_advanced_stats()
        if not player_df.empty:
            path = output_path / f"player_advanced_{today}.csv"
            player_df.to_csv(path, index=False)
            all_stats['player_advanced'] = player_df
            print(f"✅ Saved: {path}")
            
            # Aggregate to team level
            team_player_agg = self.aggregate_team_player_stats(player_df)
            if not team_player_agg.empty:
                path = output_path / f"team_player_aggregates_{today}.csv"
                team_player_agg.to_csv(path, index=False)
                all_stats['team_player_agg'] = team_player_agg
                print(f"✅ Saved: {path}")
        
        # Merge all team stats into one comprehensive dataset
        if len(all_stats) > 0:
            print("\n" + "="*80)
            print("🔗 Merging all stats into comprehensive dataset...")
            
            # Start with advanced stats
            comprehensive = all_stats.get('advanced', pd.DataFrame())
            
            # Merge other team-level stats
            merge_keys = ['four_factors', 'opponent', 'misc', 'clutch', 'team_player_agg', 
                         'last_5', 'last_10', 'last_15']
            
            for key in merge_keys:
                if key in all_stats and not all_stats[key].empty:
                    print(f"   Merging {key}...")
                    comprehensive = comprehensive.merge(
                        all_stats[key],
                        on='TEAM_ABBR',
                        how='left',
                        suffixes=('', f'_{key}')
                    )
            
            if not comprehensive.empty:
                path = output_path / f"comprehensive_stats_{today}.csv"
                comprehensive.to_csv(path, index=False)
                print(f"\n✅ COMPREHENSIVE DATASET SAVED: {path}")
                print(f"   Total columns: {len(comprehensive.columns)}")
                print(f"   Total teams: {len(comprehensive)}")
        
        print("\n" + "="*80)
        print("✅ ADVANCED STATS SCRAPING COMPLETE!")
        print("="*80)
        
        return all_stats


if __name__ == "__main__":
    scraper = AdvancedStatsScraper()
    stats = scraper.save_all_advanced_stats()
    
    print("\n📊 Summary:")
    for key, df in stats.items():
        if not df.empty:
            print(f"  - {key}: {len(df)} rows, {len(df.columns)} columns")
