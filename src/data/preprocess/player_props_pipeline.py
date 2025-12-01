"""
Player Props Features Pipeline

Combines all three data sources into a unified training dataset:
  • Task #10: NBA Stats Client (player stats, minutes, trends)
  • Task #11: BR Scraper (load management, recent form)
  • Task #12: Travel Calculator (fatigue scores, timezone impact)

Output: Parquet file with 40+ features per player-game for LightGBM training

Feature Categories:
  1. Player Performance (20 features)
     - PTS, AST, REB, STEALS, BLOCKS (4 features each)
     - season_avg, recent_avg, recent_trend, consistency

  2. Load Management (8 features)
     - on_games, off_games, consistency, rest_risk
     - recent_ppg, recent_trend, recent_consistency, rest_pattern

  3. Travel & Fatigue (8 features)
     - distance_miles, timezone_diff, fatigue_score
     - back_to_back, minutes_yesterday, arena_change, travel_risk

  4. Context Features (4 features)
     - game_date, player_name, team, opponent
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import pathlib
import json


class PlayerPropsFeaturesPipeline:
    """
    Orchestrates feature extraction from all three data sources.
    Combines into unified training dataset.
    """
    
    def __init__(self):
        """Initialize the pipeline."""
        self.output_dir = pathlib.Path("data/processed/player_props")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def build_feature_matrix(
        self,
        stats_data: List[Dict],
        br_data: List[Dict],
        travel_data: List[Dict],
    ) -> pd.DataFrame:
        """
        Build complete feature matrix from all three sources.
        
        Args:
            stats_data: From NBAStatsClient (player stats, minutes)
            br_data: From BRLoader (load management, form)
            travel_data: From TravelFatigueCalculator (fatigue, timezone)
        
        Returns:
            DataFrame with ~40 features per row (player-game)
        """
        
        # Start with base player-game records
        features = []
        
        for game_record in stats_data:
            player = game_record.get("player_name", "")
            date = game_record.get("date", "")
            
            # Find matching BR data
            br_match = self._find_matching_record(
                br_data, player, date, tolerance_days=0
            )
            
            # Find matching travel data
            travel_match = self._find_matching_record(
                travel_data, game_record.get("team", ""), date, tolerance_days=0
            )
            
            # Build feature row
            row = self._build_feature_row(
                game_record, br_match, travel_match
            )
            
            if row is not None:
                features.append(row)
        
        return pd.DataFrame(features)
    
    def _find_matching_record(
        self,
        records: List[Dict],
        key1: str,
        key2: str,
        tolerance_days: int = 0,
    ) -> Optional[Dict]:
        """
        Find matching record by two keys (player/team name and date).
        
        Args:
            records: List of records to search
            key1: Player name or team name
            key2: Date (YYYY-MM-DD)
            tolerance_days: How many days to search around the date
        
        Returns:
            Matching record or None
        """
        for record in records:
            # Check key1 (player or team name)
            record_key1 = record.get("player_name") or record.get("team", "")
            if record_key1.lower() != key1.lower():
                continue
            
            # Check key2 (date)
            record_date = record.get("date", "")
            try:
                target = datetime.strptime(key2, "%Y-%m-%d")
                candidate = datetime.strptime(record_date, "%Y-%m-%d")
                
                days_diff = abs((target - candidate).days)
                if days_diff <= tolerance_days:
                    return record
            except (ValueError, KeyError):
                continue
        
        return None
    
    def _normalize_consistency(self, value: float) -> float:
        """Normalize consistency score (std dev) to 0-1 range."""
        # Typical consistency (std dev) ranges from 0-8 for NBA stats
        # Normalize to 0-1 where 0 = very consistent, 1 = inconsistent
        return min(value / 8.0, 1.0)
    
    def _build_feature_row(
        self,
        stats: Dict,
        br: Optional[Dict],
        travel: Optional[Dict],
    ) -> Optional[Dict]:
        """
        Build single feature row combining all three sources.
        
        Args:
            stats: Stats record from Task #10
            br: BR record from Task #11 (optional)
            travel: Travel record from Task #12 (optional)
        
        Returns:
            Dict with ~40 features or None if incomplete
        """
        
        if not stats:
            return None
        
        row = {}
        
        # ═══════════════════════════════════════════════════════════════
        # PLAYER PERFORMANCE FEATURES (20 features from Task #10)
        # ═══════════════════════════════════════════════════════════════
        
        # PTS features
        row["pts_season_avg"] = stats.get("pts_season_avg", 0.0)
        row["pts_recent_avg"] = stats.get("pts_recent_avg", 0.0)
        row["pts_recent_trend"] = stats.get("pts_recent_trend", 0.0)
        row["pts_consistency"] = self._normalize_consistency(stats.get("pts_consistency", 0.0))
        
        # AST features
        row["ast_season_avg"] = stats.get("ast_season_avg", 0.0)
        row["ast_recent_avg"] = stats.get("ast_recent_avg", 0.0)
        row["ast_recent_trend"] = stats.get("ast_recent_trend", 0.0)
        row["ast_consistency"] = self._normalize_consistency(stats.get("ast_consistency", 0.0))
        
        # REB features
        row["reb_season_avg"] = stats.get("reb_season_avg", 0.0)
        row["reb_recent_avg"] = stats.get("reb_recent_avg", 0.0)
        row["reb_recent_trend"] = stats.get("reb_recent_trend", 0.0)
        row["reb_consistency"] = self._normalize_consistency(stats.get("reb_consistency", 0.0))
        
        # STEALS features
        row["stl_season_avg"] = stats.get("stl_season_avg", 0.0)
        row["stl_recent_avg"] = stats.get("stl_recent_avg", 0.0)
        row["stl_recent_trend"] = stats.get("stl_recent_trend", 0.0)
        row["stl_consistency"] = self._normalize_consistency(stats.get("stl_consistency", 0.0))
        
        # BLOCKS features
        row["blk_season_avg"] = stats.get("blk_season_avg", 0.0)
        row["blk_recent_avg"] = stats.get("blk_recent_avg", 0.0)
        row["blk_recent_trend"] = stats.get("blk_recent_trend", 0.0)
        row["blk_consistency"] = self._normalize_consistency(stats.get("blk_consistency", 0.0))
        
        # ═══════════════════════════════════════════════════════════════
        # LOAD MANAGEMENT FEATURES (8 features from Task #11)
        # ═══════════════════════════════════════════════════════════════
        
        if br:
            # Load management: keep raw values (on_games, off_games are already 0-15 range)
            row["load_on_games"] = br.get("on_games", 0.0)
            row["load_off_games"] = br.get("off_games", 0.0)
            row["load_consistency"] = min(br.get("consistency", 0.0), 1.0)
            row["load_rest_risk"] = min(br.get("rest_risk", 0.0), 1.0)
            
            # Recent form
            row["form_recent_ppg"] = br.get("recent_ppg", 0.0)
            row["form_recent_trend"] = br.get("recent_trend", 0.0)
            row["form_recent_consistency"] = self._normalize_consistency(br.get("recent_consistency", 0.0))
            row["form_rest_pattern"] = 1.0 if br.get("is_resting") else 0.0
        else:
            row["load_on_games"] = 0.0
            row["load_off_games"] = 0.0
            row["load_consistency"] = 0.0
            row["load_rest_risk"] = 0.0
            row["form_recent_ppg"] = 0.0
            row["form_recent_trend"] = 0.0
            row["form_recent_consistency"] = 0.0
            row["form_rest_pattern"] = 0.0
        
        # ═══════════════════════════════════════════════════════════════
        # TRAVEL & FATIGUE FEATURES (8 features from Task #12)
        # ═══════════════════════════════════════════════════════════════
        
        if travel:
            row["travel_distance_miles"] = travel.get("distance_miles", 0.0)
            row["travel_timezone_diff"] = travel.get("timezone_diff", 0)
            row["travel_fatigue_score"] = travel.get("fatigue_score", 0)
            row["travel_back_to_back"] = 1.0 if travel.get("back_to_back") else 0.0
            row["travel_minutes_yesterday"] = travel.get("minutes_yesterday", 0.0)
            
            # Derived travel features
            row["travel_arena_change"] = 1.0 if travel.get("distance_miles", 0) > 0 else 0.0
            
            # travel_risk: normalize fatigue score to 0-1, average with rest_risk
            fatigue_normalized = min(travel.get("fatigue_score", 0) / 100.0, 1.0)
            rest_risk = min(travel.get("rest_risk", 0), 1.0)
            row["travel_risk"] = (fatigue_normalized + rest_risk) / 2.0
        else:
            row["travel_distance_miles"] = 0.0
            row["travel_timezone_diff"] = 0
            row["travel_fatigue_score"] = 0
            row["travel_back_to_back"] = 0.0
            row["travel_minutes_yesterday"] = 0.0
            row["travel_arena_change"] = 0.0
            row["travel_risk"] = 0.0
        
        # ═══════════════════════════════════════════════════════════════
        # CONTEXT FEATURES (4 features)
        # ═══════════════════════════════════════════════════════════════
        
        row["game_date"] = stats.get("date", "")
        row["player_name"] = stats.get("player_name", "")
        row["team"] = stats.get("team", "")
        row["opponent"] = stats.get("opponent", "")
        
        # ═══════════════════════════════════════════════════════════════
        # TARGET VARIABLES (for training, if available)
        # ═══════════════════════════════════════════════════════════════
        
        row["actual_pts"] = stats.get("actual_pts")
        row["actual_ast"] = stats.get("actual_ast")
        row["actual_reb"] = stats.get("actual_reb")
        row["actual_stl"] = stats.get("actual_stl")
        row["actual_blk"] = stats.get("actual_blk")
        
        return row
    
    def export_to_parquet(self, df: pd.DataFrame, filename: str = "player_props_features.parquet"):
        """
        Export feature matrix to Parquet format for LightGBM training.
        
        Args:
            df: Feature DataFrame
            filename: Output filename
        """
        output_path = self.output_dir / filename
        
        # Convert dtypes for efficiency
        for col in df.columns:
            if col.startswith("actual_"):
                df[col] = df[col].astype("float32")
            elif df[col].dtype == "float64":
                df[col] = df[col].astype("float32")
            elif df[col].dtype == "int64":
                df[col] = df[col].astype("int8")
        
        df.to_parquet(output_path, index=False)
        print(f"✅ Exported {len(df)} records to {output_path}")
        print(f"   Shape: {df.shape}")
        print(f"   Features: {list(df.columns)}")
        
        return output_path
    
    def get_feature_stats(self, df: pd.DataFrame) -> Dict:
        """
        Generate statistics about the feature matrix.
        
        Args:
            df: Feature DataFrame
        
        Returns:
            Dict with statistics
        """
        stats = {
            "total_records": len(df),
            "total_features": len(df.columns),
            "date_range": f"{df['game_date'].min()} to {df['game_date'].max()}",
            "unique_players": df["player_name"].nunique(),
            "unique_teams": df["team"].nunique(),
            "columns": list(df.columns),
            "missing_values": df.isnull().sum().to_dict(),
        }
        return stats


def create_sample_feature_matrix() -> pd.DataFrame:
    """
    Create a sample feature matrix for testing and demonstration.
    
    Returns:
        DataFrame with sample data
    """
    pipeline = PlayerPropsFeaturesPipeline()
    
    # Sample stats data (Task #10)
    stats_data = [
        {
            "date": "2023-11-15",
            "player_name": "LeBron James",
            "team": "Los Angeles Lakers",
            "opponent": "Boston Celtics",
            "pts_season_avg": 25.5,
            "pts_recent_avg": 26.2,
            "pts_recent_trend": 0.3,
            "pts_consistency": 2.1,
            "ast_season_avg": 9.2,
            "ast_recent_avg": 9.5,
            "ast_recent_trend": 0.1,
            "ast_consistency": 1.8,
            "reb_season_avg": 7.3,
            "reb_recent_avg": 7.5,
            "reb_recent_trend": 0.0,
            "reb_consistency": 1.5,
            "stl_season_avg": 1.2,
            "stl_recent_avg": 1.3,
            "stl_recent_trend": 0.05,
            "stl_consistency": 0.4,
            "blk_season_avg": 0.8,
            "blk_recent_avg": 0.9,
            "blk_recent_trend": 0.02,
            "blk_consistency": 0.3,
            "actual_pts": 24,
            "actual_ast": 9,
            "actual_reb": 8,
            "actual_stl": 1,
            "actual_blk": 1,
        }
    ]
    
    # Sample BR data (Task #11)
    br_data = [
        {
            "player_name": "LeBron James",
            "date": "2023-11-15",
            "on_games": 8.0,
            "off_games": 1.0,
            "consistency": 1.0,
            "rest_risk": 0.11,
            "recent_ppg": 23.3,
            "recent_trend": 3.0,
            "recent_consistency": 2.95,
            "is_resting": False,
        }
    ]
    
    # Sample travel data (Task #12)
    travel_data = [
        {
            "team": "Los Angeles Lakers",
            "date": "2023-11-15",
            "distance_miles": 0.0,  # Home game
            "timezone_diff": 0,
            "fatigue_score": 5,
            "back_to_back": False,
            "minutes_yesterday": 38.0,
            "rest_risk": 0.05,
        }
    ]
    
    # Build feature matrix
    df = pipeline.build_feature_matrix(stats_data, br_data, travel_data)
    
    return df


if __name__ == "__main__":
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "PLAYER PROPS FEATURES PIPELINE - TEST" + " "*17 + "║")
    print("╚" + "="*68 + "╝\n")
    
    # Create sample dataset
    df = create_sample_feature_matrix()
    
    print("Sample Feature Matrix:")
    print(f"Shape: {df.shape}")
    print(f"\nColumns ({len(df.columns)} total):")
    for i, col in enumerate(df.columns, 1):
        value = df[col].iloc[0] if len(df) > 0 else "N/A"
        print(f"  {i:2d}. {col:30s} = {value}")
    
    print(f"\n{'='*70}")
    print("Feature Categories:")
    print(f"  • Player Performance: 20 features (PTS, AST, REB, STL, BLK × 4 each)")
    print(f"  • Load Management: 8 features (rest patterns, form)")
    print(f"  • Travel & Fatigue: 8 features (distance, timezone, fatigue)")
    print(f"  • Context: 4 features (date, player, team, opponent)")
    print(f"  • Targets: 5 variables (actual stats)")
    print(f"  • TOTAL: 45 columns")
    print(f"{'='*70}\n")
    
    # Export to parquet
    pipeline = PlayerPropsFeaturesPipeline()
    pipeline.export_to_parquet(df, "player_props_features_sample.parquet")
    
    # Get statistics
    stats = pipeline.get_feature_stats(df)
    print(f"\nFeature Matrix Statistics:")
    print(f"  Total Records: {stats['total_records']}")
    print(f"  Total Features: {stats['total_features']}")
    print(f"  Unique Players: {stats['unique_players']}")
    print(f"  Unique Teams: {stats['unique_teams']}")
