import pandas as pd
import numpy as np
import pathlib
import logging

logger = logging.getLogger(__name__)

class LiveFeatureEngineer:
    """
    Create features for live/upcoming games.
    
    Maps betting odds data to the model's expected features:
    - elo_home, elo_away, elo_diff, elo_win_prob
    - home_rest_days, away_rest_days
    - home_win_streak, away_win_streak
    - home_injury_count, etc.
    """
    
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
            team_games = df[(df['home'] == team) | (df['away'] == team)]
            if team_games.empty: continue
            
            last_game = team_games.iloc[-1]
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
        """
        Create feature vectors for upcoming games.
        
        Uses IMPLIED PROBABILITY from odds to estimate Elo differences.
        A team with 1.5 odds (67% implied prob) is a heavy favorite = higher Elo.
        """
        live_games = []
        
        # Use to_dict('records') instead of iterrows() for ~10x faster iteration
        upcoming_records = upcoming_games.to_dict('records')
        
        for row in upcoming_records:
            home = row.get('home_team', '')
            away = row.get('away_team', '')
            
            # Get team states from history
            home_state = self.latest_state.get(home, {'elo': 1500, 'win_streak': 0, 'loss_streak': 0, 'recent_form': 0.5})
            away_state = self.latest_state.get(away, {'elo': 1500, 'win_streak': 0, 'loss_streak': 0, 'recent_form': 0.5})
            
            # Get implied probability from odds (this is the KEY differentiator!)
            home_implied = row.get('home_implied_prob', 0.5)
            away_implied = row.get('away_implied_prob', 0.5)
            
            # Convert implied probability to Elo-like value
            # Formula: Elo difference = 400 * log10(p / (1-p))
            # If home has 60% implied prob, Elo diff = 400 * log10(0.6/0.4) = 70 points
            def prob_to_elo_diff(p):
                if p <= 0.01: p = 0.01
                if p >= 0.99: p = 0.99
                return 400 * np.log10(p / (1 - p))
            
            # Base Elo from history, adjusted by current odds
            elo_diff_from_odds = prob_to_elo_diff(home_implied) if home_implied > 0 else 0
            
            elo_home = home_state['elo']
            elo_away = away_state['elo']
            
            # If we have odds, adjust Elo to match the implied probability
            if home_implied > 0 and home_implied != 0.5:
                # Adjust so Elo diff matches odds-implied diff
                historical_diff = elo_home - elo_away
                adjustment = (elo_diff_from_odds - historical_diff) / 2
                elo_home = elo_home + adjustment
                elo_away = elo_away - adjustment
            
            elo_diff = elo_home - elo_away
            
            # Build feature dictionary
            feat = {}
            
            # CORE ELO FEATURES (most important!)
            feat['elo_home'] = elo_home
            feat['elo_away'] = elo_away
            feat['elo_p_home'] = elo_home  # Alias
            feat['elo_diff'] = elo_diff
            feat['elo_win_prob'] = home_implied if home_implied > 0 else 0.5
            
            # HOME ADVANTAGE
            feat['home_adv_flag'] = 1.0
            feat['home_court_adv'] = 0.03
            
            # INJURY FEATURES (use spread as proxy - bigger underdog = more injuries?)
            spread = row.get('home_spread_avg', 0)
            feat['home_injury_count'] = 0.0
            feat['away_injury_count'] = 0.0
            feat['home_key_player_injured'] = 0.0
            feat['away_key_player_injured'] = 0.0
            
            # REST FEATURES (assume average)
            feat['home_rest_days'] = 2.0
            feat['away_rest_days'] = 2.0
            feat['rest_differential'] = 0.0
            feat['home_rest_advantage'] = 0.0
            feat['away_rest_advantage'] = 0.0
            feat['home_back_to_back'] = 0.0
            feat['away_back_to_back'] = 0.0
            
            # PLAYOFF FLAG
            feat['is_playoff'] = 0.0
            
            # STREAK FEATURES
            feat['home_win_streak'] = float(home_state['win_streak'])
            feat['away_win_streak'] = float(away_state['win_streak'])
            feat['home_loss_streak'] = float(home_state['loss_streak'])
            feat['away_loss_streak'] = float(away_state['loss_streak'])
            
            # WORKLOAD/FATIGUE
            feat['home_games_last_7_days'] = 3.0  # Average
            feat['away_games_last_7_days'] = 3.0
            feat['home_fatigue_score'] = 0.0
            feat['away_fatigue_score'] = 0.0
            feat['home_game_number'] = 40.0  # Mid-season
            feat['away_game_number'] = 40.0
            feat['home_season_phase'] = 2.0  # Regular season
            feat['away_season_phase'] = 2.0
            
            # Ensure we only include features the model expects
            final_feat = {}
            for feature_name in model_feature_names:
                if feature_name in feat:
                    final_feat[feature_name] = float(feat[feature_name])
                else:
                    final_feat[feature_name] = 0.0
            
            # Add game ID for joining
            final_feat['game_id'] = row.get('game_id', '')
            live_games.append(final_feat)
        
        result = pd.DataFrame(live_games)
        logger.info(f"✅ Created live features for {len(result)} games")
        
        # Log sample to verify diversity
        if len(result) > 0:
            elo_diffs = [g.get('elo_diff', 0) for g in live_games]
            logger.info(f"   Elo diff range: {min(elo_diffs):.0f} to {max(elo_diffs):.0f}")
        
        return result
