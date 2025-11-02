#!/usr/bin/env python3
"""Automated daily data refresh script for NBA Intelligence Platform."""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import teamestimatedmetrics, playergamelog
from nba_api.live.nba.endpoints import scoreboard

from src.common.logger import setup_logger
from src.common.paths import Paths

logger = setup_logger(__name__)


def fetch_yesterday_games():
    """Fetch games from yesterday and update historical data."""
    try:
        logger.info("Fetching yesterday's games...")
        
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Get games using NBA Live API
        games = scoreboard.ScoreBoard()
        games_df = games.get_data_frames()[0]
        
        # Filter for completed games
        completed_games = games_df[games_df['GAME_STATUS_TEXT'] == 'Final'].copy()
        
        logger.info(f"Found {len(completed_games)} completed games for {yesterday}")
        
        if len(completed_games) == 0:
            logger.info("No completed games found")
            return None
        
        # Load historical data
        hist_path = Paths.PROCESSED / "all_games_historical.csv"
        if hist_path.exists():
            hist_df = pd.read_csv(hist_path)
        else:
            hist_df = pd.DataFrame()
        
        # Add new games to historical data
        # Format: date, team, season, pts, etc.
        new_games = []
        for _, game in completed_games.iterrows():
            new_games.append({
                'date': yesterday,
                'home_team': game['HOME_TEAM_ABBREVIATION'],
                'away_team': game['AWAY_TEAM_ABBREVIATION'],
                'home_score': game['HOME_TEAM_WINS'],
                'away_score': game['AWAY_TEAM_WINS'],
            })
        
        if new_games:
            new_df = pd.DataFrame(new_games)
            updated_df = pd.concat([hist_df, new_df], ignore_index=True)
            updated_df.to_csv(hist_path, index=False)
            logger.info(f"Updated {len(new_games)} games to historical data")
        
        return len(completed_games)
    
    except Exception as e:
        logger.error(f"Error fetching yesterday's games: {e}")
        return None


def update_elo_ratings():
    """Recalculate Elo ratings based on latest games."""
    try:
        logger.info("Updating Elo ratings...")
        
        # Re-run feature engineering to update Elo
        from scripts.engineer_features import FeatureEngineer
        from pathlib import Path
        
        engineer = FeatureEngineer()
        games = engineer.load_games(Paths.PROCESSED / "all_games_historical.csv")
        df = engineer.process_season(games)
        
        output_path = Paths.PROCESSED / "engineered_features.csv"
        df.to_csv(output_path, index=False)
        logger.info(f"Updated Elo ratings - saved {len(df)} games")
        
        return len(df)
    
    except Exception as e:
        logger.error(f"Error updating Elo ratings: {e}")
        return None


def main():
    """Run daily refresh."""
    logger.info("=" * 80)
    logger.info("DAILY DATA REFRESH - NBA INTELLIGENCE PLATFORM")
    logger.info("=" * 80)
    
    # Fetch yesterday's games
    games_count = fetch_yesterday_games()
    if games_count is None:
        logger.error("Failed to fetch games")
        return False
    
    if games_count == 0:
        logger.warning("No games to process")
        return True
    
    # Update Elo ratings
    features_count = update_elo_ratings()
    if features_count is None:
        logger.error("Failed to update features")
        return False
    
    logger.info("=" * 80)
    logger.info(f"Daily refresh complete!")
    logger.info(f"  - Games processed: {games_count}")
    logger.info(f"  - Features updated: {features_count}")
    logger.info("=" * 80)
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
