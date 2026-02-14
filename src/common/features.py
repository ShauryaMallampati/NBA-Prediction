import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


def _mov_multiplier(margin: float) -> float:
    """
    Adjust Elo changes based on margin of victory (FiveThirtyEight style).
    
    A 20-point win shouldn't count as twice as important as a 10-point win,
    so we compress the impact of blowouts using logarithms.
    """
    return np.log1p(abs(margin)) * 0.8


def calculate_elo(df: pd.DataFrame, k: int = 20, home_advantage: float = 100) -> pd.DataFrame:
    """Calculate Elo ratings for every team as the season progresses."""
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
    """Add features about how many days of rest each team has."""
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
    """
    Enhanced Running World State — FiveThirtyEight-inspired feature engine.
    
    Maintains comprehensive per-team state for real-time NBA prediction:
    - Standard + MOV-adjusted Elo ratings
    - Rolling win%, scoring, margins, net rating (5/10/20 game windows)
    - Home/Away specific performance splits
    - Pythagorean win expectation
    - Strength of schedule (opponent quality)
    - Momentum & trend indicators
    - Head-to-head tracking
    - Rest, fatigue, streaks
    
    All features are computed from PAST data only (zero leakage).
    """
    
    def __init__(self, default_elo=1500, k=20, home_advantage=100):
        self.default_elo = default_elo
        self.k = k
        self.home_advantage = home_advantage
        
        # === Elo Ratings ===
        self.elo_ratings = {}          # Standard Elo
        self.mov_elo_ratings = {}      # MOV-adjusted Elo (FiveThirtyEight style)
        
        # === Win/Loss tracking ===
        self.win_streaks = {}
        self.loss_streaks = {}
        self.results_history = defaultdict(list)       # [(win, date), ...] all games
        self.home_results_history = defaultdict(list)   # wins/losses in HOME games
        self.away_results_history = defaultdict(list)   # wins/losses in AWAY games
        
        # === Scoring tracking ===
        self.pts_scored_history = defaultdict(list)     # points scored each game
        self.pts_allowed_history = defaultdict(list)    # points allowed each game
        self.margin_history = defaultdict(list)          # margin each game (+/-)
        self.home_pts_scored = defaultdict(list)         # pts scored in home games
        self.away_pts_scored = defaultdict(list)         # pts scored in away games
        
        # === Opponent tracking (for SOS) ===
        self.opponent_elos = defaultdict(list)           # opponent elo at time of game
        self.opponent_win_pcts = defaultdict(list)       # opponent overall win% at time
        
        # === Head-to-head ===
        self.h2h_results = defaultdict(list)  # key: (teamA, teamB) → [(home_team_won, margin, date)]
        
        # === Schedule / Rest ===
        self.last_game_date = {}
        self.games_in_last_7 = defaultdict(list)
        self.home_game_counts = {}
        self.away_game_counts = {}
        
        # === Season tracking ===
        self.season_wins = defaultdict(int)
        self.season_games = defaultdict(int)
        self.current_season_start = None
        
    def _season_key(self, d: pd.Timestamp) -> str:
        """Get NBA season key (e.g., '2024' for 2024-25 season)."""
        if d.month >= 10:
            return str(d.year)
        return str(d.year - 1)
        
    def _season_phase(self, d: pd.Timestamp) -> float:
        """Season phase: 0=Oct/Nov/Dec, 1=Jan/Feb, 2=Mar+"""
        if d.month in [10, 11, 12]:
            return 0.0
        if d.month in [1, 2]:
            return 1.0
        return 2.0
    
    def _safe_mean(self, lst, default=0.5):
        """Safe mean that handles empty lists."""
        return np.mean(lst) if lst else default
    
    def _weighted_mean(self, lst, default=0.5):
        """Exponentially-weighted mean (recent games weighted more)."""
        if not lst:
            return default
        n = len(lst)
        weights = np.exp(np.linspace(-1, 0, n))  # exponential decay
        return np.average(lst, weights=weights)
    
    def _rolling_win_pct(self, team, n):
        """Win% over last n games."""
        hist = self.results_history[team][-n:]
        if not hist:
            return 0.5
        return np.mean([h[0] for h in hist])
    
    def _rolling_pts(self, team, n, which='scored'):
        """Rolling average points scored or allowed."""
        if which == 'scored':
            hist = self.pts_scored_history[team][-n:]
        else:
            hist = self.pts_allowed_history[team][-n:]
        return np.mean(hist) if hist else 100.0
    
    def _rolling_margin(self, team, n):
        """Rolling average margin."""
        hist = self.margin_history[team][-n:]
        return np.mean(hist) if hist else 0.0
    
    def _pythagorean_win_exp(self, team, n=30):
        """
        Pythagorean win expectation: PF^exp / (PF^exp + PA^exp)
        Using exponent of 13.91 (optimal for NBA, from Basketball-Reference).
        """
        pts_for = self.pts_scored_history[team][-n:]
        pts_against = self.pts_allowed_history[team][-n:]
        if not pts_for or not pts_against:
            return 0.5
        pf = np.mean(pts_for)
        pa = np.mean(pts_against)
        exp = 13.91  # NBA-specific exponent
        if pa == 0:
            return 0.95
        return pf**exp / (pf**exp + pa**exp)
    
    def _strength_of_schedule(self, team, n=10):
        """Average opponent Elo over last n games."""
        opp_elos = self.opponent_elos[team][-n:]
        return np.mean(opp_elos) if opp_elos else self.default_elo
    
    def _opp_win_pct(self, team, n=10):
        """Average opponent win% over last n games."""
        opp_wpcts = self.opponent_win_pcts[team][-n:]
        return np.mean(opp_wpcts) if opp_wpcts else 0.5
    
    def _h2h_stats(self, home, away, max_games=10):
        """Head-to-head stats between two teams."""
        # Check both directions
        key1 = (home, away)
        key2 = (away, home)
        results = self.h2h_results[key1] + self.h2h_results[key2]
        results = results[-max_games:]  # last N meetings
        
        if not results:
            return 0, 0.5, 0.0  # games, win_pct, avg_margin
        
        home_wins = sum(1 for r in results if 
                       (r[0] == home and r[1] > 0) or (r[0] == away and r[1] < 0))
        total = len(results)
        home_win_pct = home_wins / total
        
        # Average margin from home team's perspective
        margins = []
        for r in results:
            if r[0] == home:
                margins.append(r[1])  # home was home in this game
            else:
                margins.append(-r[1])  # home was away in this game
        avg_margin = np.mean(margins) if margins else 0.0
        
        return total, home_win_pct, avg_margin

    def get_team_features(self, home, away, date) -> Dict:
        """
        Generate comprehensive pre-game features for a matchup.
        ~55 features computed from past data only.
        """
        d = pd.to_datetime(date)
        
        # === ELO FEATURES (6) ===
        h_elo = self.elo_ratings.get(home, self.default_elo)
        a_elo = self.elo_ratings.get(away, self.default_elo)
        h_mov_elo = self.mov_elo_ratings.get(home, self.default_elo)
        a_mov_elo = self.mov_elo_ratings.get(away, self.default_elo)
        
        elo_diff = h_elo - a_elo + self.home_advantage
        elo_win_prob = 1 / (1 + 10 ** ((a_elo - h_elo - self.home_advantage) / 400))
        mov_elo_diff = h_mov_elo - a_mov_elo + self.home_advantage
        mov_elo_win_prob = 1 / (1 + 10 ** ((a_mov_elo - h_mov_elo - self.home_advantage) / 400))
        
        # === ROLLING WIN% (8) ===
        h_wp5 = self._rolling_win_pct(home, 5)
        h_wp10 = self._rolling_win_pct(home, 10)
        h_wp20 = self._rolling_win_pct(home, 20)
        a_wp5 = self._rolling_win_pct(away, 5)
        a_wp10 = self._rolling_win_pct(away, 10)
        a_wp20 = self._rolling_win_pct(away, 20)
        
        # Home/away specific win%
        h_home_hist = self.home_results_history[home][-10:]
        a_away_hist = self.away_results_history[away][-10:]
        h_home_wp = np.mean(h_home_hist) if h_home_hist else 0.55  # home teams ~55%
        a_away_wp = np.mean(a_away_hist) if a_away_hist else 0.45
        
        # === ROLLING SCORING (10) ===
        h_pts5 = self._rolling_pts(home, 5, 'scored')
        h_pts10 = self._rolling_pts(home, 10, 'scored')
        a_pts5 = self._rolling_pts(away, 5, 'scored')
        a_pts10 = self._rolling_pts(away, 10, 'scored')
        
        h_pts_allowed10 = self._rolling_pts(home, 10, 'allowed')
        a_pts_allowed10 = self._rolling_pts(away, 10, 'allowed')
        
        h_net_rating = h_pts10 - h_pts_allowed10
        a_net_rating = a_pts10 - a_pts_allowed10
        
        h_margin5 = self._rolling_margin(home, 5)
        h_margin10 = self._rolling_margin(home, 10)
        a_margin5 = self._rolling_margin(away, 5)
        a_margin10 = self._rolling_margin(away, 10)
        
        # === PYTHAGOREAN (2) ===
        h_pyth = self._pythagorean_win_exp(home, 30)
        a_pyth = self._pythagorean_win_exp(away, 30)
        
        # === STRENGTH OF SCHEDULE (4) ===
        h_sos = self._strength_of_schedule(home, 10)
        a_sos = self._strength_of_schedule(away, 10)
        h_opp_wp = self._opp_win_pct(home, 10)
        a_opp_wp = self._opp_win_pct(away, 10)
        
        # === MOMENTUM / TRENDS (4) ===
        h_momentum = h_wp5 - h_wp20  # positive = improving
        a_momentum = a_wp5 - a_wp20
        h_scoring_trend = self._rolling_pts(home, 5, 'scored') - self._rolling_pts(home, 20, 'scored')
        a_scoring_trend = self._rolling_pts(away, 5, 'scored') - self._rolling_pts(away, 20, 'scored')
        
        # Weighted recent form (exponential decay)
        h_weighted_form = self._weighted_mean(
            [r[0] for r in self.results_history[home][-10:]], 0.5)
        a_weighted_form = self._weighted_mean(
            [r[0] for r in self.results_history[away][-10:]], 0.5)
        
        # === REST / FATIGUE (7) ===
        h_rest = (d - self.last_game_date.get(home, d - pd.Timedelta(days=3))).days
        a_rest = (d - self.last_game_date.get(away, d - pd.Timedelta(days=3))).days
        h_rest = min(h_rest, 7)
        a_rest = min(a_rest, 7)
        
        cutoff = d - pd.Timedelta(days=7)
        h_g7 = len([dt for dt in self.games_in_last_7.get(home, []) if dt > cutoff])
        a_g7 = len([dt for dt in self.games_in_last_7.get(away, []) if dt > cutoff])
        
        # === STREAKS (4) ===
        h_win_streak = float(self.win_streaks.get(home, 0))
        a_win_streak = float(self.win_streaks.get(away, 0))
        h_loss_streak = float(self.loss_streaks.get(home, 0))
        a_loss_streak = float(self.loss_streaks.get(away, 0))
        
        # === HEAD-TO-HEAD (3) ===
        h2h_games, h2h_home_wp, h2h_margin = self._h2h_stats(home, away, 10)
        
        # === CONTEXT (4) ===
        h_home_games = self.home_game_counts.get(home, 0)
        a_away_games = self.away_game_counts.get(away, 0)
        season_phase = self._season_phase(d)
        is_playoff = 1.0 if d.month in [4, 5, 6] and d.day >= 10 else 0.0
        day_of_week = float(d.dayofweek)
        
        # === DIFFERENTIALS (critical for model — direct comparison features) ===
        features = {
            # Elo (6)
            'elo_home': h_elo,
            'elo_away': a_elo,
            'elo_diff': elo_diff,
            'elo_win_prob': elo_win_prob,
            'mov_elo_diff': mov_elo_diff,
            'mov_elo_win_prob': mov_elo_win_prob,
            
            # Rolling win% (8)
            'home_win_pct_l5': h_wp5,
            'home_win_pct_l10': h_wp10,
            'home_win_pct_l20': h_wp20,
            'away_win_pct_l5': a_wp5,
            'away_win_pct_l10': a_wp10,
            'away_win_pct_l20': a_wp20,
            'home_home_win_pct': h_home_wp,
            'away_away_win_pct': a_away_wp,
            
            # Rolling scoring (12)
            'home_pts_avg_l5': h_pts5,
            'home_pts_avg_l10': h_pts10,
            'away_pts_avg_l5': a_pts5,
            'away_pts_avg_l10': a_pts10,
            'home_pts_allowed_l10': h_pts_allowed10,
            'away_pts_allowed_l10': a_pts_allowed10,
            'home_net_rating': h_net_rating,
            'away_net_rating': a_net_rating,
            'home_margin_avg_l5': h_margin5,
            'home_margin_avg_l10': h_margin10,
            'away_margin_avg_l5': a_margin5,
            'away_margin_avg_l10': a_margin10,
            
            # Pythagorean (2)
            'home_pythagorean': h_pyth,
            'away_pythagorean': a_pyth,
            
            # SOS (4)
            'home_sos_l10': h_sos,
            'away_sos_l10': a_sos,
            'home_opp_win_pct_l10': h_opp_wp,
            'away_opp_win_pct_l10': a_opp_wp,
            
            # Momentum (6)
            'home_momentum': h_momentum,
            'away_momentum': a_momentum,
            'home_scoring_trend': h_scoring_trend,
            'away_scoring_trend': a_scoring_trend,
            'home_weighted_form': h_weighted_form,
            'away_weighted_form': a_weighted_form,
            
            # Rest/Fatigue (7)
            'home_rest_days': float(h_rest),
            'away_rest_days': float(a_rest),
            'rest_differential': float(h_rest - a_rest),
            'home_back_to_back': 1.0 if h_rest <= 1 else 0.0,
            'away_back_to_back': 1.0 if a_rest <= 1 else 0.0,
            'home_games_last_7_days': float(h_g7),
            'away_games_last_7_days': float(a_g7),
            
            # Streaks (4)
            'home_win_streak': h_win_streak,
            'away_win_streak': a_win_streak,
            'home_loss_streak': h_loss_streak,
            'away_loss_streak': a_loss_streak,
            
            # H2H (3)
            'h2h_games': float(h2h_games),
            'h2h_home_win_pct': h2h_home_wp,
            'h2h_avg_margin': h2h_margin,
            
            # Context (5)
            'home_game_number': float(h_home_games + 1),
            'away_game_number': float(a_away_games + 1),
            'season_phase': season_phase,
            'is_playoff': is_playoff,
            'day_of_week': day_of_week,
            
            # Key differentials (10)
            'win_pct_diff_l5': h_wp5 - a_wp5,
            'win_pct_diff_l10': h_wp10 - a_wp10,
            'win_pct_diff_l20': h_wp20 - a_wp20,
            'pts_avg_diff': h_pts10 - a_pts10,
            'net_rating_diff': h_net_rating - a_net_rating,
            'margin_diff': h_margin10 - a_margin10,
            'pythagorean_diff': h_pyth - a_pyth,
            'sos_diff': h_sos - a_sos,
            'momentum_diff': h_momentum - a_momentum,
            'weighted_form_diff': h_weighted_form - a_weighted_form,
            
            # Legacy compatibility
            'home_adv_flag': 1.0,
            'home_court_adv': 100.0,
            'elo_p_home': h_elo / (h_elo + a_elo) if (h_elo + a_elo) > 0 else 0.5,
            'home_rest_advantage': 1.0 if h_rest > a_rest else 0.0,
            'away_rest_advantage': 1.0 if a_rest > h_rest else 0.0,
            'home_injury_count': 0.0,
            'away_injury_count': 0.0,
            'home_key_player_injured': 0.0,
            'away_key_player_injured': 0.0,
            'home_fatigue_score': h_g7 * 0.5 + (1.0 if h_rest <= 1 else 0.0) * 2.0,
            'away_fatigue_score': a_g7 * 0.5 + (1.0 if a_rest <= 1 else 0.0) * 2.0,
            'home_season_phase': season_phase,
            'away_season_phase': season_phase,
        }
        return features

    def update(self, home, away, date, home_win, home_pts=None, away_pts=None):
        """
        Update all state after a game is finished.
        
        Args:
            home: Home team name
            away: Away team name
            date: Game date
            home_win: 1 if home won, 0 if away won
            home_pts: Home team points (optional, enables scoring features)
            away_pts: Away team points (optional, enables scoring features)
        """
        d = pd.to_datetime(date)
        h_elo = self.elo_ratings.get(home, self.default_elo)
        a_elo = self.elo_ratings.get(away, self.default_elo)
        h_mov_elo = self.mov_elo_ratings.get(home, self.default_elo)
        a_mov_elo = self.mov_elo_ratings.get(away, self.default_elo)
        
        # === Standard Elo Update ===
        exp_home = 1 / (1 + 10 ** ((a_elo - h_elo - self.home_advantage) / 400))
        self.elo_ratings[home] = h_elo + self.k * (home_win - exp_home)
        self.elo_ratings[away] = a_elo + self.k * ((1 - home_win) - (1 - exp_home))

        # === MOV Elo Update (FiveThirtyEight style) ===
        margin = 0.0
        if home_pts is not None and away_pts is not None:
            margin = float(home_pts - away_pts)
            mov_k = self.k * _mov_multiplier(margin)
        else:
            mov_k = self.k
        
        exp_home_mov = 1 / (1 + 10 ** ((a_mov_elo - h_mov_elo - self.home_advantage) / 400))
        self.mov_elo_ratings[home] = h_mov_elo + mov_k * (home_win - exp_home_mov)
        self.mov_elo_ratings[away] = a_mov_elo + mov_k * ((1 - home_win) - (1 - exp_home_mov))
        
        # === Win/Loss Results ===
        self.results_history[home].append((home_win, d))
        self.results_history[away].append((1 - home_win, d))
        self.home_results_history[home].append(home_win)
        self.away_results_history[away].append(1 - home_win)
        
        # Keep history manageable (last 100 games per team)
        for team in [home, away]:
            if len(self.results_history[team]) > 100:
                self.results_history[team] = self.results_history[team][-100:]
            if len(self.home_results_history[team]) > 50:
                self.home_results_history[team] = self.home_results_history[team][-50:]
            if len(self.away_results_history[team]) > 50:
                self.away_results_history[team] = self.away_results_history[team][-50:]
        
        # === Scoring ===
        if home_pts is not None and away_pts is not None:
            self.pts_scored_history[home].append(float(home_pts))
            self.pts_scored_history[away].append(float(away_pts))
            self.pts_allowed_history[home].append(float(away_pts))
            self.pts_allowed_history[away].append(float(home_pts))
            self.margin_history[home].append(margin)
            self.margin_history[away].append(-margin)
            self.home_pts_scored[home].append(float(home_pts))
            self.away_pts_scored[away].append(float(away_pts))
            
            # Keep manageable
            for team in [home, away]:
                for hist in [self.pts_scored_history, self.pts_allowed_history, 
                           self.margin_history]:
                    if len(hist[team]) > 100:
                        hist[team] = hist[team][-100:]
        
        # === Opponent tracking (for SOS) ===
        # Record opponent's elo at time of game
        self.opponent_elos[home].append(a_elo)
        self.opponent_elos[away].append(h_elo)
        
        # Record opponent's win% at time of game
        a_games = self.results_history[away]
        h_games = self.results_history[home]
        a_wp = np.mean([r[0] for r in a_games[-20:]]) if a_games else 0.5
        h_wp = np.mean([r[0] for r in h_games[-20:]]) if h_games else 0.5
        self.opponent_win_pcts[home].append(a_wp)
        self.opponent_win_pcts[away].append(h_wp)
        
        for team in [home, away]:
            if len(self.opponent_elos[team]) > 50:
                self.opponent_elos[team] = self.opponent_elos[team][-50:]
            if len(self.opponent_win_pcts[team]) > 50:
                self.opponent_win_pcts[team] = self.opponent_win_pcts[team][-50:]
        
        # === Head-to-head ===
        # Store: (home_team_in_this_game, margin, date)
        self.h2h_results[(home, away)].append((home, margin, d))
        if len(self.h2h_results[(home, away)]) > 20:
            self.h2h_results[(home, away)] = self.h2h_results[(home, away)][-20:]
        
        # === Streaks ===
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
            
        # === Schedule / Rest ===
        self.last_game_date[home] = d
        self.last_game_date[away] = d
        
        self.games_in_last_7[home].append(d)
        self.games_in_last_7[away].append(d)
        self.games_in_last_7[home] = self.games_in_last_7[home][-10:]
        self.games_in_last_7[away] = self.games_in_last_7[away][-10:]

        # === Game counts ===
        self.home_game_counts[home] = self.home_game_counts.get(home, 0) + 1
        self.away_game_counts[away] = self.away_game_counts.get(away, 0) + 1
        
        # === Season tracking ===
        season = self._season_key(d)
        self.season_wins[(home, season)] = self.season_wins.get((home, season), 0) + home_win
        self.season_wins[(away, season)] = self.season_wins.get((away, season), 0) + (1 - home_win)
        self.season_games[(home, season)] = self.season_games.get((home, season), 0) + 1
        self.season_games[(away, season)] = self.season_games.get((away, season), 0) + 1
