"""
Process historical archive data and merge with NBA API data
Handles 73 years of NBA history (1953-2026)
"""
import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import json
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArchiveProcessor:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.archive_dir = data_dir / "archive"
        self.archive3_dir = data_dir / "archive (3)"
        self.processed_dir = data_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        
        # SQLite database
        self.db_path = self.archive_dir / "nba.sqlite"
        
    def process_sqlite_games(self) -> pd.DataFrame:
        """Extract games from SQLite database (most comprehensive)"""
        logger.info("Processing SQLite database...")
        
        if not self.db_path.exists():
            logger.warning(f"SQLite database not found at {self.db_path}")
            return pd.DataFrame()
        
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get game data with team info
            query = """
            SELECT 
                g.*,
                ht.abbreviation as home_team,
                at.abbreviation as away_team
            FROM game g
            LEFT JOIN team ht ON g.home_team_id = ht.id
            LEFT JOIN team at ON g.away_team_id = at.id
            ORDER BY g.date_time
            """
            
            games = pd.read_sql_query(query, conn)
            conn.close()
            
            logger.info(f"Loaded {len(games)} games from SQLite")
            return games
            
        except Exception as e:
            logger.error(f"Error processing SQLite: {e}")
            return pd.DataFrame()
    
    def process_archive3_seasons(self) -> pd.DataFrame:
        """Process Archive 3 season files (1953-2021)"""
        logger.info("Processing Archive 3 season files...")
        
        all_games = []
        
        # Process each season file
        for season_file in sorted(self.archive3_dir.glob("season_*_detailed.csv")):
            try:
                season_data = pd.read_csv(season_file)
                season_year = season_file.stem.split('_')[1]
                season_data['season'] = season_year
                
                all_games.append(season_data)
                logger.info(f"Loaded season {season_year}: {len(season_data)} games")
                
            except Exception as e:
                logger.error(f"Error processing {season_file}: {e}")
                continue
        
        if all_games:
            games_df = pd.concat(all_games, ignore_index=True)
            logger.info(f"Total games from Archive 3: {len(games_df)}")
            return games_df
        
        return pd.DataFrame()
    
    def standardize_game_format(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Standardize game data to common format"""
        logger.info(f"Standardizing format for {source}...")
        
        # Common columns we need
        standard_cols = {
            'game_id': 'game_id',
            'date': 'date',
            'home_team': 'home_team',
            'away_team': 'away_team',
            'home_score': 'home_pts',
            'away_score': 'away_pts',
            'season': 'season',
        }
        
        standardized = pd.DataFrame()
        
        if source == 'sqlite':
            # SQLite format
            standardized['game_id'] = df['id']
            standardized['date'] = pd.to_datetime(df['date_time'])
            standardized['home_team'] = df['home_team']
            standardized['away_team'] = df['away_team']
            
        elif source == 'archive3':
            # Archive 3 format (CSV from Basketball Reference)
            standardized['date'] = pd.to_datetime(df['date'])
            standardized['home_team'] = df['team']  # Home team in 'team' column
            standardized['season'] = df['season']
            
            # Parse player stats to aggregate team stats
            # Group by date and team to get game-level stats
            game_stats = df.groupby(['date', 'team']).agg({
                'PTS': 'sum',  # Total points
                'TRB': 'sum',  # Total rebounds
                'AST': 'sum',  # Total assists
                'STL': 'sum',  # Total steals
                'BLK': 'sum',  # Total blocks
                'TOV': 'sum',  # Total turnovers
            }).reset_index()
            
            standardized = standardized.merge(
                game_stats,
                left_on=['date', 'home_team'],
                right_on=['date', 'team'],
                how='left'
            )
            
            standardized['home_pts'] = standardized['PTS']
        
        # Add derived columns
        if 'home_pts' in standardized.columns and 'away_pts' in standardized.columns:
            standardized['home_win'] = (standardized['home_pts'] > standardized['away_pts']).astype(int)
            standardized['point_diff'] = standardized['home_pts'] - standardized['away_pts']
        
        logger.info(f"Standardized {len(standardized)} games")
        return standardized
    
    def merge_with_nba_api(self, historical_games: pd.DataFrame) -> pd.DataFrame:
        """Merge historical data with recent NBA API data"""
        logger.info("Merging with NBA API data...")
        
        # Import NBA API fetcher
        try:
            from nba_api.stats.endpoints import leaguegamefinder
            
            # Get recent seasons (2022-2026)
            recent_games = []
            
            for season in ['2022-23', '2023-24', '2024-25', '2025-26']:
                try:
                    logger.info(f"Fetching {season} from NBA API...")
                    
                    games = leaguegamefinder.LeagueGameFinder(
                        season_nullable=season,
                        season_type_nullable='Regular Season'
                    ).get_data_frames()[0]
                    
                    # Convert to our format
                    games['date'] = pd.to_datetime(games['GAME_DATE'])
                    games['season'] = season
                    games['home_team'] = games['MATCHUP'].str.split(' vs. ').str[0]
                    games['home_pts'] = games['PTS']
                    
                    recent_games.append(games)
                    logger.info(f"Loaded {len(games)} games from {season}")
                    
                except Exception as e:
                    logger.warning(f"Could not fetch {season}: {e}")
                    continue
            
            if recent_games:
                recent_df = pd.concat(recent_games, ignore_index=True)
                
                # Merge with historical
                all_games = pd.concat([historical_games, recent_df], ignore_index=True)
                logger.info(f"Total games after merge: {len(all_games)}")
                return all_games
            
        except Exception as e:
            logger.warning(f"Could not merge with NBA API: {e}")
        
        return historical_games
    
    def save_processed_data(self, games: pd.DataFrame):
        """Save processed games to CSV"""
        output_path = self.processed_dir / "all_games_historical.csv"
        
        # Sort by date
        games = games.sort_values('date').reset_index(drop=True)
        
        # Save
        games.to_csv(output_path, index=False)
        logger.info(f"Saved {len(games)} games to {output_path}")
        
        # Save metadata
        metadata = {
            'total_games': len(games),
            'date_range': {
                'start': str(games['date'].min()),
                'end': str(games['date'].max())
            },
            'seasons': games['season'].nunique() if 'season' in games.columns else 'N/A',
            'teams': games['home_team'].nunique() if 'home_team' in games.columns else 'N/A',
            'processed_at': datetime.now().isoformat()
        }
        
        metadata_path = self.processed_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata: {metadata}")
    
    def run(self):
        """Main processing pipeline"""
        logger.info("=" * 80)
        logger.info("NBA ARCHIVE DATA PROCESSOR")
        logger.info("=" * 80)
        
        # Try SQLite first (most comprehensive)
        games = self.process_sqlite_games()
        
        # If SQLite fails, use Archive 3 CSV files
        if games.empty:
            logger.info("SQLite empty, falling back to Archive 3 CSVs...")
            games = self.process_archive3_seasons()
            games = self.standardize_game_format(games, 'archive3')
        else:
            games = self.standardize_game_format(games, 'sqlite')
        
        # Merge with recent NBA API data
        games = self.merge_with_nba_api(games)
        
        # Save processed data
        if not games.empty:
            self.save_processed_data(games)
            
            logger.info("=" * 80)
            logger.info("PROCESSING COMPLETE!")
            logger.info(f"Total games: {len(games)}")
            logger.info(f"Date range: {games['date'].min()} to {games['date'].max()}")
            logger.info("=" * 80)
        else:
            logger.error("No games processed!")


def main():
    """Main entry point"""
    data_dir = Path(__file__).parent.parent / "data"
    
    processor = ArchiveProcessor(data_dir)
    processor.run()


if __name__ == "__main__":
    main()
