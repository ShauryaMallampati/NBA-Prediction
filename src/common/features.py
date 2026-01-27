import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

def calculate_elo(df: pd.DataFrame, k: int = 20, home_advantage: float = 100) -> pd.DataFrame:
    """Calculate ELO ratings for all teams across all games."""
    elo_ratings = {}
    default_elo = 1500
    elo_home_list, elo_away_list, elo_diff_list, elo_win_prob_list = [], [], [], []
    
    df = df.sort_values('date').reset_index(drop=True)
    
    for idx, row in df.iterrows():
        home, away, home_win = row['home'], row['away'], row['home_win']
        home_elo = elo_ratings.get(home, default_elo)
        away_elo = elo_ratings.get(away, default_elo)
        
        elo_home_list.append(home_elo)
        elo_away_list.append(away_elo)
        elo_diff_list.append(home_elo - away_elo + home_advantage)
        
        exp_home = 1 / (1 + 10 ** ((away_elo - home_elo - home_advantage) / 400))
        elo_win_prob_list.append(exp_home)
        
        if pd.notna(home_win):
            new_home_elo = home_elo + k * (home_win - exp_home)
            new_away_elo = away_elo + k * ((1 - home_win) - (1 - exp_home))
            elo_ratings[home] = new_home_elo
            elo_ratings[away] = new_away_elo
            
    df['elo_home'] = elo_home_list
    df['elo_away'] = elo_away_list
    df['elo_diff'] = elo_diff_list
    df['elo_win_prob'] = elo_win_prob_list
    df['elo_p_home'] = df['elo_home'] / (df['elo_home'] + df['elo_away'])
    df['home_adv_flag'] = 1
    df['home_court_adv'] = 100
    return df

def add_rest_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add rest day features."""
    df = df.sort_values('date').reset_index(drop=True)
    last_game = {}
    home_rest, away_rest = [], []
    
    for idx, row in df.iterrows():
        home, away = row['home'], row['away']
        game_date = pd.to_datetime(row['date'])
        
        h_rest = (game_date - last_game.get(home, game_date - pd.Timedelta(days=3))).days
        a_rest = (game_date - last_game.get(away, game_date - pd.Timedelta(days=3))).days
        
        home_rest.append(min(h_rest, 7))
        away_rest.append(min(a_rest, 7))
        last_game[home], last_game[away] = game_date, game_date
        
    df['home_rest_days'] = home_rest
    df['away_rest_days'] = away_rest
    df['rest_differential'] = df['home_rest_days'] - df['away_rest_days']
    df['home_rest_advantage'] = (df['home_rest_days'] > df['away_rest_days']).astype(int)
    df['away_rest_advantage'] = (df['away_rest_days'] > df['home_rest_days']).astype(int)
    df['home_back_to_back'] = (df['home_rest_days'] <= 1).astype(int)
    df['away_back_to_back'] = (df['away_rest_days'] <= 1).astype(int)
    return df

def add_streak_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add win/loss streak features."""
    df = df.sort_values('date').reset_index(drop=True)
    win_streaks, loss_streaks = {}, {}
    h_win_s, a_win_s, h_loss_s, a_loss_s = [], [], [], []
    
    for idx, row in df.iterrows():
        home, away = row['home'], row['away']
        h_win_s.append(win_streaks.get(home, 0))
        a_win_s.append(win_streaks.get(away, 0))
        h_loss_s.append(loss_streaks.get(home, 0))
        a_loss_s.append(loss_streaks.get(away, 0))
        
        if pd.notna(row['home_win']):
            if row['home_win'] == 1:
                win_streaks[home] = win_streaks.get(home, 0) + 1
                loss_streaks[home] = 0
                win_streaks[away] = 0
                loss_streaks[away] = loss_streaks.get(away, 0) + 1
            else:
                win_streaks[home] = 0
                loss_streaks[home] = loss_streaks.get(home, 0) + 1
                win_streaks[away] = win_streaks.get(away, 0) + 1
                loss_streaks[away] = 0
                
    df['home_win_streak'], df['away_win_streak'] = h_win_s, a_win_s
    df['home_loss_streak'], df['away_loss_streak'] = h_loss_s, a_loss_s
    return df

def add_schedule_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add schedule-based features like games in last 7 days."""
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    h_games_7, a_games_7 = [], []
    for idx, row in df.iterrows():
        home, away, d = row['home'], row['away'], row['date']
        
        # This is a bit slow for 72k games but consistent
        h_7 = len(df[(df['date'] < d) & (df['date'] >= d - pd.Timedelta(days=7)) & ((df['home'] == home) | (df['away'] == home))])
        a_7 = len(df[(df['date'] < d) & (df['date'] >= d - pd.Timedelta(days=7)) & ((df['home'] == away) | (df['away'] == away))])
        
        h_games_7.append(h_7)
        a_games_7.append(a_7)
        
    df['home_games_last_7_days'], df['away_games_last_7_days'] = h_games_7, a_games_7
    df['home_fatigue_score'] = df['home_games_last_7_days'] / 4.0
    df['away_fatigue_score'] = df['away_games_last_7_days'] / 4.0
    
    # Season phase and game numbers
    df['month'] = df['date'].dt.month
    df['home_season_phase'] = df['month'].apply(lambda x: 1 if x in [10, 11] else (2 if x in [12, 1, 2] else 3))
    df['away_season_phase'] = df['home_season_phase']
    
    # Cumulative game number per team per season
    df['season'] = df['date'].dt.year - (df['date'].dt.month < 10).astype(int)
    df['home_game_number'] = df.groupby(['season', 'home']).cumcount() + 1
    df['away_game_number'] = df.groupby(['season', 'away']).cumcount() + 1
    
    return df

class RunningWorldState:
    """ Maintains the state of all teams (ELO, streaks, rest) for real-time simulation. """
    def __init__(self, default_elo=1500, k=20, home_advantage=100):
        self.elo_ratings = {}
        self.win_streaks = {}
        self.loss_streaks = {}
        self.last_game_date = {}
        self.games_in_last_7 = {} # {team: [dates]}
        # Track cumulative home/away game counts across all history
        self.home_game_counts = {}
        self.away_game_counts = {}
        self.default_elo = default_elo
        self.k = k
        self.home_advantage = home_advantage

    def _season_phase(self, d: pd.Timestamp) -> float:
        """
        Match historical_2024.parquet season phase mapping:
        0 = Oct/Nov/Dec, 1 = Jan/Feb, 2 = Mar-Apr-May-Jun-Jul-Aug-Sep
        """
        if d.month in [10, 11, 12]:
            return 0.0
        if d.month in [1, 2]:
            return 1.0
        return 2.0
        
    def get_team_features(self, home, away, date) -> Dict:
        """ Generate features for a pre-game matchup based on current state. """
        d = pd.to_datetime(date)
        h_elo = self.elo_ratings.get(home, self.default_elo)
        a_elo = self.elo_ratings.get(away, self.default_elo)
        
        # Rest
        h_rest = (d - self.last_game_date.get(home, d - pd.Timedelta(days=3))).days
        a_rest = (d - self.last_game_date.get(away, d - pd.Timedelta(days=3))).days
        h_rest = min(h_rest, 7)
        a_rest = min(a_rest, 7)
        
        # Fatigue (Last 7 days)
        cutoff = d - pd.Timedelta(days=7)
        h_g7 = len([dt for dt in self.games_in_last_7.get(home, []) if dt > cutoff])
        a_g7 = len([dt for dt in self.games_in_last_7.get(away, []) if dt > cutoff])

        # Home/Away game number within season (home/away specific counts)
        h_home_games = self.home_game_counts.get(home, 0)
        a_away_games = self.away_game_counts.get(away, 0)
        
        features = {
            'elo_home': h_elo,
            'elo_away': a_elo,
            'elo_p_home': h_elo / (h_elo + a_elo),
            'elo_diff': h_elo - a_elo + self.home_advantage,
            'elo_win_prob': 1 / (1 + 10 ** ((a_elo - h_elo - self.home_advantage) / 400)),
            'home_adv_flag': 1.0,
            'home_court_adv': 100.0,
            'home_injury_count': 0.0, 'away_injury_count': 0.0,
            'home_key_player_injured': 0.0, 'away_key_player_injured': 0.0,
            'home_rest_days': float(h_rest),
            'away_rest_days': float(a_rest),
            'rest_differential': float(h_rest - a_rest),
            'home_rest_advantage': 1.0 if h_rest > a_rest else 0.0,
            'away_rest_advantage': 1.0 if a_rest > h_rest else 0.0,
            'home_back_to_back': 1.0 if h_rest <= 1 else 0.0,
            'away_back_to_back': 1.0 if a_rest <= 1 else 0.0,
            'is_playoff': 1.0 if d.month >= 4 else 0.0,
            'home_win_streak': float(self.win_streaks.get(home, 0)),
            'away_win_streak': float(self.win_streaks.get(away, 0)),
            'home_loss_streak': float(self.loss_streaks.get(home, 0)),
            'away_loss_streak': float(self.loss_streaks.get(away, 0)),
            'home_games_last_7_days': float(h_g7),
            'away_games_last_7_days': float(a_g7),
            # Match historical_2024.parquet: 0.5*games_last_7 + 2*b2b
            'home_fatigue_score': h_g7 * 0.5 + (1.0 if h_rest <= 1 else 0.0) * 2.0,
            'away_fatigue_score': a_g7 * 0.5 + (1.0 if a_rest <= 1 else 0.0) * 2.0,
            # Match historical_2024.parquet: cumulative home/away game counts
            'home_game_number': float(h_home_games + 1),
            'away_game_number': float(a_away_games + 1),
            # Match historical_2024.parquet: month-based season phase (0/1/2)
            'home_season_phase': self._season_phase(d),
            'away_season_phase': self._season_phase(d)
        }
        return features

    def update(self, home, away, date, home_win):
        """ Update ratings and streaks after a game is finished. """
        d = pd.to_datetime(date)
        h_elo = self.elo_ratings.get(home, self.default_elo)
        a_elo = self.elo_ratings.get(away, self.default_elo)
        
        # ELO Update
        exp_home = 1 / (1 + 10 ** ((a_elo - h_elo - self.home_advantage) / 400))
        self.elo_ratings[home] = h_elo + self.k * (home_win - exp_home)
        self.elo_ratings[away] = a_elo + self.k * ((1 - home_win) - (1 - exp_home))
        
        # Streak Update
        if home_win == 1:
            self.win_streaks[home] = self.win_streaks.get(home, 0) + 1
            self.loss_streaks[home] = 0
            self.win_streaks[away] = 0
            self.loss_streaks[away] = self.loss_streaks.get(away, 0) + 1
        else:
            self.win_streaks[home] = 0
            self.loss_streaks[home] = self.loss_streaks.get(home, 0) + 1
            self.win_streaks[away] = self.win_streaks.get(away, 0) + 1
            self.loss_streaks[away] = 0
            
        # Last Game & Fatigue
        self.last_game_date[home] = d
        self.last_game_date[away] = d
        
        if home not in self.games_in_last_7: self.games_in_last_7[home] = []
        if away not in self.games_in_last_7: self.games_in_last_7[away] = []
        self.games_in_last_7[home].append(d)
        self.games_in_last_7[away].append(d)
        self.games_in_last_7[home] = self.games_in_last_7[home][-10:]
        self.games_in_last_7[away] = self.games_in_last_7[away][-10:]

        # Update cumulative home/away game counts
        self.home_game_counts[home] = self.home_game_counts.get(home, 0) + 1
        self.away_game_counts[away] = self.away_game_counts.get(away, 0) + 1
