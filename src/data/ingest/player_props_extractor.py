"""Player props feature extraction pipeline.

This module orchestrates the extraction of player statistics and
builds training data for player props models (PTS, AST, REB, STEALS, BLOCKS).

Workflow:
1. Fetch season games and player-game statistics
2. Compute per-player features (recent avg, trend, consistency)
3. Compute opponent matchup difficulty
4. Export features to parquet for model training
"""

from typing import Dict, List, Optional
import pathlib
import pandas as pd
import numpy as np
from datetime import datetime

from src.common.logger import setup_logger
from src.data.ingest.nba_stats_client import NBAStatsClient

logger = setup_logger(__name__)


class PlayerPropsExtractor:
    """Extract player props features for model training."""
    
    PROPS = ["PTS", "AST", "REB", "STEALS", "BLOCKS"]
    OUTPUT_DIR = pathlib.Path("artifacts/player_props_data")
    
    def __init__(self):
        """Initialize extractor."""
        self.client = NBAStatsClient()
        self.output_dir = self.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_season_features(
        self,
        season: int,
        min_games_played: int = 10
    ) -> pd.DataFrame:
        """Extract player props features for all players in a season.
        
        Args:
            season: Season year (e.g., 2023)
            min_games_played: Minimum games required to include player
            
        Returns:
            DataFrame with columns:
            - player_id, player_name, season
            - {PTS,AST,REB,STEALS,BLOCKS}_{season_avg, recent_avg, recent_trend, consistency}
            - games_played
        """
        logger.info(f"Extracting features for season {season}...")
        
        # Fetch season games
        df_games = self.client.get_season_games(season)
        logger.info(f"Found {len(df_games)} games in season {season}")
        
        # Fetch player statistics for all games
        all_stats = []
        for game_id in df_games["game_id"].unique()[:10]:  # Sample first 10 games for now
            try:
                df_stats = self.client.get_game_statistics(game_id)
                if not df_stats.empty:
                    df_stats["game_id"] = game_id
                    all_stats.append(df_stats)
            except Exception as e:
                logger.warning(f"Error fetching stats for game {game_id}: {e}")
        
        if not all_stats:
            logger.error("No statistics found!")
            return pd.DataFrame()
        
        df_all_stats = pd.concat(all_stats, ignore_index=True)
        
        # Group by player and compute features
        player_features = []
        for player_id, player_group in df_all_stats.groupby("player_id"):
            player_name = player_group["player_name"].iloc[0]
            games_played = len(player_group)
            
            if games_played < min_games_played:
                continue
            
            logger.debug(f"Computing features for {player_name} ({games_played} games)")
            
            # Build features using client
            features = self.client.build_player_props_features(
                player_id=int(player_id),
                player_name=player_name,
                season=season,
                last_n_games=10
            )
            
            features.update({
                "player_id": int(player_id),
                "player_name": player_name,
                "season": season,
                "games_played": games_played,
            })
            
            player_features.append(features)
        
        df_features = pd.DataFrame(player_features)
        logger.info(f"Extracted features for {len(df_features)} players")
        
        # Save to parquet
        output_path = self.output_dir / f"player_props_{season}.parquet"
        df_features.to_parquet(output_path, index=False)
        logger.info(f"Saved to {output_path}")
        
        return df_features
    
    def extract_game_context_features(
        self,
        df_games: pd.DataFrame
    ) -> pd.DataFrame:
        """Add game context features to games DataFrame.
        
        Computes:
        - Expected point spread (from Elo or team stats)
        - Home/away indicators
        - Team opponent defensive ratings
        
        Args:
            df_games: DataFrame with games (from get_season_games)
            
        Returns:
            DataFrame with additional context columns
        """
        logger.info(f"Adding context features to {len(df_games)} games...")
        
        df_games = df_games.copy()
        
        # Compute point margin (blowout indicator)
        df_games["point_margin"] = df_games["home_score"] - df_games["away_score"]
        df_games["is_blowout"] = df_games["point_margin"].abs() >= 15
        
        # Expected points (simple heuristic: stronger team in Vegas line)
        # TODO: In production, fetch actual Vegas spreads from ODDS_API
        df_games["expected_total_points"] = df_games["home_score"] + df_games["away_score"]
        df_games["pace_factor"] = df_games["expected_total_points"] / 96  # NBA avg game length
        
        logger.info("Added context features")
        return df_games
    
    def build_player_game_features(
        self,
        player_id: int,
        player_name: str,
        game_date: str,
        season: int,
        opponent_team_id: int,
    ) -> Dict[str, float]:
        """Build features for a specific player in a specific game.
        
        This is used for making predictions before a game starts.
        
        Args:
            player_id: NBA player ID
            player_name: Player name
            game_date: Date of game (YYYY-MM-DD)
            season: Season year
            opponent_team_id: Opponent team ID
            
        Returns:
            Dictionary with game-specific features
        """
        # Player season stats
        player_features = self.client.build_player_props_features(
            player_id=player_id,
            player_name=player_name,
            season=season,
            last_n_games=10
        )
        
        # Opponent defensive stats
        opponent_stats = self.client.get_team_opponent_stats(
            team_id=opponent_team_id,
            season=season
        )
        
        # Combine
        game_features = {
            "player_id": player_id,
            "player_name": player_name,
            "game_date": game_date,
            "season": season,
            "opponent_team_id": opponent_team_id,
        }
        game_features.update(player_features)
        game_features.update(opponent_stats)
        
        return game_features


def main():
    """Main entry point for feature extraction."""
    import sys
    
    season = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
    
    extractor = PlayerPropsExtractor()
    
    # Extract features for season
    df_features = extractor.extract_season_features(season=season, min_games_played=5)
    
    if not df_features.empty:
        logger.info(f"\n✅ Extracted {len(df_features)} players' features")
        logger.info(f"Features saved to: {extractor.output_dir / f'player_props_{season}.parquet'}")
        logger.info(f"\nSample output:")
        print(df_features.head(3))
    else:
        logger.error("Failed to extract features")
        sys.exit(1)


if __name__ == "__main__":
    main()
