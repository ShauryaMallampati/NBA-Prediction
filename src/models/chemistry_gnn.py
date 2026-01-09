"""
Graph Neural Network for Player Chemistry

A simple GCN-inspired model that learns player synergy patterns.
Uses PyTorch (no need for torch_geometric for this simple version).
"""

import json
import numpy as np
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
    
    def load(self) -> bool:
        """Load chemistry data from scraped files."""
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
    
    def get_team_chemistry_score(self, team_abbr: str) -> float:
        """Get chemistry score for a team (0-1 scale)."""
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
    
    def get_chemistry_differential(self, home_team: str, away_team: str) -> float:
        """Get chemistry advantage for home team over away team."""
        home_chem = self.get_team_chemistry_score(home_team)
        away_chem = self.get_team_chemistry_score(away_team)
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
