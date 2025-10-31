"""
Consolidate All Real NBA Data from Archive Files

Combines multiple Basketball-Reference data files into a unified training dataset.
Processes: Player Per Game, Player Totals, Advanced, Shooting, and Team data.

Output: consolidated_player_stats.csv ready for feature engineering
"""

import pandas as pd
import numpy as np
import os
import glob
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_csv_files(pattern: str = "data/archive*/Player Per Game.csv") -> list:
    """Find all CSV files matching pattern across archive folders."""
    files = glob.glob(pattern)
    logger.info(f"Found {len(files)} files matching pattern: {pattern}")
    return files


def consolidate_player_per_game() -> pd.DataFrame:
    """Consolidate Player Per Game data from all archives."""
    logger.info("\n" + "=" * 80)
    logger.info("CONSOLIDATING REAL NBA DATA")
    logger.info("=" * 80)
    
    logger.info("\n📊 Step 1: Loading Player Per Game stats...")
    
    files = find_csv_files("data/archive*/Player Per Game.csv")
    
    all_data = []
    for file in files:
        logger.info(f"  Loading: {file}")
        try:
            df = pd.read_csv(file)
            all_data.append(df)
        except Exception as e:
            logger.warning(f"  ⚠️ Error loading {file}: {e}")
            continue
    
    if not all_data:
        logger.error("No Player Per Game data found!")
        return None
    
    # Combine all data
    df_combined = pd.concat(all_data, ignore_index=True)
    logger.info(f"  ✓ Loaded {len(df_combined)} total records from {len(files)} files")
    
    # Drop duplicates (same season/player might be in multiple archives)
    # Use lowercase column names from Basketball-Reference
    player_col = 'player' if 'player' in df_combined.columns else 'Player'
    season_col = 'season' if 'season' in df_combined.columns else 'Season'
    
    df_combined = df_combined.drop_duplicates(subset=[player_col, season_col], keep='first')
    logger.info(f"  ✓ Removed duplicates: {len(df_combined)} unique records")
    
    return df_combined


def consolidate_advanced_stats() -> pd.DataFrame:
    """Consolidate Advanced stats."""
    logger.info("\n📊 Step 2: Loading Advanced stats...")
    
    files = find_csv_files("data/archive*/Advanced.csv")
    
    all_data = []
    for file in files:
        logger.info(f"  Loading: {file}")
        try:
            df = pd.read_csv(file)
            all_data.append(df)
        except Exception as e:
            logger.warning(f"  ⚠️ Error loading {file}: {e}")
            continue
    
    if not all_data:
        logger.warning("No Advanced data found")
        return None
    
    df_combined = pd.concat(all_data, ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=['Player', 'Season'], keep='first')
    logger.info(f"  ✓ Loaded {len(df_combined)} unique records")
    
    return df_combined


def consolidate_shooting_stats() -> pd.DataFrame:
    """Consolidate Shooting stats."""
    logger.info("\n📊 Step 3: Loading Shooting stats...")
    
    files = find_csv_files("data/archive*/Player Shooting.csv")
    
    all_data = []
    for file in files:
        logger.info(f"  Loading: {file}")
        try:
            df = pd.read_csv(file)
            all_data.append(df)
        except Exception as e:
            logger.warning(f"  ⚠️ Error loading {file}: {e}")
            continue
    
    if not all_data:
        logger.warning("No Shooting data found")
        return None
    
    df_combined = pd.concat(all_data, ignore_index=True)
    df_combined = df_combined.drop_duplicates(subset=['Player', 'Season'], keep='first')
    logger.info(f"  ✓ Loaded {len(df_combined)} unique records")
    
    return df_combined


def merge_all_data(df_per_game, df_advanced, df_shooting) -> pd.DataFrame:
    """Merge all datasets on Player and Season."""
    logger.info("\n📊 Step 4: Merging all data sources...")
    
    # Start with per-game data
    df = df_per_game.copy()
    
    # Merge advanced stats
    if df_advanced is not None:
        logger.info("  Merging Advanced stats...")
        merge_on = ['Player', 'Season'] if 'Season' in df_advanced.columns else ['Player']
        df = df.merge(df_advanced, on=merge_on, how='left', suffixes=('', '_adv'))
        logger.info(f"  ✓ Merged: {len(df)} records")
    
    # Merge shooting stats
    if df_shooting is not None:
        logger.info("  Merging Shooting stats...")
        merge_on = ['Player', 'Season'] if 'Season' in df_shooting.columns else ['Player']
        df = df.merge(df_shooting, on=merge_on, how='left', suffixes=('', '_shoot'))
        logger.info(f"  ✓ Merged: {len(df)} records")
    
    return df


def extract_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Extract target variables (PTS, AST, REB, STL, BLK) from real data."""
    logger.info("\n📊 Step 5: Extracting target variables...")
    
    # Map column names (Basketball-Reference column names vary)
    column_mapping = {
        'PTS': ['PTS', 'Pts'],  # Points
        'AST': ['AST', 'Ast'],  # Assists
        'REB': ['TRB', 'Reb', 'Rebounds'],  # Rebounds (TRB = Total Rebounds)
        'STL': ['STL', 'Stl'],  # Steals
        'BLK': ['BLK', 'Blk'],  # Blocks
    }
    
    # Find actual columns in data
    df_out = df[['Player', 'Season']].copy()
    
    for target, possible_names in column_mapping.items():
        found = False
        for col_name in possible_names:
            if col_name in df.columns:
                df_out[f'{target}_actual'] = pd.to_numeric(df[col_name], errors='coerce')
                logger.info(f"  ✓ Found {target} in column: {col_name}")
                found = True
                break
        
        if not found:
            logger.warning(f"  ⚠️ {target} not found, using 0")
            df_out[f'{target}_actual'] = 0
    
    return df_out


def clean_and_prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Clean data and prepare for training."""
    logger.info("\n📊 Step 6: Cleaning and preparing data...")
    
    # Convert Season to year (e.g., "2021-22" → 2021)
    if 'Season' in df.columns:
        df['year'] = df['Season'].str.split('-').str[0].astype(int, errors='ignore')
    
    # Create date column (simplified: use season midpoint)
    df['date'] = pd.to_datetime(df['year'].astype(str) + '-11-15', errors='coerce')
    
    # Create team and opponent (placeholder, would need game-by-game data)
    df['team'] = 'TEAM'
    df['opponent'] = 'OPP'
    
    # Fill NaN values with 0
    for col in ['PTS_actual', 'AST_actual', 'REB_actual', 'STL_actual', 'BLK_actual']:
        df[col] = df[col].fillna(0)
    
    # Filter valid records (must have targets > 0 for at least one stat)
    df_valid = df[(df['PTS_actual'] > 0) | (df['AST_actual'] > 0) | (df['REB_actual'] > 0)].copy()
    
    logger.info(f"  ✓ Kept {len(df_valid)} records with valid target data")
    logger.info(f"  ✓ Removed {len(df) - len(df_valid)} records with missing targets")
    
    return df_valid


def consolidate_real_data():
    """Main consolidation pipeline."""
    logger.info("Starting real data consolidation from Basketball-Reference archives...")
    
    # Load all data sources
    df_per_game = consolidate_player_per_game()
    df_advanced = consolidate_advanced_stats()
    df_shooting = consolidate_shooting_stats()
    
    if df_per_game is None:
        logger.error("Failed to load Player Per Game data!")
        return None
    
    # Merge all data
    df_merged = merge_all_data(df_per_game, df_advanced, df_shooting)
    
    # Extract targets
    df_targets = extract_targets(df_merged)
    
    # Clean and prepare
    df_final = clean_and_prepare(df_targets)
    
    # Save consolidated data
    output_path = "data/raw/consolidated_player_stats.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_final.to_csv(output_path, index=False)
    
    logger.info(f"\n{'='*80}")
    logger.info("CONSOLIDATION COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"✅ Saved {len(df_final)} records to {output_path}")
    logger.info(f"\nData Summary:")
    logger.info(f"  Date Range: {df_final['date'].min()} to {df_final['date'].max()}")
    logger.info(f"  Years: {sorted(df_final['year'].unique())}")
    logger.info(f"  Players: {df_final['Player'].nunique()}")
    logger.info(f"\nTarget Statistics:")
    logger.info(f"  PTS: mean={df_final['PTS_actual'].mean():.1f}, std={df_final['PTS_actual'].std():.1f}")
    logger.info(f"  AST: mean={df_final['AST_actual'].mean():.1f}, std={df_final['AST_actual'].std():.1f}")
    logger.info(f"  REB: mean={df_final['REB_actual'].mean():.1f}, std={df_final['REB_actual'].std():.1f}")
    logger.info(f"  STL: mean={df_final['STL_actual'].mean():.1f}, std={df_final['STL_actual'].std():.1f}")
    logger.info(f"  BLK: mean={df_final['BLK_actual'].mean():.1f}, std={df_final['BLK_actual'].std():.1f}")
    logger.info(f"{'='*80}\n")
    
    return df_final


if __name__ == "__main__":
    df = consolidate_real_data()
    
    if df is not None:
        print(f"✅ Consolidation successful!")
        print(f"\nFirst few rows:")
        print(df.head(10))
        print(f"\nShape: {df.shape}")
