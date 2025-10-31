"""Seed all real data."""

import sys
from pathlib import Path

import pandas as pd

from src.common.config import load_config, settings
from src.common.logger import setup_logger
from src.common.paths import Paths
from src.common.validators import validate_api_keys, validate_data_exists
from src.data.ingest.nba_stats_client import NBAStatsClient

logger = setup_logger(__name__)


def seed_nba_data() -> None:
    """Seed NBA game and player data."""
    logger.info("Seeding NBA data...")

    config = load_config()
    seasons = (
        config["data"]["seasons"]["train"]
        + config["data"]["seasons"]["validate"]
        + config["data"]["seasons"]["test"]
    )

    client = NBAStatsClient()

    all_games = []
    for season in seasons:
        logger.info(f"Fetching season {season}...")
        games_df = client.get_season_games(season)
        all_games.append(games_df)

        if settings.simplified_mode and len(games_df) > 100:
            logger.info(f"SIMPLIFIED_MODE: limiting to first 100 games")
            games_df = games_df.head(100)

    # Combine and save
    games_df = pd.concat(all_games, ignore_index=True)
    output_path = Paths.RAW / "games.parquet"
    games_df.to_parquet(output_path, index=False)
    logger.info(f"✓ Saved {len(games_df)} games to {output_path}")

    # Validate
    validate_data_exists(output_path, min_rows=100)


def main() -> None:
    """Main seeding entry point."""
    logger.info("=" * 70)
    logger.info("NBA INTELLIGENCE PLATFORM - DATA SEEDING")
    logger.info("=" * 70)

    try:
        # Validate keys first
        validate_api_keys()

        # Seed data
        seed_nba_data()

        logger.info("=" * 70)
        logger.info("✓ Data seeding complete!")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        if settings.require_real_data:
            sys.exit(1)


if __name__ == "__main__":
    main()
