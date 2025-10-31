#!/usr/bin/env python3
"""
Feature Engineering Pipeline for NBA Prediction Models

Transforms raw game data into ML features:
- Elo ratings
- Recent form (win/loss streaks, last N games)
- Head-to-head records
- Home/away splits
- Rest days and back-to-backs
- Season trends
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from collections import defaultdict

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


class EloRatingSystem:
    """Elo rating system for NBA teams"""
    
    def __init__(self, k_factor: float = 20.0, initial_rating: float = 1500.0):
        """
        Initialize Elo rating system
        
        Args:
            k_factor: K-factor (how much ratings change per game)
            initial_rating: Starting rating for all teams
        """
        self.k_factor = k_factor
        self.initial_rating = initial_rating
        self.ratings = defaultdict(lambda: initial_rating)
        self.rating_history = defaultdict(list)
    
    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Calculate expected score (win probability) for team A
        
        Args:
            rating_a: Elo rating of team A
            rating_b: Elo rating of team B
        
        Returns:
            Expected score (0-1)
        """
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))
    
    def update_ratings(self, team_a: str, team_b: str, score_a: int, 
                       score_b: int, is_home: bool = True, date: str = None):
        """
        Update Elo ratings after a game
        
        Args:
            team_a: Team A identifier
            team_b: Team B identifier
            score_a: Team A final score
            score_b: Team B final score
            is_home: Whether team A is home team
            date: Game date
        """
        rating_a = self.ratings[team_a]
        rating_b = self.ratings[team_b]
        
        # Expected scores
        expected_a = self.expected_score(rating_a, rating_b)
        expected_b = 1.0 - expected_a
        
        # Actual scores (1 for win, 0.5 for tie, 0 for loss)
        actual_a = 1.0 if score_a > score_b else (0.5 if score_a == score_b else 0.0)
        actual_b = 1.0 - actual_a
        
        # Home court advantage adjustment (roughly 100 rating points = 64% win prob)
        home_advantage = 100 if is_home else -100
        
        # Update ratings
        self.ratings[team_a] += self.k_factor * (actual_a - expected_a)
        self.ratings[team_b] += self.k_factor * (actual_b - expected_b)
        
        # Store history
        if date:
            self.rating_history[team_a].append({
                'date': date,
                'rating': self.ratings[team_a],
                'opponent': team_b,
                'result': actual_a
            })
            self.rating_history[team_b].append({
                'date': date,
                'rating': self.ratings[team_b],
                'opponent': team_a,
                'result': actual_b
            })
    
    def get_rating(self, team: str) -> float:
        """Get current Elo rating for a team"""
        return self.ratings[team]
    
    def get_win_probability(self, team_a: str, team_b: str, 
                           is_home: bool = True) -> float:
        """
        Get win probability for team A vs team B
        
        Args:
            team_a: Team A identifier
            team_b: Team B identifier
            is_home: Whether team A is home team
        
        Returns:
            Win probability (0-1)
        """
        rating_a = self.ratings[team_a]
        rating_b = self.ratings[team_b]
        
        # Adjust for home court advantage
        if is_home:
            rating_a += 100
        
        return self.expected_score(rating_a, rating_b)


class FeatureEngineer:
    """Feature engineering for NBA prediction models"""
    
    def __init__(self, elo_k_factor: float = 20.0):
        """Initialize feature engineer"""
        self.elo = EloRatingSystem(k_factor=elo_k_factor)
        self.team_records = defaultdict(lambda: {'wins': 0, 'losses': 0, 'games': []})
        self.h2h_records = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'losses': 0}))
    
    def _get_team_name(self, game: Dict, key: str) -> str:
        """Extract team name from game dict (handles both nested and flat formats)"""
        if isinstance(game.get(key), dict):
            return game.get(key, {}).get('abbreviation', '')
        return game.get(key, '')
    
    def _get_score(self, game: Dict, key: str) -> int:
        """Extract score from game dict (handles both nested and flat formats)"""
        if isinstance(game.get(key), dict):
            return game.get(key, {}).get('score', 0)
        return game.get(f"{key}_score", 0)
    
    def load_games(self, games_file: Path) -> List[Dict]:
        """
        Load games from CSV or JSON file
        
        Args:
            games_file: Path to games CSV or JSON file
        
        Returns:
            List of game dictionaries
        """
        if games_file.suffix == '.csv':
            # Load CSV file
            df = pd.read_csv(games_file, low_memory=False)
            df['date'] = pd.to_datetime(df['date'], format='mixed', errors='coerce')
            
            # Drop rows with missing critical data
            df = df.dropna(subset=['date'])
            
            # Check if we have NBA API format (with MATCHUP column)
            if 'MATCHUP' in df.columns:
                # NBA API format - has home/away in MATCHUP
                games = []
                for _, row in df.iterrows():
                    if pd.isna(row.get('MATCHUP')) or pd.isna(row.get('PTS')):
                        continue
                    
                    matchup = str(row['MATCHUP'])
                    team = str(row.get('TEAM_ABBREVIATION', row.get('team', '')))
                    
                    # Parse matchup to determine home/away
                    if ' vs. ' in matchup:
                        # Home game
                        home_team = team
                        away_team = matchup.split(' vs. ')[1] if len(matchup.split(' vs. ')) > 1 else 'Unknown'
                    elif ' @ ' in matchup:
                        # Away game - skip for now, we'll get it from home game
                        continue
                    else:
                        continue
                    
                    game = {
                        'date': row['date'].isoformat() if pd.notna(row['date']) else None,
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_score': int(float(row['PTS'])),
                        'away_score': 0,  # Will be filled from matching away game
                        'season': str(row.get('SEASON_ID', row.get('season', '')))
                    }
                    
                    if game['date'] is not None:
                        games.append(game)
                
                print(f"  📊 Loaded {len(games)} games from NBA API format")
            else:
                # Archive 3 format - just team stats, need to pair them
                # Group by date to find matchups
                games = []
                grouped = df.groupby('date')
                
                for date, group in grouped:
                    teams = group[group['team'].notna()]
                    if len(teams) >= 2:
                        # Take first two teams as a matchup
                        teams_list = teams.to_dict('records')
                        for i in range(0, len(teams_list)-1, 2):
                            team1 = teams_list[i]
                            team2 = teams_list[i+1] if i+1 < len(teams_list) else None
                            
                            if team2 is None:
                                continue
                            
                            pts1 = team1.get('pts', team1.get('PTS', 0))
                            pts2 = team2.get('pts', team2.get('PTS', 0))
                            
                            if pd.isna(pts1) or pd.isna(pts2):
                                continue
                            
                            game = {
                                'date': date.isoformat() if pd.notna(date) else None,
                                'home_team': str(team1.get('team', 'Unknown')),
                                'away_team': str(team2.get('team', 'Unknown')),
                                'home_score': int(float(pts1)),
                                'away_score': int(float(pts2)),
                                'season': str(team1.get('season', ''))
                            }
                            
                            if game['date'] is not None:
                                games.append(game)
                
                print(f"  📊 Loaded {len(games)} games from Archive 3 format")
            
            return games
        else:
            # Load JSON file (legacy format)
            with open(games_file, 'r') as f:
                data = json.load(f)
            
            return data.get('games', [])
    
    def engineer_game_features(self, game: Dict, previous_games: List[Dict]) -> Dict:
        """
        Engineer features for a single game
        
        Args:
            game: Game dictionary
            previous_games: List of games that happened before this one
        
        Returns:
            Dictionary of engineered features
        """
        # Extract team names using helper
        home_team = self._get_team_name(game, 'home_team')
        away_team = self._get_team_name(game, 'away_team') or self._get_team_name(game, 'visitor_team')
        game_date = game.get('date')
        
        if not home_team or not away_team:
            return {}
        
        features = {
            'game_id': game.get('game_id', f"{game_date}_{home_team}_{away_team}"),
            'date': game_date,
            'home_team': home_team,
            'away_team': away_team,
        }
        
        # Elo ratings
        features['home_elo'] = self.elo.get_rating(home_team)
        features['away_elo'] = self.elo.get_rating(away_team)
        features['elo_diff'] = features['home_elo'] - features['away_elo']
        features['elo_win_prob'] = self.elo.get_win_probability(home_team, away_team, is_home=True)
        
        # Recent form (last 5 and 10 games)
        home_last_5 = self._get_recent_record(home_team, previous_games, n=5)
        away_last_5 = self._get_recent_record(away_team, previous_games, n=5)
        home_last_10 = self._get_recent_record(home_team, previous_games, n=10)
        away_last_10 = self._get_recent_record(away_team, previous_games, n=10)
        
        features['home_last_5_wins'] = home_last_5['wins']
        features['home_last_5_win_pct'] = home_last_5['win_pct']
        features['away_last_5_wins'] = away_last_5['wins']
        features['away_last_5_win_pct'] = away_last_5['win_pct']
        
        features['home_last_10_wins'] = home_last_10['wins']
        features['home_last_10_win_pct'] = home_last_10['win_pct']
        features['away_last_10_wins'] = away_last_10['wins']
        features['away_last_10_win_pct'] = away_last_10['win_pct']
        
        # Head-to-head record
        h2h = self.h2h_records[home_team][away_team]
        features['h2h_home_wins'] = h2h['wins']
        features['h2h_away_wins'] = h2h['losses']  # From home team perspective
        
        # Rest days
        features['home_rest_days'] = self._get_rest_days(home_team, game_date, previous_games)
        features['away_rest_days'] = self._get_rest_days(away_team, game_date, previous_games)
        
        # Back-to-back detection
        features['home_back_to_back'] = 1 if features['home_rest_days'] == 0 else 0
        features['away_back_to_back'] = 1 if features['away_rest_days'] == 0 else 0
        
        # Home/away splits
        home_home_record = self._get_home_away_record(home_team, previous_games, is_home=True)
        away_away_record = self._get_home_away_record(away_team, previous_games, is_home=False)
        
        features['home_home_win_pct'] = home_home_record['win_pct']
        features['away_away_win_pct'] = away_away_record['win_pct']
        
        # Actual result (if available)
        if game.get('status', '').lower().find('final') >= 0 or 'home_score' in game:
            home_score = self._get_score(game, 'home_team')
            away_score = self._get_score(game, 'away_team') or self._get_score(game, 'visitor_team')
            
            if home_score is not None and away_score is not None and home_score != 0:
                features['home_score'] = home_score
                features['away_score'] = away_score
                features['home_win'] = 1 if home_score > away_score else 0
                features['score_diff'] = home_score - away_score
        
        return features
    
    def _get_recent_record(self, team: str, games: List[Dict], n: int = 5) -> Dict:
        """Get recent win/loss record for team"""
        team_games = [
            g for g in games
            if (self._get_team_name(g, 'home_team') == team or
                self._get_team_name(g, 'away_team') == team or
                self._get_team_name(g, 'visitor_team') == team)
        ]
        
        # Take last N games
        recent_games = team_games[-n:] if len(team_games) > n else team_games
        
        wins = 0
        for game in recent_games:
            is_home = self._get_team_name(game, 'home_team') == team
            home_score = self._get_score(game, 'home_team')
            away_score = self._get_score(game, 'away_team') or self._get_score(game, 'visitor_team')
            
            if (game.get('status', '').lower().find('final') >= 0 or 'home_score' in game) and home_score != 0:
                if is_home and home_score > away_score:
                    wins += 1
                elif not is_home and away_score > home_score:
                    wins += 1
        
        games_played = len(recent_games)
        win_pct = wins / games_played if games_played > 0 else 0.0
        
        return {
            'wins': wins,
            'losses': games_played - wins,
            'games_played': games_played,
            'win_pct': win_pct
        }
    
    def _get_rest_days(self, team: str, game_date: str, games: List[Dict]) -> int:
        """Calculate days of rest since last game"""
        team_games = [
            g for g in games
            if (self._get_team_name(g, 'home_team') == team or
                self._get_team_name(g, 'away_team') == team or
                self._get_team_name(g, 'visitor_team') == team) and
               g.get('date', '') < game_date
        ]
        
        if not team_games:
            return 7  # Default to 7 if no previous games
        
        last_game = team_games[-1]
        last_date = datetime.fromisoformat(last_game.get('date', game_date))
        current_date = datetime.fromisoformat(game_date)
        
        return (current_date - last_date).days - 1  # Subtract 1 to get rest days
    
    def _get_home_away_record(self, team: str, games: List[Dict], is_home: bool) -> Dict:
        """Get home or away record for team"""
        if is_home:
            team_games = [
                g for g in games
                if self._get_team_name(g, 'home_team') == team
            ]
        else:
            team_games = [
                g for g in games
                if (self._get_team_name(g, 'away_team') == team or
                    self._get_team_name(g, 'visitor_team') == team)
            ]
        
        wins = 0
        for game in team_games:
            if game.get('status', '').lower().find('final') >= 0 or 'home_score' in game:
                home_score = self._get_score(game, 'home_team')
                away_score = self._get_score(game, 'away_team') or self._get_score(game, 'visitor_team')
                
                if home_score != 0 and away_score is not None:
                    if is_home and home_score > away_score:
                        wins += 1
                    elif not is_home and away_score > home_score:
                        wins += 1
        
        games_played = len(team_games)
        win_pct = wins / games_played if games_played > 0 else 0.5
        
        return {
            'wins': wins,
            'losses': games_played - wins,
            'games_played': games_played,
            'win_pct': win_pct
        }
    
    def process_season(self, games: List[Dict]) -> pd.DataFrame:
        """
        Process all games in a season and engineer features
        
        Args:
            games: List of game dictionaries
        
        Returns:
            DataFrame with engineered features
        """
        print(f"Processing {len(games)} games...")
        
        # Sort games by date
        games = sorted(games, key=lambda g: g.get('date', ''))
        
        all_features = []
        
        for i, game in enumerate(games):
            if i % 100 == 0:
                print(f"  Processed {i}/{len(games)} games...")
            
            # Get all previous games for context
            previous_games = games[:i]
            
            # Engineer features
            features = self.engineer_game_features(game, previous_games)
            
            if features:
                all_features.append(features)
            
            # Update Elo ratings if game is final
            if game.get('status', '').lower().find('final') >= 0 or 'home_score' in game:
                home_team = self._get_team_name(game, 'home_team')
                away_team = self._get_team_name(game, 'away_team') or self._get_team_name(game, 'visitor_team')
                home_score = self._get_score(game, 'home_team')
                away_score = self._get_score(game, 'away_team') or self._get_score(game, 'visitor_team')
                
                if home_team and away_team and home_score != 0:
                    self.elo.update_ratings(
                        team_a=home_team,
                        team_b=away_team,
                        score_a=home_score,
                        score_b=away_score,
                        is_home=True,
                        date=game.get('date')
                    )
                    
                    # Update head-to-head
                    if home_score > away_score:
                        self.h2h_records[home_team][away_team]['wins'] += 1
                        self.h2h_records[away_team][home_team]['losses'] += 1
                    else:
                        self.h2h_records[away_team][home_team]['wins'] += 1
                        self.h2h_records[home_team][away_team]['losses'] += 1
        
        print(f"  ✅ Processed {len(all_features)} games with features")
        
        return pd.DataFrame(all_features)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Engineer features from NBA game data')
    parser.add_argument('--input', type=str, default='data/processed/all_games_historical.csv',
                       help='Input games CSV or JSON file')
    parser.add_argument('--output', type=str, default='data/processed/engineered_features.csv',
                       help='Output features CSV file')
    parser.add_argument('--elo-k', type=float, default=20.0,
                       help='Elo K-factor')
    
    args = parser.parse_args()
    
    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize feature engineer
    engineer = FeatureEngineer(elo_k_factor=args.elo_k)
    
    # Load games
    print(f"\n📂 Loading games from {args.input}...")
    games = engineer.load_games(Path(args.input))
    print(f"  ✅ Loaded {len(games)} games")
    
    # Process season
    print(f"\n⚙️  Engineering features...")
    features_df = engineer.process_season(games)
    
    # Save features
    print(f"\n💾 Saving features to {args.output}...")
    features_df.to_csv(output_path, index=False)
    print(f"  ✅ Saved {len(features_df)} rows with {len(features_df.columns)} features")
    
    # Print sample
    print(f"\n📊 Sample features:")
    print(features_df.head(10).to_string())
    
    print(f"\n✅ Feature engineering complete!")


if __name__ == "__main__":
    main()
