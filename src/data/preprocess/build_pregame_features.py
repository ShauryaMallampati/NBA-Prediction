"""
Comprehensive Pregame Feature Engineering Pipeline

Integrates:
- Elo ratings (basic)
- Advanced features (15+ features)
- Temporal features (19 features)
- Injury/availability features
- Lineup features

Total: 50+ features for game predictions
"""

from __future__ import annotations
import pathlib
import pandas as pd
import numpy as np
import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional

from src.common.validators import guard_mock_allowed
from src.common.logger import setup_logger

# Import advanced feature modules
from .build_advanced_features import add_advanced_features
from .build_temporal_features import add_temporal_features

logger = setup_logger(__name__)

OUT = pathlib.Path("artifacts/features").resolve()
OUT.mkdir(parents=True, exist_ok=True)


def compute_elo(df_games: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Elo ratings with decaying K factor.
    
    Args:
        df_games: DataFrame with games (home, away, date, home_pts, away_pts)
    
    Returns:
        DataFrame with Elo ratings
    """
    logger.info("📊 Computing Elo ratings...")
    
    K0, decay, home_adv, margin_mult = 24.0, 0.98, 60.0, 0.75
    ratings = {}
    rows = []
    
    df_sorted = df_games.sort_values("date").copy()
    
    # Add day_index if not present
    if 'day_index' not in df_sorted.columns:
        df_sorted['day_index'] = range(len(df_sorted))
    
    for _, row in df_sorted.iterrows():
        h, a = row['home'], row['away']
        Rh = ratings.get(h, 1500.0)
        Ra = ratings.get(a, 1500.0)
        
        # Expected win probability
        exp_h = 1.0 / (1.0 + 10 ** (-(Rh + home_adv - Ra) / 400))
        
        # Result
        margin = row['home_pts'] - row['away_pts']
        res_h = 1.0 if margin > 0 else 0.0
        
        # K factor with decay
        k = K0 * (decay ** row['day_index'])
        k *= 1 + margin_mult * np.tanh(abs(margin) / 10.0)
        
        # Update ratings
        Rh_new = Rh + k * (res_h - exp_h)
        Ra_new = Ra + k * ((1 - res_h) - (1 - exp_h))
        
        ratings[h], ratings[a] = Rh_new, Ra_new
        
        rows.append({
            "game_id": row.get('game_id', f"{h}_{a}_{row['date']}"),
            "elo_home": Rh,
            "elo_away": Ra,
            "elo_diff": Rh - Ra,
            "elo_win_prob": exp_h,
        })
    
    logger.info(f"✅ Computed Elo ratings for {len(ratings)} teams")
    return pd.DataFrame(rows)


def load_historical_games() -> pd.DataFrame:
    """
    Load historical games from multiple sources.
    
    Returns:
        DataFrame with games
    """
    logger.info("📂 Loading historical games...")
    
    # Try to load from processed data
    processed_dir = pathlib.Path("data/processed")
    if (processed_dir / "games.csv").exists():
        df = pd.read_csv(processed_dir / "games.csv")
        df['date'] = pd.to_datetime(df['date'])
        logger.info(f"✅ Loaded {len(df)} games from processed data")
        return df
    
    # Try to load from raw data
    raw_dir = pathlib.Path("data/raw/nba_stats")
    if raw_dir.exists():
        # Look for scoreboard files
        scoreboard_files = list(raw_dir.glob("scoreboard_*.json"))
        if scoreboard_files:
            games = []
            for file in scoreboard_files:
                try:
                    data = json.loads(file.read_text())
                    for g in data.get("scoreboard", {}).get("games", []):
                        games.append({
                            "game_id": g.get("gameId", f"game_{len(games)}"),
                            "date": file.stem.split("_")[-1],  # Extract date from filename
                            "home": g.get("homeTeam", {}).get("teamTricode", "HOM"),
                            "away": g.get("awayTeam", {}).get("teamTricode", "AWY"),
                            "home_pts": g.get("homeTeam", {}).get("score", 0),
                            "away_pts": g.get("awayTeam", {}).get("score", 0),
                        })
                except Exception as e:
                    logger.warning(f"Error loading {file}: {e}")
            
            if games:
                df = pd.DataFrame(games)
                df['date'] = pd.to_datetime(df['date'])
                logger.info(f"✅ Loaded {len(df)} games from raw data")
                return df
    
    # Fallback to seed data
    logger.warning("No historical data found, using seed data")
    guard_mock_allowed()
    return pd.DataFrame([
        {"game_id": "g1", "date": "2024-10-25", "home": "LAL", "away": "GSW", "home_pts": 110, "away_pts": 105},
        {"game_id": "g2", "date": "2024-10-26", "home": "BOS", "away": "NYK", "home_pts": 100, "away_pts": 108},
    ])


def build_comprehensive_features(df_games: pd.DataFrame) -> pd.DataFrame:
    """
    Build comprehensive feature set for game predictions.
    
    Args:
        df_games: DataFrame with games
    
    Returns:
        DataFrame with all features
    """
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE FEATURE ENGINEERING")
    logger.info("=" * 80)
    
    df = df_games.copy()
    
    # Ensure date is datetime
    if 'date' not in df.columns:
        raise ValueError("Dataframe must have 'date' column")
    df['date'] = pd.to_datetime(df['date'])
    
    # Ensure required columns exist
    if 'home' not in df.columns or 'away' not in df.columns:
        raise ValueError("Dataframe must have 'home' and 'away' columns")
    
    if 'home_pts' not in df.columns or 'away_pts' not in df.columns:
        logger.warning("Missing points data, adding placeholder")
        df['home_pts'] = 100
        df['away_pts'] = 100
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    # Add day_index for Elo calculation
    df['day_index'] = range(len(df))
    
    # 1. Compute Elo ratings
    logger.info("\n📊 Step 1: Computing Elo ratings...")
    elo_df = compute_elo(df)
    df = df.merge(elo_df, on='game_id', how='left')
    
    # Fill NaN Elo with 1500 (league average)
    for col in ['elo_home', 'elo_away', 'elo_diff', 'elo_win_prob']:
        if col not in df.columns:
            df[col] = 1500.0 if 'elo' in col and 'prob' not in col else 0.5
        df[col] = df[col].fillna(1500.0 if 'elo' in col and 'prob' not in col else 0.5)
    
    # 2. Add home court advantage flag
    df['home_adv_flag'] = 1
    df['home_court_adv'] = 0.03  # 3% home court advantage
    
    # 3. Add advanced features
    logger.info("\n📊 Step 2: Adding advanced features...")
    try:
        df = add_advanced_features(df)
    except Exception as e:
        logger.error(f"Error adding advanced features: {e}")
        logger.warning("Continuing without advanced features...")
    
    # 4. Add temporal features
    logger.info("\n📊 Step 3: Adding temporal features...")
    try:
        df = add_temporal_features(df)
    except Exception as e:
        logger.error(f"Error adding temporal features: {e}")
        logger.warning("Continuing without temporal features...")
    
    # 5. Add injury/availability features (if available)
    logger.info("\n📊 Step 4: Adding injury/availability features...")
    try:
        from src.data.ingest.injury_fetcher import get_injury_fetcher
        injury_fetcher = get_injury_fetcher()
        
        # Add placeholder injury features (will be populated when injury data is available)
        df['home_injury_count'] = 0
        df['away_injury_count'] = 0
        df['home_key_player_injured'] = 0
        df['away_key_player_injured'] = 0
        
    except Exception as e:
        logger.warning(f"Injury features not available: {e}")
        df['home_injury_count'] = 0
        df['away_injury_count'] = 0
        df['home_key_player_injured'] = 0
        df['away_key_player_injured'] = 0
    
    # 6. Fill NaN values
    logger.info("\n📊 Step 5: Filling NaN values...")
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col not in ['home_pts', 'away_pts', 'home_win', 'away_win']:
            df[col] = df[col].fillna(df[col].median() if df[col].notna().sum() > 0 else 0)
    
    # 7. Add target variable
    if 'home_win' not in df.columns:
        df['home_win'] = (df['home_pts'] > df['away_pts']).astype(int)
    if 'away_win' not in df.columns:
        df['away_win'] = (df['away_pts'] > df['home_pts']).astype(int)
    
    # 8. Add season column
    if 'season' not in df.columns:
        df['season'] = df['date'].dt.year
    
    logger.info("=" * 80)
    logger.info("FEATURE ENGINEERING COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total games: {len(df)}")
    logger.info(f"Total features: {len(df.columns)}")
    logger.info(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    logger.info("=" * 80)
    
    return df


def main() -> None:
    """Main function to build pregame features."""
    logger.info("=" * 80)
    logger.info("PREGAME FEATURE ENGINEERING PIPELINE")
    logger.info("=" * 80)
    
    # Load historical games
    df_games = load_historical_games()
    
    if len(df_games) == 0:
        logger.error("No games found. Please run data collection first.")
        return
    
    # Build comprehensive features
    df_features = build_comprehensive_features(df_games)
    
    # Save features
    output_path = OUT / "pregame.parquet"
    df_features.to_parquet(output_path, index=False)
    logger.info(f"✅ Saved features to {output_path}")
    
    # Also save as CSV for easy inspection
    csv_path = OUT / "pregame.csv"
    df_features.to_csv(csv_path, index=False)
    logger.info(f"✅ Saved features to {csv_path}")
    
    # Print feature summary
    logger.info("\n📋 Feature Summary:")
    feature_cols = [col for col in df_features.columns 
                   if col not in ['game_id', 'date', 'home', 'away', 'home_pts', 'away_pts',
                                 'home_win', 'away_win', 'season', 'year', 'month', 'day_of_week']]
    
    logger.info(f"  Total features: {len(feature_cols)}")
    logger.info(f"  Feature categories:")
    logger.info(f"    - Elo features: {len([c for c in feature_cols if 'elo' in c.lower()])}")
    logger.info(f"    - Advanced features: {len([c for c in feature_cols if any(x in c for x in ['h2h', 'form', 'streak', 'fatigue', 'rest', 'b2b'])])}")
    logger.info(f"    - Temporal features: {len([c for c in feature_cols if any(x in c for x in ['momentum', 'season', 'month', 'day', 'weighted'])])}")
    logger.info(f"    - Other features: {len([c for c in feature_cols if c not in [f for cat in [['elo'], ['h2h', 'form', 'streak', 'fatigue', 'rest', 'b2b'], ['momentum', 'season', 'month', 'day', 'weighted']] for f in cat]])}")
    
    logger.info("\n✅ Feature engineering complete!")
    logger.info(f"   Output: {output_path}")
    logger.info(f"   Features: {len(feature_cols)}")
    logger.info(f"   Games: {len(df_features)}")


if __name__ == "__main__":
    main()
