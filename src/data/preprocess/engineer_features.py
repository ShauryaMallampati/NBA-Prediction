"""Build features for training player prop models.

We take raw game logs and transform them into ML-ready features:
  - Recent rolling averages (last 3, 7 games)
  - How they perform against specific opponents  
  - Rest and travel factors
  - Shooting percentages and usage

Output: A clean CSV ready to train LightGBM models on
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Turn raw stats into useful features that help predict player performance.
    
    Args:
        df: The player game logs from our data collection
    
    Returns:
        Enhanced dataframe with 40+ features ready for training
    """
    logger.info("=" * 80)
    logger.info("FEATURE ENGINEERING PIPELINE")
    logger.info("=" * 80)
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # =====================================================================
    # Rolling averages are the bread and butter of sports prediction
    # =====================================================================
    logger.info("\n📊 1. Building rolling averages...")
    
    # Group by player for rolling calculations
    for col in ['PTS_actual', 'AST_actual', 'REB_actual', 'STL_actual', 'BLK_actual']:
        # Last 3 games average - shows current hot/cold streak
        df[f'{col}_rolling_3'] = df.groupby('player_name')[col].rolling(3, min_periods=1).mean().reset_index(drop=True)
        
        # Last 7 games - more stable baseline
        df[f'{col}_rolling_7'] = df.groupby('player_name')[col].rolling(7, min_periods=1).mean().reset_index(drop=True)
        
        # Season average for context
        df[f'{col}_season_avg'] = df.groupby(['season', 'player_name'])[col].transform('mean')
        
        # Consistency score (low std = reliable)
        df[f'{col}_rolling_std_7'] = df.groupby('player_name')[col].rolling(7, min_periods=1).std().reset_index(drop=True)
    
    logger.info(f"  ✓ Generated {len([c for c in df.columns if 'rolling' in c])} rolling features")
    
    # =====================================================================
    # Some teams just play better/worse defense against certain stats
    # =====================================================================
    logger.info("\n📊 2. Calculating matchup advantages...")
    
    # Opponent defense rating (simple: avg opponent PTS allowed to this player type)
    opponent_avg = df.groupby('opponent')[['PTS_actual', 'AST_actual', 'REB_actual', 'STL_actual', 'BLK_actual']].mean()
    opponent_avg.columns = ['opp_def_PTS', 'opp_def_AST', 'opp_def_REB', 'opp_def_STL', 'opp_def_BLK']
    
    df = df.merge(opponent_avg, left_on='opponent', right_index=True, how='left')
    
    # Advantage vs opponent
    for stat in ['PTS', 'AST', 'REB', 'STL', 'BLK']:
        df[f'{stat}_vs_opp_advantage'] = df[f'{stat}_actual'] - df[f'opp_def_{stat}']
    
    logger.info(f"  ✓ Generated {len([c for c in df.columns if 'opp_def' in c or 'advantage' in c])} opponent features")
    
    # =====================================================================
    # 3. GAME CONTEXT FEATURES
    # =====================================================================
    logger.info("\n📊 3. Computing game context features...")
    
    # Home/Away (random for now - would use actual game schedule)
    df['is_home'] = np.random.choice([0, 1], size=len(df))
    
    # Rest days (days since last game)
    df['rest_days'] = df.groupby('player_name')['date'].diff().dt.days.fillna(1).clip(0, 10)
    
    # Back-to-back flag
    df['is_back_to_back'] = (df['rest_days'] <= 1).astype(int)
    
    # Month of season (early, mid, late)
    df['month'] = df['date'].dt.month
    df['is_playoffs'] = ((df['month'] >= 4) & (df['month'] <= 6)).astype(int)
    
    logger.info(f"  ✓ Generated 5 game context features")
    
    # =====================================================================
    # 4. SHOOTING EFFICIENCY METRICS
    # =====================================================================
    logger.info("\n📊 4. Computing shooting efficiency...")
    
    # FG%, 3P%, FT% (already in data, just rename)
    df['FG_pct'] = df['FG_PCT'].fillna(0.44)  # Fill missing with league avg
    df['FG3_pct'] = df['FG3_PCT'].fillna(0.35)
    df['FT_pct'] = df['FT_PCT'].fillna(0.75)
    
    # Usage rate
    df['usage_pct'] = df['USG_PCT'].fillna(0.24)
    
    # True shooting percentage (advanced metric approximation)
    df['TS_pct'] = (df['PTS_actual'] / (2 * (df['FG_PCT'] * 100 + 0.44 * df['FT_PCT'] * 100))).clip(0, 1)
    
    logger.info(f"  ✓ Generated 5 shooting efficiency features")
    
    # =====================================================================
    # 5. TREND INDICATORS
    # =====================================================================
    logger.info("\n📊 5. Computing trend indicators...")
    
    # Hot/Cold streaks (last 3 games)
    for col in ['PTS_actual', 'AST_actual', 'REB_actual']:
        rolling_3 = df.groupby('player_name')[col].rolling(3, min_periods=1).mean().reset_index(drop=True)
        season_avg = df.groupby('season')[col].transform('mean')
        df[f'{col}_trend'] = rolling_3 - season_avg  # Positive = hot
    
    logger.info(f"  ✓ Generated 3 trend indicator features")
    
    # =====================================================================
    # 6. DURABILITY METRICS
    # =====================================================================
    logger.info("\n📊 6. Computing durability metrics...")
    
    # Games played (count of games)
    df['games_played'] = df.groupby('player_name').cumcount() + 1
    
    # Consistency (low std = reliable)
    df['consistency_score'] = 1 - df.groupby('player_name')['PTS_actual'].rolling(7, min_periods=1).std().reset_index(drop=True).fillna(0) / 10
    
    logger.info(f"  ✓ Generated 2 durability features")
    
    # =====================================================================
    # FINAL PROCESSING
    # =====================================================================
    logger.info("\n📊 7. Final processing...")
    
    # Drop rows with NaN features (first few games per player)
    df_clean = df.dropna(subset=[col for col in df.columns if col not in ['opponent', 'team', 'player_name', 'season', 'date']])
    
    logger.info(f"  ✓ Dropped {len(df) - len(df_clean)} rows with missing values")
    logger.info(f"  ✓ Kept {len(df_clean)} complete records")
    
    # Extract year from date
    df_clean['year'] = df_clean['date'].dt.year
    
    # Select features for model training
    feature_cols = [col for col in df_clean.columns 
                   if col not in ['date', 'season', 'player_name', 'team', 'opponent', 'year', 
                                  'PTS_actual', 'AST_actual', 'REB_actual', 'STL_actual', 'BLK_actual']]
    
    logger.info(f"\n{'='*80}")
    logger.info(f"FEATURE ENGINEERING COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Total Features: {len(feature_cols)}")
    logger.info(f"Total Records: {len(df_clean)}")
    logger.info(f"Date Range: {df_clean['date'].min().date()} to {df_clean['date'].max().date()}")
    logger.info(f"Seasons: {sorted(df_clean['season'].unique())}")
    logger.info(f"\nTrain/Val/Test Split:")
    logger.info(f"  Train (2017-2020): {len(df_clean[df_clean['year'] < 2021])} records")
    logger.info(f"  Val   (2021):      {len(df_clean[df_clean['year'] == 2021])} records")
    logger.info(f"  Test  (2022):      {len(df_clean[df_clean['year'] == 2022])} records")
    logger.info(f"\nFeature Categories:")
    logger.info(f"  Rolling Stats: {len([c for c in feature_cols if 'rolling' in c])} features")
    logger.info(f"  Opponent Adj:  {len([c for c in feature_cols if 'opp' in c or 'advantage' in c])} features")
    logger.info(f"  Context:       {len([c for c in feature_cols if any(x in c for x in ['home', 'rest', 'back', 'month', 'playoff'])])} features")
    logger.info(f"  Shooting:      {len([c for c in feature_cols if any(x in c for x in ['pct', 'usage', 'ts'])])} features")
    logger.info(f"  Trends:        {len([c for c in feature_cols if 'trend' in c])} features")
    logger.info(f"  Durability:    {len([c for c in feature_cols if any(x in c for x in ['games_', 'consistency'])])} features")
    logger.info(f"{'='*80}")
    
    return df_clean


def prepare_training_data(df: pd.DataFrame) -> tuple:
    """
    Prepare data for LightGBM training.
    
    Returns:
        (features_df, train_indices, val_indices, test_indices)
    """
    logger.info("\n📊 Preparing training/validation/test splits...")
    
    # Create year column if not present
    if 'year' not in df.columns:
        df['year'] = df['date'].dt.year
    
    train_idx = df['year'] < 2021
    val_idx = df['year'] == 2021
    test_idx = df['year'] == 2022
    
    logger.info(f"  Train: {train_idx.sum()} records (2017-2020)")
    logger.info(f"  Val:   {val_idx.sum()} records (2021)")
    logger.info(f"  Test:  {test_idx.sum()} records (2022)")
    
    return df, train_idx, val_idx, test_idx


if __name__ == "__main__":
    # Load collected data
    logger.info("Loading collected player stats...")
    df_raw = pd.read_csv('data/raw/player_stats.csv')
    logger.info(f"Loaded {len(df_raw)} records")
    
    # Engineer features
    df_engineered = engineer_features(df_raw)
    
    # Prepare splits
    df_engineered, train_idx, val_idx, test_idx = prepare_training_data(df_engineered)
    
    # Save engineered features
    output_path = 'data/raw/features_engineered.csv'
    df_engineered.to_csv(output_path, index=False)
    logger.info(f"\n✅ Saved engineered features to {output_path}")
    
    # Print sample features
    logger.info("\n📋 Sample engineered features:")
    feature_cols = [col for col in df_engineered.columns 
                   if col not in ['date', 'season', 'player_name', 'team', 'opponent', 'year', 
                                  'PTS_actual', 'AST_actual', 'REB_actual', 'STL_actual', 'BLK_actual']]
    print("\nFeature list:")
    for i, col in enumerate(feature_cols[:20], 1):
        print(f"  {i:2d}. {col}")
    print(f"  ... and {len(feature_cols) - 20} more features")
    
    print(f"\n✅ Feature engineering complete!")
