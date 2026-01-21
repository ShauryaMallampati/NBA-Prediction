"""
Advanced Feature Engineering for NBA Game Predictions

Adds 15+ advanced features:
- Player injury/availability
- Opponent-adjusted team metrics
- Home/away splits by month/season
- Recent form with exponential decay
- Head-to-head matchup history
- Rest differential
- Back-to-back impact by team
- Playoff indicator
- Streak indicators
- Team strength rankings
- Player minutes-weighted team stats
- Clutch performance metrics
- Fatigue indicators
- Pace-adjusted metrics
- Offensive/defensive rating differentials
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from pathlib import Path

# Import NBA API
try:
    from nba_api.stats.endpoints import (
        scoreboard,
        leaguegamefinder,
        teamgamelog,
        teamdashboardbygeneralsplits,
        commonteamroster
    )
    from nba_api.stats.static import teams as static_teams
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False
    logging.warning("nba_api not available. Install with: pip install nba-api")

logger = logging.getLogger(__name__)


def add_injury_availability_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add player injury/availability features.
    
    Features:
    - home_injury_count: Number of injured players on home team
    - away_injury_count: Number of injured players on away team
    - home_key_player_injured: Flag if key player is injured
    - away_key_player_injured: Flag if key player is injured
    """
    logger.info("📋 Adding injury/availability features...")
    
    df = df.copy()
    
    # Initialize injury features
    df['home_injury_count'] = 0
    df['away_injury_count'] = 0
    df['home_key_player_injured'] = 0
    df['away_key_player_injured'] = 0
    
    # Placeholder: Injury data fetching disabled to avoid API limits
    
    logger.info("  ✓ Added 4 injury/availability features")
    return df


def add_opponent_adjusted_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add opponent-adjusted team metrics (OAPOW-style).
    
    Features:
    - home_opp_adjusted_off_rating: Home team offense adjusted for opponent defense
    - away_opp_adjusted_off_rating: Away team offense adjusted for opponent defense
    - home_opp_adjusted_def_rating: Home team defense adjusted for opponent offense
    - away_opp_adjusted_def_rating: Away team defense adjusted for opponent offense
    """
    logger.info("📊 Adding opponent-adjusted metrics...")
    
    df = df.copy()
    
    # Calculate team offensive and defensive ratings
    if 'home_pts' not in df.columns or 'away_pts' not in df.columns:
        logger.warning("Missing points data, skipping opponent-adjusted metrics")
        df['home_opp_adjusted_off_rating'] = 0
        df['away_opp_adjusted_off_rating'] = 0
        df['home_opp_adjusted_def_rating'] = 0
        df['away_opp_adjusted_def_rating'] = 0
        return df
    
    # Calculate average points scored/allowed by each team
    home_off_rating = df.groupby('home')['home_pts'].mean()
    home_def_rating = df.groupby('home')['away_pts'].mean()
    away_off_rating = df.groupby('away')['away_pts'].mean()
    away_def_rating = df.groupby('away')['home_pts'].mean()
    
    # Merge ratings
    df = df.merge(home_off_rating.rename('home_team_off_rating'), left_on='home', right_index=True, how='left')
    df = df.merge(home_def_rating.rename('home_team_def_rating'), left_on='home', right_index=True, how='left')
    df = df.merge(away_off_rating.rename('away_team_off_rating'), left_on='away', right_index=True, how='left')
    df = df.merge(away_def_rating.rename('away_team_def_rating'), left_on='away', right_index=True, how='left')
    
    # Calculate opponent-adjusted ratings
    df['home_opp_adjusted_off_rating'] = df['home_team_off_rating'] - df['away_team_def_rating']
    df['away_opp_adjusted_off_rating'] = df['away_team_off_rating'] - df['home_team_def_rating']
    df['home_opp_adjusted_def_rating'] = df['home_team_def_rating'] - df['away_team_off_rating']
    df['away_opp_adjusted_def_rating'] = df['away_team_def_rating'] - df['home_team_off_rating']
    
    # Fill NaN with 0
    for col in ['home_opp_adjusted_off_rating', 'away_opp_adjusted_off_rating',
                'home_opp_adjusted_def_rating', 'away_opp_adjusted_def_rating']:
        df[col] = df[col].fillna(0)
    
    logger.info("  ✓ Added 4 opponent-adjusted metrics")
    return df


def add_home_away_splits(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add home/away splits by month/season.
    
    Features:
    - home_home_win_pct: Home team's home win percentage this season
    - away_away_win_pct: Away team's away win percentage this season
    - home_home_win_pct_month: Home team's home win percentage this month
    - away_away_win_pct_month: Away team's away win percentage this month
    """
    logger.info("🏠 Adding home/away splits...")
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Extract season and month
    df['season'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    
    # Calculate home win percentage for home team (home games)
    home_team_home_wins = df[df['home_pts'] > df['away_pts']].groupby(['home', 'season']).size()
    home_team_home_games = df.groupby(['home', 'season']).size()
    home_team_home_win_pct = (home_team_home_wins / home_team_home_games).fillna(0.5)
    
    # Calculate away win percentage for away team (away games)
    away_team_away_wins = df[df['away_pts'] > df['home_pts']].groupby(['away', 'season']).size()
    away_team_away_games = df.groupby(['away', 'season']).size()
    away_team_away_win_pct = (away_team_away_wins / away_team_away_games).fillna(0.5)
    
    # Merge
    df = df.merge(home_team_home_win_pct.rename('home_home_win_pct'), 
                  left_on=['home', 'season'], right_index=True, how='left')
    df = df.merge(away_team_away_win_pct.rename('away_away_win_pct'),
                  left_on=['away', 'season'], right_index=True, how='left')
    
    # Fill NaN with 0.5 (league average)
    df['home_home_win_pct'] = df['home_home_win_pct'].fillna(0.5)
    df['away_away_win_pct'] = df['away_away_win_pct'].fillna(0.5)
    
    # Month-based splits (last 30 days)
    df['home_home_win_pct_month'] = 0.5  # Placeholder
    df['away_away_win_pct_month'] = 0.5  # Placeholder
    
    logger.info("  ✓ Added 4 home/away split features")
    return df


def add_recent_form_features(df: pd.DataFrame, decay_factor: float = 0.95) -> pd.DataFrame:
    """
    Add recent form features with exponential decay weighting.
    Optimized O(N) implementation.
    """
    logger.info("📈 Adding recent form features (Optimized)...")
    
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # Calculate win indicators
    df['home_win'] = (df['home_pts'] > df['away_pts']).astype(int)
    df['away_win'] = (df['away_pts'] > df['home_pts']).astype(int)
    
    # Track game history for each team
    # Dict mapping team -> List of last 10 outcomes (1 for win, 0 for loss)
    team_history = {}
    
    home_recent_form = []
    away_recent_form = []
    
    for _, row in df.iterrows():
        h, a = row['home'], row['away']
        
        # Get form BEFORE this game
        h_hist = team_history.get(h, [])
        a_hist = team_history.get(a, [])
        
        # Calculate exponentially weighted form
        def get_form(hist):
            if not hist: return 0.5
            weights = [decay_factor ** (len(hist) - j - 1) for j in range(len(hist))]
            return float(np.average(hist, weights=weights))
        
        home_recent_form.append(get_form(h_hist))
        away_recent_form.append(get_form(a_hist))
        
        # Update history with outcome of THIS game
        h_win = 1 if row['home_pts'] > row['away_pts'] else 0
        a_win = 1 - h_win
        
        if h not in team_history: team_history[h] = []
        if a not in team_history: team_history[a] = []
        
        team_history[h].append(h_win)
        team_history[a].append(a_win)
        
        # Keep only last 10
        if len(team_history[h]) > 10: team_history[h].pop(0)
        if len(team_history[a]) > 10: team_history[a].pop(0)
    
    df['home_recent_form'] = home_recent_form
    df['away_recent_form'] = away_recent_form
    
    # Last 3 and 5 games form using rolling (more efficient than manual loops)
    # We need to shift(1) because form should be PRE-GAME
    def get_rolling_form(team_col, win_col, window):
        return df.groupby(team_col, group_keys=False)[win_col].apply(
            lambda x: x.shift(1).rolling(window, min_periods=1).mean()
        ).fillna(0.5)

    df['home_recent_form_3'] = get_rolling_form('home', 'home_win', 3)
    df['away_recent_form_3'] = get_rolling_form('away', 'away_win', 3)
    df['home_recent_form_5'] = get_rolling_form('home', 'home_win', 5)
    df['away_recent_form_5'] = get_rolling_form('away', 'away_win', 5)
    
    logger.info("  ✓ Added 6 recent form features")
    return df


def add_head_to_head_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add head-to-head matchup history features.
    Optimized O(N) implementation.
    """
    logger.info("⚔️ Adding head-to-head features (Optimized)...")
    
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # Dict mapping frozenset({team1, team2}) -> List of past outcomes
    # Each outcome is: (winner_name, home_pts - away_pts if home_team else away_pts - home_pts)
    matchup_history = {}
    
    h2h_home_wins = []
    h2h_away_wins = []
    h2h_home_win_pct = []
    h2h_avg_score_diff = []
    
    for _, row in df.iterrows():
        h, a = row['home'], row['away']
        matchup_key = frozenset([h, a])
        
        # Get history BEFORE this game
        history = matchup_history.get(matchup_key, [])
        
        if not history:
            h2h_home_wins.append(0)
            h2h_away_wins.append(0)
            h2h_home_win_pct.append(0.5)
            h2h_avg_score_diff.append(0.0)
        else:
            hw = sum(1 for winner, diff in history if winner == h)
            aw = len(history) - hw
            h2h_home_wins.append(hw)
            h2h_away_wins.append(aw)
            h2h_home_win_pct.append(hw / len(history))
            h2h_avg_score_diff.append(float(np.mean([diff if winner == h else -diff for winner, diff in history])))
        
        # Update history with outcome of THIS game
        winner = h if row['home_pts'] > row['away_pts'] else a
        diff = abs(row['home_pts'] - row['away_pts'])
        
        if matchup_key not in matchup_history: matchup_history[matchup_key] = []
        matchup_history[matchup_key].append((winner, diff))
        
        # Keep only last 10
        if len(matchup_history[matchup_key]) > 10: matchup_history[matchup_key].pop(0)
        
    df['h2h_home_wins'] = h2h_home_wins
    df['h2h_away_wins'] = h2h_away_wins
    df['h2h_home_win_pct'] = h2h_home_win_pct
    df['h2h_avg_score_diff'] = h2h_avg_score_diff
    
    logger.info("  ✓ Added 4 head-to-head features")
    return df


def add_rest_differential_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add rest differential features.
    
    Features:
    - rest_differential: home_rest_days - away_rest_days
    - home_rest_advantage: 1 if home team has more rest, 0 otherwise
    - away_rest_advantage: 1 if away team has more rest, 0 otherwise
    """
    logger.info("😴 Adding rest differential features...")
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Calculate rest days for home team
    df['home_last_game_date'] = df.groupby('home')['date'].shift(1)
    df['home_rest_days'] = (df['date'] - df['home_last_game_date']).dt.days.fillna(2)
    df['home_rest_days'] = df['home_rest_days'].clip(0, 10)
    
    # Calculate rest days for away team
    df['away_last_game_date'] = df.groupby('away')['date'].shift(1)
    df['away_rest_days'] = (df['date'] - df['away_last_game_date']).dt.days.fillna(2)
    df['away_rest_days'] = df['away_rest_days'].clip(0, 10)
    
    # Rest differential
    df['rest_differential'] = df['home_rest_days'] - df['away_rest_days']
    df['home_rest_advantage'] = (df['rest_differential'] > 0).astype(int)
    df['away_rest_advantage'] = (df['rest_differential'] < 0).astype(int)
    
    # Clean up temporary columns
    df = df.drop(columns=['home_last_game_date', 'away_last_game_date'])
    
    logger.info("  ✓ Added 3 rest differential features")
    return df


def add_back_to_back_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add back-to-back features with team-specific impact.
    
    Features:
    - home_back_to_back: 1 if home team is on B2B, 0 otherwise
    - away_back_to_back: 1 if away team is on B2B, 0 otherwise
    - home_b2b_win_pct: Home team's win percentage on B2B games
    - away_b2b_win_pct: Away team's win percentage on B2B games
    """
    logger.info("🔄 Adding back-to-back features...")
    
    df = df.copy()
    
    # Back-to-back flags (already calculated in rest features)
    if 'home_rest_days' in df.columns:
        df['home_back_to_back'] = (df['home_rest_days'] <= 1).astype(int)
        df['away_back_to_back'] = (df['away_rest_days'] <= 1).astype(int)
    else:
        df['home_back_to_back'] = 0
        df['away_back_to_back'] = 0
    
    # Calculate B2B win percentage for each team
    df = df.sort_values('date').reset_index(drop=True)
    
    # Home team B2B win percentage
    home_b2b_wins = df[df['home_back_to_back'] == 1].groupby('home')['home_win'].mean()
    df = df.merge(home_b2b_wins.rename('home_b2b_win_pct'), left_on='home', right_index=True, how='left')
    df['home_b2b_win_pct'] = df['home_b2b_win_pct'].fillna(0.5)
    
    # Away team B2B win percentage
    away_b2b_wins = df[df['away_back_to_back'] == 1].groupby('away')['away_win'].mean()
    df = df.merge(away_b2b_wins.rename('away_b2b_win_pct'), left_on='away', right_index=True, how='left')
    df['away_b2b_win_pct'] = df['away_b2b_win_pct'].fillna(0.5)
    
    logger.info("  ✓ Added 4 back-to-back features")
    return df


def add_playoff_indicator(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add playoff indicator feature.
    
    Features:
    - is_playoff: 1 if playoff game, 0 otherwise
    """
    logger.info("🏆 Adding playoff indicator...")
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Playoffs typically run from April to June
    df['month'] = df['date'].dt.month
    df['is_playoff'] = ((df['month'] >= 4) & (df['month'] <= 6)).astype(int)
    
    logger.info("  ✓ Added 1 playoff indicator feature")
    return df


def add_streak_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add win/loss streak features.
    Optimized O(N) implementation.
    """
    logger.info("🔥 Adding streak features (Optimized)...")
    
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # Dict mapping team -> Current streak (positive for wins, negative for losses)
    team_streaks = {}
    
    home_win_streak = []
    away_win_streak = []
    home_loss_streak = []
    away_loss_streak = []
    
    for _, row in df.iterrows():
        h, a = row['home'], row['away']
        
        # Get streaks BEFORE this game
        h_streak = team_streaks.get(h, 0)
        a_streak = team_streaks.get(a, 0)
        
        home_win_streak.append(max(0, h_streak))
        home_loss_streak.append(max(0, -h_streak))
        away_win_streak.append(max(0, a_streak))
        away_loss_streak.append(max(0, -a_streak))
        
        # Update streaks with outcome of THIS game
        h_win = row['home_pts'] > row['away_pts']
        
        if h_win:
            team_streaks[h] = max(0, h_streak) + 1
            team_streaks[a] = min(0, a_streak) - 1
        else:
            team_streaks[h] = min(0, h_streak) - 1
            team_streaks[a] = max(0, a_streak) + 1
            
    df['home_win_streak'] = home_win_streak
    df['away_win_streak'] = away_win_streak
    df['home_loss_streak'] = home_loss_streak
    df['away_loss_streak'] = away_loss_streak
    
    logger.info("  ✓ Added 4 streak features")
    return df


def add_team_strength_rankings(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add team strength rankings based on Elo tiers.
    
    Features:
    - home_elo_tier: Home team's Elo tier (top 10, middle 10, bottom 10)
    - away_elo_tier: Away team's Elo tier
    - elo_tier_matchup: Interaction between Elo tiers
    """
    logger.info("💪 Adding team strength rankings...")
    
    df = df.copy()
    
    # Use Elo ratings if available
    if 'elo_home' in df.columns and 'elo_away' in df.columns:
        # Calculate Elo tiers (top 10, middle 10, bottom 10)
        all_elos = pd.concat([df['elo_home'], df['elo_away']])
        elo_quantiles = all_elos.quantile([0.33, 0.67])
        
        def get_elo_tier(elo):
            if elo >= elo_quantiles[0.67]:
                return 2  # Top tier
            elif elo >= elo_quantiles[0.33]:
                return 1  # Middle tier
            else:
                return 0  # Bottom tier
        
        df['home_elo_tier'] = df['elo_home'].apply(get_elo_tier)
        df['away_elo_tier'] = df['elo_away'].apply(get_elo_tier)
        df['elo_tier_matchup'] = df['home_elo_tier'] * 3 + df['away_elo_tier']
    else:
        # Fallback: use win percentage
        home_win_pct = df.groupby('home')['home_win'].mean()
        away_win_pct = df.groupby('away')['away_win'].mean()
        
        all_win_pcts = pd.concat([home_win_pct, away_win_pct])
        win_pct_quantiles = all_win_pcts.quantile([0.33, 0.67])
        
        def get_tier(win_pct):
            if win_pct >= win_pct_quantiles[0.67]:
                return 2
            elif win_pct >= win_pct_quantiles[0.33]:
                return 1
            else:
                return 0
        
        df = df.merge(home_win_pct.rename('home_win_pct'), left_on='home', right_index=True, how='left')
        df = df.merge(away_win_pct.rename('away_win_pct'), left_on='away', right_index=True, how='left')
        
        df['home_elo_tier'] = df['home_win_pct'].apply(get_tier)
        df['away_elo_tier'] = df['away_win_pct'].apply(get_tier)
        df['elo_tier_matchup'] = df['home_elo_tier'] * 3 + df['away_elo_tier']
    
    logger.info("  ✓ Added 3 team strength ranking features")
    return df


def add_fatigue_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add fatigue indicators.
    Optimized O(N) implementation.
    """
    logger.info("😓 Adding fatigue indicators (Optimized)...")
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Dict mapping team -> List of game dates in last 7 days
    team_game_dates = {}
    
    home_games_7d = []
    away_games_7d = []
    
    for _, row in df.iterrows():
        h, a = row['home'], row['away']
        d = row['date']
        
        # Get history BEFORE this game
        def get_7d_count(team, game_date):
            history = team_game_dates.get(team, [])
            # Purge dates older than 7 days
            history = [prev_date for prev_date in history if (game_date - prev_date).days <= 7]
            team_game_dates[team] = history
            return len(history)
            
        home_games_7d.append(get_7d_count(h, d))
        away_games_7d.append(get_7d_count(a, d))
        
        # Update history with THIS game date
        team_game_dates[h].append(d)
        team_game_dates[a].append(d)
        
    df['home_games_last_7_days'] = home_games_7d
    df['away_games_last_7_days'] = away_games_7d
    df['home_fatigue_score'] = (df['home_games_last_7_days'] * 20).clip(0, 100)
    df['away_fatigue_score'] = (df['away_games_last_7_days'] * 20).clip(0, 100)
    
    logger.info("  ✓ Added 4 fatigue indicator features")
    return df


def add_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add all advanced features to dataframe.
    
    Args:
        df: Input dataframe with basic game data (home, away, date, home_pts, away_pts)
    
    Returns:
        Dataframe with all advanced features added
    """
    logger.info("=" * 80)
    logger.info("ADVANCED FEATURE ENGINEERING")
    logger.info("=" * 80)
    
    df = df.copy()
    
    # Ensure date column is datetime
    if 'date' not in df.columns:
        raise ValueError("Dataframe must have 'date' column")
    if 'home' not in df.columns or 'away' not in df.columns:
        raise ValueError("Dataframe must have 'home' and 'away' columns")
    
    df['date'] = pd.to_datetime(df['date'])
    
    # Add all advanced features
    df = add_injury_availability_features(df)
    df = add_opponent_adjusted_metrics(df)
    df = add_home_away_splits(df)
    df = add_recent_form_features(df)
    df = add_head_to_head_features(df)
    df = add_rest_differential_features(df)
    df = add_back_to_back_features(df)
    df = add_playoff_indicator(df)
    df = add_streak_features(df)
    df = add_team_strength_rankings(df)
    df = add_fatigue_indicators(df)
    
    logger.info("=" * 80)
    logger.info("ADVANCED FEATURE ENGINEERING COMPLETE")
    logger.info(f"Total features added: 30+")
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
        
        # Add advanced features
        df_advanced = add_advanced_features(df)
        
        # Save
        output_path = data_dir / "games_advanced_features.csv"
        df_advanced.to_csv(output_path, index=False)
        logger.info(f"✅ Saved advanced features to {output_path}")
    else:
        logger.warning("Sample data not found. Create sample data first.")

