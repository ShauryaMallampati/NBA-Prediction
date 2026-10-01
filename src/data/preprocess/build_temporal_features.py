"""Time-based features that capture when games happen and recent momentum.

We track things like:
- Recent form: What have you done for me lately?
- Season timing: Early season rust vs. playoff push
- Calendar effects: Monday games? End of month?
- Day-of-week patterns: Teams play differently on different nights
- Momentum: Are they hot right now or slumping?
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def add_recency_weighting(df: pd.DataFrame, decay_factor: float = 0.95) -> pd.DataFrame:
    """Weight recent games more heavily than old ones.
    
    What happened last week matters more than what happened two months ago.
    We use exponential decay so each game fades gradually over time.
    
    Features:
    - home_recent_weighted_form: Home team's recent record with emphasis on latest games
    - away_recent_weighted_form: Away team's recent record, same deal
    - home_recent_weighted_pts: How many points they've been scoring lately
    - away_recent_weighted_pts: Same for the away team
    """
    logger.info("⏰ Adding recency weighting features...")
    
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # Calculate recency-weighted form
    def calculate_weighted_form(team_games, decay_factor):
        """Calculate weighted form with exponential decay."""
        form_values = []
        for i, row in team_games.iterrows():
            prev_games = team_games[team_games['date'] < row['date']].tail(10)
            
            if len(prev_games) == 0:
                form_values.append(0.5)
            else:
                # Exponential decay weights
                days_ago = (row['date'] - prev_games['date']).dt.days.values
                weights = [decay_factor ** days for days in days_ago]
                weights = np.array(weights) / np.sum(weights)  # Normalize
                
                wins = prev_games['home_win'].values if 'home_win' in prev_games.columns else prev_games['away_win'].values
                weighted_form = np.average(wins, weights=weights)
                form_values.append(weighted_form)
        
        return form_values
    
    # Home team weighted form
    df['home_recent_weighted_form'] = 0.5
    for team in df['home'].unique():
        team_games = df[df['home'] == team].copy()
        team_games = team_games.sort_values('date')
        
        if 'home_win' not in team_games.columns:
            team_games['home_win'] = (team_games['home_pts'] > team_games['away_pts']).astype(int)
        
        form_values = calculate_weighted_form(team_games, decay_factor)
        team_indices = team_games.index
        df.loc[team_indices, 'home_recent_weighted_form'] = form_values
    
    # Away team weighted form
    df['away_recent_weighted_form'] = 0.5
    for team in df['away'].unique():
        team_games = df[df['away'] == team].copy()
        team_games = team_games.sort_values('date')
        
        if 'away_win' not in team_games.columns:
            team_games['away_win'] = (team_games['away_pts'] > team_games['home_pts']).astype(int)
        
        form_values = calculate_weighted_form(team_games, decay_factor)
        team_indices = team_games.index
        df.loc[team_indices, 'away_recent_weighted_form'] = form_values
    
    # Fill NaN
    df['home_recent_weighted_form'] = df['home_recent_weighted_form'].fillna(0.5)
    df['away_recent_weighted_form'] = df['away_recent_weighted_form'].fillna(0.5)
    
    logger.info("  ✓ Added 2 recency weighting features")
    return df


def add_seasonal_adjustments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add seasonal adjustment features.
    
    Features:
    - season_phase: Early season (0-20 games), mid season (21-60), late season (61-82)
    - home_season_phase_win_pct: Home team's win percentage in current season phase
    - away_season_phase_win_pct: Away team's win percentage in current season phase
    """
    logger.info("📅 Adding seasonal adjustment features...")
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Determine season phase based on game number
    df = df.sort_values('date').reset_index(drop=True)
    
    # Game number in season for each team
    df['home_game_number'] = df.groupby(['home', 'season']).cumcount() + 1
    df['away_game_number'] = df.groupby(['away', 'season']).cumcount() + 1
    
    # Season phase (early: 1-20, mid: 21-60, late: 61-82)
    def get_season_phase(game_number):
        if game_number <= 20:
            return 0  # Early season
        elif game_number <= 60:
            return 1  # Mid season
        else:
            return 2  # Late season
    
    df['home_season_phase'] = df['home_game_number'].apply(get_season_phase)
    df['away_season_phase'] = df['away_game_number'].apply(get_season_phase)
    
    # Calculate win percentage by season phase
    df = df.sort_values('date').reset_index(drop=True)
    
    # Home team win percentage by phase
    home_phase_wins = {}
    for team in df['home'].unique():
        team_games = df[df['home'] == team].copy()
        team_games = team_games.sort_values('date')
        
        phase_win_pcts = []
        for idx, row in team_games.iterrows():
            phase = row['home_season_phase']
            prev_games_same_phase = team_games[
                (team_games['date'] < row['date']) &
                (team_games['home_season_phase'] == phase)
            ]
            
            if len(prev_games_same_phase) > 0:
                win_pct = prev_games_same_phase['home_win'].mean()
            else:
                win_pct = 0.5  # League average
            
            phase_win_pcts.append(win_pct)
        
        home_phase_wins[team] = phase_win_pcts
    
    # Map back to dataframe
    df['home_season_phase_win_pct'] = 0.5
    for team, win_pcts in home_phase_wins.items():
        team_indices = df[df['home'] == team].index
        df.loc[team_indices, 'home_season_phase_win_pct'] = win_pcts[:len(team_indices)]
    
    # Similar for away team
    away_phase_wins = {}
    for team in df['away'].unique():
        team_games = df[df['away'] == team].copy()
        team_games = team_games.sort_values('date')
        
        phase_win_pcts = []
        for idx, row in team_games.iterrows():
            phase = row['away_season_phase']
            prev_games_same_phase = team_games[
                (team_games['date'] < row['date']) &
                (team_games['away_season_phase'] == phase)
            ]
            
            if len(prev_games_same_phase) > 0:
                win_pct = prev_games_same_phase['away_win'].mean()
            else:
                win_pct = 0.5
            
            phase_win_pcts.append(win_pct)
        
        away_phase_wins[team] = phase_win_pcts
    
    df['away_season_phase_win_pct'] = 0.5
    for team, win_pcts in away_phase_wins.items():
        team_indices = df[df['away'] == team].index
        df.loc[team_indices, 'away_season_phase_win_pct'] = win_pcts[:len(team_indices)]
    
    # Fill NaN
    df['home_season_phase_win_pct'] = df['home_season_phase_win_pct'].fillna(0.5)
    df['away_season_phase_win_pct'] = df['away_season_phase_win_pct'].fillna(0.5)
    
    logger.info("  ✓ Added 5 seasonal adjustment features")
    return df


def add_month_based_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add month-based win percentage features.
    
    Features:
    - home_month_win_pct: Home team's win percentage in current month
    - away_month_win_pct: Away team's win percentage in current month
    - month: Month of the year (1-12)
    """
    logger.info("📆 Adding month-based features...")
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    
    # Calculate month-based win percentage
    df = df.sort_values('date').reset_index(drop=True)
    
    # Home team month win percentage
    df['home_month_win_pct'] = 0.5
    for team in df['home'].unique():
        team_games = df[df['home'] == team].copy()
        team_games = team_games.sort_values('date')
        
        month_win_pcts = []
        for idx, row in team_games.iterrows():
            month = row['month']
            year = row['year']
            
            prev_games_same_month = team_games[
                (team_games['date'] < row['date']) &
                (team_games['month'] == month)
            ]
            
            if len(prev_games_same_month) > 0:
                win_pct = prev_games_same_month['home_win'].mean()
            else:
                win_pct = 0.5  # League average
            
            month_win_pcts.append(win_pct)
        
        team_indices = team_games.index
        df.loc[team_indices, 'home_month_win_pct'] = month_win_pcts[:len(team_indices)]
    
    # Away team month win percentage
    df['away_month_win_pct'] = 0.5
    for team in df['away'].unique():
        team_games = df[df['away'] == team].copy()
        team_games = team_games.sort_values('date')
        
        month_win_pcts = []
        for idx, row in team_games.iterrows():
            month = row['month']
            
            prev_games_same_month = team_games[
                (team_games['date'] < row['date']) &
                (team_games['month'] == month)
            ]
            
            if len(prev_games_same_month) > 0:
                win_pct = prev_games_same_month['away_win'].mean()
            else:
                win_pct = 0.5
            
            month_win_pcts.append(win_pct)
        
        team_indices = team_games.index
        df.loc[team_indices, 'away_month_win_pct'] = month_win_pcts[:len(team_indices)]
    
    # Fill NaN
    df['home_month_win_pct'] = df['home_month_win_pct'].fillna(0.5)
    df['away_month_win_pct'] = df['away_month_win_pct'].fillna(0.5)
    
    logger.info("  ✓ Added 3 month-based features")
    return df


def add_day_of_week_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add day-of-week effects.
    
    Features:
    - day_of_week: Day of week (0=Monday, 6=Sunday)
    - home_day_win_pct: Home team's win percentage on this day of week
    - away_day_win_pct: Away team's win percentage on this day of week
    """
    logger.info("📅 Adding day-of-week features...")
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df['day_of_week'] = df['date'].dt.dayofweek  # 0=Monday, 6=Sunday
    
    # Calculate day-of-week win percentage
    df = df.sort_values('date').reset_index(drop=True)
    
    # Home team day win percentage
    df['home_day_win_pct'] = 0.5
    for team in df['home'].unique():
        team_games = df[df['home'] == team].copy()
        team_games = team_games.sort_values('date')
        
        day_win_pcts = []
        for idx, row in team_games.iterrows():
            day = row['day_of_week']
            
            prev_games_same_day = team_games[
                (team_games['date'] < row['date']) &
                (team_games['day_of_week'] == day)
            ]
            
            if len(prev_games_same_day) > 0:
                win_pct = prev_games_same_day['home_win'].mean()
            else:
                win_pct = 0.5  # League average
            
            day_win_pcts.append(win_pct)
        
        team_indices = team_games.index
        df.loc[team_indices, 'home_day_win_pct'] = day_win_pcts[:len(team_indices)]
    
    # Away team day win percentage
    df['away_day_win_pct'] = 0.5
    for team in df['away'].unique():
        team_games = df[df['away'] == team].copy()
        team_games = team_games.sort_values('date')
        
        day_win_pcts = []
        for idx, row in team_games.iterrows():
            day = row['day_of_week']
            
            prev_games_same_day = team_games[
                (team_games['date'] < row['date']) &
                (team_games['day_of_week'] == day)
            ]
            
            if len(prev_games_same_day) > 0:
                win_pct = prev_games_same_day['away_win'].mean()
            else:
                win_pct = 0.5
            
            day_win_pcts.append(win_pct)
        
        team_indices = team_games.index
        df.loc[team_indices, 'away_day_win_pct'] = day_win_pcts[:len(team_indices)]
    
    # Fill NaN
    df['home_day_win_pct'] = df['home_day_win_pct'].fillna(0.5)
    df['away_day_win_pct'] = df['away_day_win_pct'].fillna(0.5)
    
    logger.info("  ✓ Added 3 day-of-week features")
    return df


def add_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add momentum indicators.
    
    Features:
    - home_momentum_3: Home team's momentum (last 3 games)
    - away_momentum_3: Away team's momentum (last 3 games)
    - home_momentum_5: Home team's momentum (last 5 games)
    - away_momentum_5: Away team's momentum (last 5 games)
    - home_momentum_10: Home team's momentum (last 10 games)
    - away_momentum_10: Away team's momentum (last 10 games)
    """
    logger.info("🚀 Adding momentum indicators...")
    
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # Calculate momentum (win percentage in last N games)
    # Momentum = (wins - losses) / games
    def calculate_momentum(team_games, n_games):
        """Calculate momentum over last N games."""
        momentum_values = []
        for idx, row in team_games.iterrows():
            prev_games = team_games[team_games['date'] < row['date']].tail(n_games)
            
            if len(prev_games) == 0:
                momentum_values.append(0.0)  # No momentum
            else:
                wins = prev_games['home_win'].sum() if 'home_win' in prev_games.columns else prev_games['away_win'].sum()
                losses = len(prev_games) - wins
                momentum = (wins - losses) / len(prev_games)
                momentum_values.append(momentum)
        
        return momentum_values
    
    # Home team momentum
    for n in [3, 5, 10]:
        df[f'home_momentum_{n}'] = 0.0
        for team in df['home'].unique():
            team_games = df[df['home'] == team].copy()
            team_games = team_games.sort_values('date')
            
            if 'home_win' not in team_games.columns:
                team_games['home_win'] = (team_games['home_pts'] > team_games['away_pts']).astype(int)
            
            momentum_values = calculate_momentum(team_games, n)
            team_indices = team_games.index
            df.loc[team_indices, f'home_momentum_{n}'] = momentum_values[:len(team_indices)]
    
    # Away team momentum
    for n in [3, 5, 10]:
        df[f'away_momentum_{n}'] = 0.0
        for team in df['away'].unique():
            team_games = df[df['away'] == team].copy()
            team_games = team_games.sort_values('date')
            
            if 'away_win' not in team_games.columns:
                team_games['away_win'] = (team_games['away_pts'] > team_games['home_pts']).astype(int)
            
            momentum_values = calculate_momentum(team_games, n)
            team_indices = team_games.index
            df.loc[team_indices, f'away_momentum_{n}'] = momentum_values[:len(team_indices)]
    
    # Fill NaN
    for n in [3, 5, 10]:
        df[f'home_momentum_{n}'] = df[f'home_momentum_{n}'].fillna(0.0)
        df[f'away_momentum_{n}'] = df[f'away_momentum_{n}'].fillna(0.0)
    
    logger.info("  ✓ Added 6 momentum indicator features")
    return df


def add_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all temporal features to dataframe.
    
    Args:
        df: Input dataframe with basic game data
    
    Returns:
        Dataframe with all temporal features added
    """
    logger.info("=" * 80)
    logger.info("TEMPORAL FEATURE ENGINEERING")
    logger.info("=" * 80)
    
    df = df.copy()
    
    # Ensure date column is datetime
    if 'date' not in df.columns:
        raise ValueError("Dataframe must have 'date' column")
    
    df['date'] = pd.to_datetime(df['date'])
    
    # Add win columns if not present
    if 'home_win' not in df.columns:
        df['home_win'] = (df['home_pts'] > df['away_pts']).astype(int)
    if 'away_win' not in df.columns:
        df['away_win'] = (df['away_pts'] > df['home_pts']).astype(int)
    
    # Add season column if not present
    if 'season' not in df.columns:
        df['season'] = df['date'].dt.year
    
    # Add all temporal features
    df = add_recency_weighting(df)
    df = add_seasonal_adjustments(df)
    df = add_month_based_features(df)
    df = add_day_of_week_features(df)
    df = add_momentum_indicators(df)
    
    logger.info("=" * 80)
    logger.info("TEMPORAL FEATURE ENGINEERING COMPLETE")
    logger.info(f"Total temporal features added: 19")
    logger.info(f"Total columns: {len(df.columns)}")
    logger.info("=" * 80)
    
    return df


if __name__ == "__main__":
    # Example usage
    import pandas as pd
    from pathlib import Path
    
    # Load sample data
    data_dir = Path("data/processed")
    if (data_dir / "games.csv").exists():
        df = pd.read_csv(data_dir / "games.csv")
        df['date'] = pd.to_datetime(df['date'])
        
        # Add temporal features
        df_temporal = add_temporal_features(df)
        
        # Save
        output_path = data_dir / "games_temporal_features.csv"
        df_temporal.to_csv(output_path, index=False)
        logger.info(f"✅ Saved temporal features to {output_path}")
    else:
        logger.warning("Sample data not found. Create sample data first.")

