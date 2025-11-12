"""
NBA Player Tracking & Hustle Stats Scraper
Uses nba_api to fetch:
- Speed & Distance (player movement)
- Touches & Possessions
- Drives, Passes, Assists
- Deflections, Loose Balls Recovered
- Screen Assists, Charges Drawn
- Box Outs, Contested Shots
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import time
from typing import Dict, List
from nba_api.stats.endpoints import (
    leaguehustlestatsplayer,
    leaguedashptstats
)
from requests.exceptions import ReadTimeout, ConnectionError
import warnings
warnings.filterwarnings('ignore')

class PlayerTrackingScraper:
    """Scraper for NBA player tracking and hustle statistics"""
    
    def __init__(self):
        self.team_mapping = self._get_team_mapping()
        
    def _get_team_mapping(self) -> Dict:
        """Map team IDs to abbreviations"""
        return {
            1610612737: 'ATL', 1610612738: 'BOS', 1610612751: 'BKN',
            1610612766: 'CHA', 1610612741: 'CHI', 1610612739: 'CLE',
            1610612742: 'DAL', 1610612743: 'DEN', 1610612765: 'DET',
            1610612744: 'GSW', 1610612745: 'HOU', 1610612754: 'IND',
            1610612746: 'LAC', 1610612747: 'LAL', 1610612763: 'MEM',
            1610612748: 'MIA', 1610612749: 'MIL', 1610612750: 'MIN',
            1610612740: 'NOP', 1610612752: 'NYK', 1610612760: 'OKC',
            1610612753: 'ORL', 1610612755: 'PHI', 1610612756: 'PHX',
            1610612757: 'POR', 1610612758: 'SAC', 1610612759: 'SAS',
            1610612761: 'TOR', 1610612762: 'UTA', 1610612764: 'WAS'
        }
    
    def scrape_hustle_stats(self) -> pd.DataFrame:
        """Scrape hustle stats (deflections, loose balls, screen assists, etc.)"""
        print("\n💪 Scraping Hustle Stats...")
        
        try:
            hustle = leaguehustlestatsplayer.LeagueHustleStatsPlayer(
                season='2024-25',
                season_type_all_star='Regular Season',
                per_mode_simple='PerGame'
            )
            
            df = hustle.get_data_frames()[0]
            
            # Map team IDs
            df['TEAM_ABBR'] = df['TEAM_ID'].map(self.team_mapping)
            
            print(f"✅ Scraped hustle stats for {len(df)} players")
            print(f"   Metrics: DEFLECTIONS, LOOSE_BALLS_RECOVERED, CHARGES_DRAWN, SCREEN_ASSISTS, etc.")
            
            return df
            
        except Exception as e:
            print(f"❌ Error scraping hustle stats: {e}")
            return pd.DataFrame()
    
    def scrape_speed_distance(self) -> pd.DataFrame:
        """Scrape speed & distance tracking"""
        print("\n🏃 Scraping Speed & Distance Stats...")
        
        try:
            tracking = leaguedashptstats.LeagueDashPtStats(
                season='2024-25',
                season_type_all_star='Regular Season',
                per_mode_simple='PerGame',
                pt_measure_type='SpeedDistance'
            )
            
            df = tracking.get_data_frames()[0]
            df['TEAM_ABBR'] = df['TEAM_ID'].map(self.team_mapping)
            
            print(f"✅ Scraped speed/distance for {len(df)} players")
            print(f"   Metrics: DIST_FEET, DIST_MILES, AVG_SPEED, etc.")
            
            return df
            
        except Exception as e:
            print(f"❌ Error scraping speed/distance: {e}")
            return pd.DataFrame()
    
    def scrape_touches(self) -> pd.DataFrame:
        """Scrape touches & possessions tracking"""
        print("\n🤲 Scraping Touches & Possessions...")
        
        try:
            tracking = leaguedashptstats.LeagueDashPtStats(
                season='2024-25',
                season_type_all_star='Regular Season',
                per_mode_simple='PerGame',
                pt_measure_type='Possessions'
            )
            
            df = tracking.get_data_frames()[0]
            df['TEAM_ABBR'] = df['TEAM_ID'].map(self.team_mapping)
            
            print(f"✅ Scraped touches for {len(df)} players")
            print(f"   Metrics: TOUCHES, FRONT_CT_TOUCHES, TIME_OF_POSS, AVG_DRIB_PER_TOUCH, etc.")
            
            return df
            
        except Exception as e:
            print(f"❌ Error scraping touches: {e}")
            return pd.DataFrame()
    
    def scrape_drives(self) -> pd.DataFrame:
        """Scrape drive stats"""
        print("\n🚗 Scraping Drive Stats...")
        
        try:
            tracking = leaguedashptstats.LeagueDashPtStats(
                season='2024-25',
                season_type_all_star='Regular Season',
                per_mode_simple='PerGame',
                pt_measure_type='Drives'
            )
            
            df = tracking.get_data_frames()[0]
            df['TEAM_ABBR'] = df['TEAM_ID'].map(self.team_mapping)
            
            print(f"✅ Scraped drives for {len(df)} players")
            print(f"   Metrics: DRIVES, DRIVE_FG_PCT, DRIVE_FT_PCT, DRIVE_PTS, etc.")
            
            return df
            
        except Exception as e:
            print(f"❌ Error scraping drives: {e}")
            return pd.DataFrame()
    
    def scrape_catch_shoot(self) -> pd.DataFrame:
        """Scrape catch & shoot stats"""
        print("\n🎯 Scraping Catch & Shoot Stats...")
        
        try:
            tracking = leaguedashptstats.LeagueDashPtStats(
                season='2024-25',
                season_type_all_star='Regular Season',
                per_mode_simple='PerGame',
                pt_measure_type='CatchShoot'
            )
            
            df = tracking.get_data_frames()[0]
            df['TEAM_ABBR'] = df['TEAM_ID'].map(self.team_mapping)
            
            print(f"✅ Scraped catch & shoot for {len(df)} players")
            print(f"   Metrics: CATCH_SHOOT_FGM, CATCH_SHOOT_FG_PCT, CATCH_SHOOT_PTS, etc.")
            
            return df
            
        except Exception as e:
            print(f"❌ Error scraping catch & shoot: {e}")
            return pd.DataFrame()
    
    def scrape_pull_up(self) -> pd.DataFrame:
        """Scrape pull-up shot stats"""
        print("\n🏀 Scraping Pull-Up Stats...")
        
        try:
            tracking = leaguedashptstats.LeagueDashPtStats(
                season='2024-25',
                season_type_all_star='Regular Season',
                per_mode_simple='PerGame',
                pt_measure_type='PullUpShot'
            )
            
            df = tracking.get_data_frames()[0]
            df['TEAM_ABBR'] = df['TEAM_ID'].map(self.team_mapping)
            
            print(f"✅ Scraped pull-up for {len(df)} players")
            
            return df
            
        except Exception as e:
            print(f"❌ Error scraping pull-up: {e}")
            return pd.DataFrame()
    
    def aggregate_to_team_level(self, player_df: pd.DataFrame, prefix: str) -> pd.DataFrame:
        """Aggregate player stats to team level"""
        if player_df.empty:
            return pd.DataFrame()
        
        # Select numeric columns
        numeric_cols = player_df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        numeric_cols = [col for col in numeric_cols if col not in ['TEAM_ID', 'PLAYER_ID']]
        
        # Aggregate by team
        team_agg = player_df.groupby('TEAM_ABBR')[numeric_cols].mean().reset_index()
        
        # Rename with prefix
        rename_map = {col: f'{prefix}_{col}' for col in team_agg.columns if col != 'TEAM_ABBR'}
        team_agg.rename(columns=rename_map, inplace=True)
        
        return team_agg
    
    def save_all_tracking_stats(self, output_dir: str = "data/tracking"):
        """Scrape and save all tracking statistics"""
        
        print("\n" + "="*80)
        print("NBA PLAYER TRACKING & HUSTLE STATS SCRAPER")
        print("="*80)
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        all_stats = {}
        
        # 1. Hustle Stats
        hustle_df = self.scrape_hustle_stats()
        if not hustle_df.empty:
            hustle_df.to_csv(output_path / f"player_hustle_{today}.csv", index=False)
            team_hustle = self.aggregate_to_team_level(hustle_df, 'HUSTLE')
            if not team_hustle.empty:
                team_hustle.to_csv(output_path / f"team_hustle_{today}.csv", index=False)
                all_stats['hustle'] = team_hustle
        time.sleep(2)
        
        # 2. Speed & Distance
        speed_df = self.scrape_speed_distance()
        if not speed_df.empty:
            speed_df.to_csv(output_path / f"player_speed_{today}.csv", index=False)
            team_speed = self.aggregate_to_team_level(speed_df, 'SPEED')
            if not team_speed.empty:
                team_speed.to_csv(output_path / f"team_speed_{today}.csv", index=False)
                all_stats['speed'] = team_speed
        time.sleep(2)
        
        # 3. Touches & Possessions
        touches_df = self.scrape_touches()
        if not touches_df.empty:
            touches_df.to_csv(output_path / f"player_touches_{today}.csv", index=False)
            team_touches = self.aggregate_to_team_level(touches_df, 'TOUCH')
            if not team_touches.empty:
                team_touches.to_csv(output_path / f"team_touches_{today}.csv", index=False)
                all_stats['touches'] = team_touches
        time.sleep(2)
        
        # 4. Drives
        drives_df = self.scrape_drives()
        if not drives_df.empty:
            drives_df.to_csv(output_path / f"player_drives_{today}.csv", index=False)
            team_drives = self.aggregate_to_team_level(drives_df, 'DRIVE')
            if not team_drives.empty:
                team_drives.to_csv(output_path / f"team_drives_{today}.csv", index=False)
                all_stats['drives'] = team_drives
        time.sleep(2)
        
        # 5. Catch & Shoot
        catch_df = self.scrape_catch_shoot()
        if not catch_df.empty:
            catch_df.to_csv(output_path / f"player_catch_shoot_{today}.csv", index=False)
            team_catch = self.aggregate_to_team_level(catch_df, 'CATCH')
            if not team_catch.empty:
                team_catch.to_csv(output_path / f"team_catch_shoot_{today}.csv", index=False)
                all_stats['catch_shoot'] = team_catch
        time.sleep(2)
        
        # 6. Pull-Up Shots
        pullup_df = self.scrape_pull_up()
        if not pullup_df.empty:
            pullup_df.to_csv(output_path / f"player_pullup_{today}.csv", index=False)
            team_pullup = self.aggregate_to_team_level(pullup_df, 'PULLUP')
            if not team_pullup.empty:
                team_pullup.to_csv(output_path / f"team_pullup_{today}.csv", index=False)
                all_stats['pullup'] = team_pullup
        
        # Merge all tracking stats
        if all_stats:
            print("\n🔗 Merging all tracking stats...")
            comprehensive = all_stats['hustle']
            
            for key in ['speed', 'touches', 'drives', 'catch_shoot', 'pullup']:
                if key in all_stats:
                    comprehensive = comprehensive.merge(
                        all_stats[key],
                        on='TEAM_ABBR',
                        how='outer'
                    )
            
            path = output_path / f"comprehensive_tracking_{today}.csv"
            comprehensive.to_csv(path, index=False)
            print(f"✅ COMPREHENSIVE TRACKING SAVED: {path}")
            print(f"   Columns: {len(comprehensive.columns)}, Teams: {len(comprehensive)}")
        
        print("\n" + "="*80)
        print("✅ TRACKING STATS SCRAPING COMPLETE!")
        print("="*80)
        
        return all_stats


if __name__ == "__main__":
    scraper = PlayerTrackingScraper()
    stats = scraper.save_all_tracking_stats()
    
    print("\n📊 Summary:")
    for key, df in stats.items():
        if not df.empty:
            print(f"  - {key}: {len(df)} teams, {len(df.columns)} columns")
