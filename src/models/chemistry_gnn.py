"""
Graph Neural Network for Player Chemistry

A simple GCN-inspired model that learns player synergy patterns.
Uses PyTorch (no need for torch_geometric for this simple version).
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = Path("data/chemistry")
MODEL_DIR = Path("artifacts/models/chemistry")


class PlayerChemistryModel:
    """
    Simple chemistry scoring model based on player pair net ratings.
    
    This is a "pseudo-GNN" that captures the essence of graph-based
    chemistry modeling without requiring PyTorch Geometric.
    """
    
    def __init__(self):
        self.team_chemistry: Dict[str, float] = {}
        self.top_duos: List[Dict] = []
        self.player_pairs: Dict[str, Dict] = {}
        self.loaded = False
        # Optional pre-indexed games for fast progressive chemistry lookups
        self._games_df_id = None
        self._team_games_index = {}
        self._team_games_dates = {}

    def set_games_df(self, games_df) -> None:
        """Pre-index games by team for fast chemistry lookups."""
        if games_df is None:
            return
        try:
            df = games_df.copy()
            df['date'] = pd.to_datetime(df['date'])
            self._games_df_id = id(games_df)
            self._team_games_index = {}
            self._team_games_dates = {}
            teams = pd.concat([df['home'], df['away']]).unique()
            df = df.sort_values('date')
            for team in teams:
                team_games = df[(df['home'] == team) | (df['away'] == team)].sort_values('date')
                self._team_games_index[team] = team_games
            self._team_games_dates[team] = team_games['date'].to_numpy(dtype='datetime64[ns]')
        except Exception as e:
            logger.warning(f"Failed to build chemistry game index: {e}")
    
    async def load_async(self) -> bool:
        """Async version of chemistry data loading."""
        import asyncio
        scores_file = DATA_DIR / "chemistry_scores.json"
        pairs_file = DATA_DIR / "player_pairs.json"
        
        if not scores_file.exists() or not pairs_file.exists():
            return False
            
        async def read_json(path):
            with open(path, 'r') as f:
                return json.load(f)
                
        scores_data = await asyncio.to_thread(read_json, scores_file)
        pairs_data = await asyncio.to_thread(read_json, pairs_file)
        
        self.team_chemistry = scores_data.get('team_chemistry', {})
        self.top_duos = scores_data.get('top_duos', [])
        self.player_pairs = pairs_data.get('pairs', {})
        
        self.loaded = True
        return True

    def load(self) -> bool:
        """Load chemistry data from scraped files (sync version)."""
        scores_file = DATA_DIR / "chemistry_scores.json"
        pairs_file = DATA_DIR / "player_pairs.json"
        
        if not scores_file.exists() or not pairs_file.exists():
            logger.warning("Chemistry data not found. Run fetch_lineup_data.py first.")
            return False
        
        with open(scores_file, 'r') as f:
            scores_data = json.load(f)
        
        with open(pairs_file, 'r') as f:
            pairs_data = json.load(f)
        
        self.team_chemistry = scores_data.get('team_chemistry', {})
        self.top_duos = scores_data.get('top_duos', [])
        self.player_pairs = pairs_data.get('pairs', {})
        
        self.loaded = True
        logger.info(f"✅ Loaded chemistry model: {len(self.team_chemistry)} teams, {len(self.player_pairs)} pairs")
        return True
    
    def get_team_chemistry_score(self, team_abbr: str, current_date: str = None, games_df = None) -> float:
        """
        Get chemistry score for a team (0-1 scale).
        
        If current_date and games_df are provided, calculates a PROGRESSIVE chemistry
        score based on team's recent performance consistency (proxy for chemistry).
        
        Args:
            team_abbr: Team name/abbreviation
            current_date: Date string for pregame-only calculation
            games_df: DataFrame with game history
        """
        import pandas as pd
        import numpy as np
        
        # If we have date context, calculate progressive chemistry
        if current_date is not None and games_df is not None:
            try:
                target_date = pd.to_datetime(current_date)

                # Build or refresh index if needed
                if self._games_df_id != id(games_df):
                    self.set_games_df(games_df)

                # Get team's past games in this season (after Oct 1 of that year)
                season_start = np.datetime64(f"{target_date.year if target_date.month >= 10 else target_date.year - 1}-10-01")
                target_dt = np.datetime64(target_date)

                if team_abbr in self._team_games_index:
                    team_games = self._team_games_index[team_abbr]
                    team_dates = self._team_games_dates[team_abbr]
                    start_idx = np.searchsorted(team_dates, season_start, side='left')
                    end_idx = np.searchsorted(team_dates, target_dt, side='left')
                    team_games = team_games.iloc[start_idx:end_idx].tail(10)
                else:
                    team_games = games_df[
                        ((games_df['home'] == team_abbr) | (games_df['away'] == team_abbr)) &
                        (games_df['date'] >= season_start) &
                        (games_df['date'] < target_date)
                    ].sort_values('date', ascending=False).head(10)
                
                if len(team_games) < 1:
                    # No games yet - return neutral
                    return 0.5
                
                # Calculate chemistry proxy: consistency + recent form
                margins = []
                for _, game in team_games.iterrows():
                    if game['home'] == team_abbr:
                        margins.append(game['margin'])
                    else:
                        margins.append(-game['margin'])
                
                # Chemistry = combination of:
                # 1. Consistency (low variance = good chemistry)
                # 2. Recent form (positive margins = good)
                variance = np.std(margins)
                mean_margin = np.mean(margins)
                
                # Normalize: lower variance = higher chemistry (0.3-0.7 range)
                consistency_score = 1 - min(variance / 20, 1)  # 20 point variance = 0
                form_score = np.clip((mean_margin + 10) / 20, 0, 1)  # -10 to +10 margin
                
                # Combine: 60% consistency, 40% form
                chemistry = 0.3 + (0.6 * consistency_score + 0.4 * form_score) * 0.4
                
                logger.debug(f"Chemistry for {team_abbr}: var={variance:.1f}, margin={mean_margin:.1f} -> {chemistry:.3f}")
                return chemistry
                
            except Exception as e:
                logger.warning(f"Progressive chemistry error for {team_abbr}: {e}")
                # Fall through to static lookup
        
        # Fallback to static pre-loaded data
        if not self.loaded:
            self.load()
        
        # Try exact match
        if team_abbr in self.team_chemistry:
            return self.team_chemistry[team_abbr]
        
        # Try common abbreviation mappings
        abbr_map = {
            'BKN': 'BRK', 'PHX': 'PHO', 'CHA': 'CHO',
            'NOP': 'NOP', 'NYK': 'NYK', 'LAL': 'LAL',
        }
        mapped = abbr_map.get(team_abbr, team_abbr)
        if mapped in self.team_chemistry:
            return self.team_chemistry[mapped]
        
        # Default neutral chemistry
        return 0.5
    
    def get_chemistry_differential(self, home_team: str, away_team: str,
                                    current_date: str = None, games_df = None) -> float:
        """
        Get chemistry advantage for home team over away team.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            current_date: Date string for pregame-only calculation
            games_df: DataFrame with game history
        """
        home_chem = self.get_team_chemistry_score(home_team, current_date, games_df)
        away_chem = self.get_team_chemistry_score(away_team, current_date, games_df)
        return home_chem - away_chem
    
    def get_top_team_duos(self, team_abbr: str, n: int = 5) -> List[Dict]:
        """Get top player duos for a specific team."""
        if not self.loaded:
            self.load()
        
        team_duos = []
        for pair_key, pair_data in self.player_pairs.items():
            if pair_data.get('team') == team_abbr:
                team_duos.append({
                    'players': f"{pair_data['player1']} + {pair_data['player2']}",
                    'net_rating': pair_data.get('net_rating', 0),
                    'games': pair_data.get('games', 0),
                    'minutes': pair_data.get('minutes', 0),
                })
        
        # Sort by minutes (most impactful duos)
        team_duos.sort(key=lambda x: x['minutes'], reverse=True)
        return team_duos[:n]
    
    def get_league_top_duos(self, n: int = 10) -> List[Dict]:
        """Get top duos across the entire league."""
        if not self.loaded:
            self.load()
        return self.top_duos[:n]
    
    def predict_chemistry_impact(self, home_team: str, away_team: str) -> Dict:
        """
        Predict the chemistry impact on a game.
        
        Returns:
            Dictionary with chemistry analysis for the matchup.
        """
        if not self.loaded:
            self.load()
        
        home_chem = self.get_team_chemistry_score(home_team)
        away_chem = self.get_team_chemistry_score(away_team)
        diff = home_chem - away_chem
        
        # Convert to win probability adjustment (-5% to +5%)
        win_prob_adjustment = diff * 0.1  # 10% max impact
        
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_chemistry_score': round(home_chem, 3),
            'away_chemistry_score': round(away_chem, 3),
            'chemistry_differential': round(diff, 3),
            'win_probability_adjustment': round(win_prob_adjustment, 3),
            'home_top_duos': self.get_top_team_duos(home_team, 3),
            'away_top_duos': self.get_top_team_duos(away_team, 3),
        }


# Singleton instance
_chemistry_model = None

def get_chemistry_model() -> PlayerChemistryModel:
    """Get or create the chemistry model singleton."""
    global _chemistry_model
    if _chemistry_model is None:
        _chemistry_model = PlayerChemistryModel()
        _chemistry_model.load()
    return _chemistry_model

async def get_chemistry_model_async() -> PlayerChemistryModel:
    """Async version of chemistry model getter."""
    global _chemistry_model
    if _chemistry_model is None:
        _chemistry_model = PlayerChemistryModel()
        await _chemistry_model.load_async()
    elif not _chemistry_model.loaded:
        await _chemistry_model.load_async()
    return _chemistry_model


if __name__ == "__main__":
    # Test the model
    model = PlayerChemistryModel()
    if model.load():
        print("\n🏀 Chemistry Model Test")
        print("=" * 50)
        
        # Test a matchup
        result = model.predict_chemistry_impact("BOS", "LAL")
        print(f"\nBOS vs LAL:")
        print(f"  Boston chemistry: {result['home_chemistry_score']}")
        print(f"  Lakers chemistry: {result['away_chemistry_score']}")
        print(f"  Win prob adjustment: {result['win_probability_adjustment']:+.1%}")
        
        print("\n🔝 League Top Duos:")
        for duo in model.get_league_top_duos(5):
            print(f"  {duo['players']}: {duo['net_rating']:.1f} net rating")
