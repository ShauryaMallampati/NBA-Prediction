import pandas as pd
import numpy as np
import pathlib
import logging

logger = logging.getLogger(__name__)

class LiveFeatureEngineer:
    def __init__(self, historical_features_path="artifacts/features/pregame.parquet"):
        self.path = pathlib.Path(historical_features_path)
        self.df_hist = None
        self.latest_state = {}
        if self.path.exists():
            try:
                self.df_hist = pd.read_parquet(self.path)
                self._precompute_latest_state()
            except Exception as e:
                logger.error(f"Error loading historical features: {e}")

    def _precompute_latest_state(self):
        """Precompute the latest known state (streak, form, etc) for each team."""
        if self.df_hist is None: return
        
        # Sort by date to get the most recent games
        df = self.df_hist.sort_values('date')
        
        # Get all unique teams
        all_teams = set(df['home'].unique()) | set(df['away'].unique())
        
        for team in all_teams:
            # Get last game for this team (either home or away)
            team_games = df[(df['home'] == team) | (df['away'] == team)]
            if team_games.empty: continue
            
            last_game = team_games.iloc[-1]
            
            # Extract relevant 'rolling' features depending on whether they were home or away
            is_home = last_game['home'] == team
            prefix = 'home_' if is_home else 'away_'
            
            state = {
                'win_streak': last_game.get(f'{prefix}win_streak', 0),
                'loss_streak': last_game.get(f'{prefix}loss_streak', 0),
                'elo': last_game.get(f'elo_{"home" if is_home else "away"}', 1500),
                'recent_form': last_game.get(f'{prefix}recent_form', 0.5),
            }
            self.latest_state[team] = state

    def create_live_features(self, upcoming_games: pd.DataFrame, model_feature_names: list) -> pd.DataFrame:
        """Create feature vectors for upcoming games based on latest team states."""
        live_games = []
        
        for idx, row in upcoming_games.iterrows():
            home = row['home_team']
            away = row['away_team']
            
            home_state = self.latest_state.get(home, {'elo': 1500, 'win_streak': 0, 'loss_streak': 0, 'recent_form': 0.5})
            away_state = self.latest_state.get(away, {'elo': 1500, 'win_streak': 0, 'loss_streak': 0, 'recent_form': 0.5})
            
            # Construct feature dict matching the model's expectation
            feat = {col: 0.0 for col in model_feature_names} # Default/Neutral
            
            # Map known states if they exist in the feature set
            if 'elo_home' in feat: feat['elo_home'] = float(home_state['elo'])
            if 'elo_away' in feat: feat['elo_away'] = float(away_state['elo'])
            if 'elo_diff' in feat: feat['elo_diff'] = float(home_state['elo'] - away_state['elo'])
            if 'home_win_streak' in feat: feat['home_win_streak'] = float(home_state['win_streak'])
            if 'away_win_streak' in feat: feat['away_win_streak'] = float(away_state['win_streak'])
            if 'home_recent_form' in feat: feat['home_recent_form'] = float(home_state['recent_form'])
            if 'away_recent_form' in feat: feat['away_recent_form'] = float(away_state['recent_form'])
            if 'home_adv_flag' in feat: feat['home_adv_flag'] = 1.0
            if 'home_court_adv' in feat: feat['home_court_adv'] = 0.03
            
            # Add identifiers for joining later (not part of training features)
            feat['game_id'] = row['game_id']
            live_games.append(feat)
            
        return pd.DataFrame(live_games)
