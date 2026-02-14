"""
"""Add rest risk calculations to our prediction API.

We adjust model probabilities when players are likely to sit due to
blowouts, fatigue, or back-to-back scheduling.
"""

# This script demonstrates how to integrate rest risk into the API
# The actual integration happens in betting_api.py

import sys
sys.path.insert(0, '/Users/shauryamallampati/Desktop/NBA prediction')

from datetime import datetime, timedelta
from src.models.pregame.blowout_rest_predictor import BlowoutRestPredictor, GameContext
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def integrate_rest_risk():
    """Show how rest risk gets integrated into the API."""
    
    print("\n" + "="*80)
    print("TASK #16: INTEGRATE REST RISK PREDICTOR")
    print("="*80)
    
    # Initialize rest predictor
    print("\n📊 Initializing rest risk predictor...")
    rest_predictor = BlowoutRestPredictor()
    print("✅ BlowoutRestPredictor ready")
    
    # Example scenarios
    print("\n🎯 Testing rest risk calculations...")
    print("-" * 80)
    
    scenarios = [
        {
            "name": "Close Game, Player Fresh",
            "context": GameContext(
                score_diff=2,  # Close game
                quarter=2,
                time_remaining_sec=300,
                player_minutes_today=10,
                player_minutes_yesterday=0,  # Not back-to-back
                is_back_to_back=False,
                travel_fatigue_score=20,  # Low fatigue
                team_leading=True,
            )
        },
        {
            "name": "Blowout Game, Deep in Q3",
            "context": GameContext(
                score_diff=20,  # Big lead
                quarter=3,
                time_remaining_sec=600,
                player_minutes_today=20,
                player_minutes_yesterday=35,  # B2B with heavy minutes
                is_back_to_back=True,
                travel_fatigue_score=65,  # Higher fatigue
                team_leading=True,
            )
        },
        {
            "name": "Tight Game, Player Worn Down",
            "context": GameContext(
                score_diff=-3,  # Trailing
                quarter=4,
                time_remaining_sec=120,
                player_minutes_today=35,
                player_minutes_yesterday=38,  # Heavy usage both nights
                is_back_to_back=True,
                travel_fatigue_score=80,  # High fatigue
                team_leading=False,
            )
        },
    ]
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario['name']}")
        context = scenario['context']
        
        # Calculate risk
        risk_assessment = rest_predictor.predict_rest_risk(context)
        rest_risk = risk_assessment.fatigue_risk  # Use fatigue component
        
        # Interpret
        risk_level = "🔴 HIGH" if rest_risk > 0.15 else "🟡 MEDIUM" if rest_risk > 0.08 else "🟢 LOW"
        print(f"  Rest Risk: {rest_risk:.1%} {risk_level}")
        
        # Calculate adjustment factor
        adjustment_factor = 1 - rest_risk
        print(f"  Adjustment Factor: {adjustment_factor:.2f}x")
        
        # Example probability adjustments
        example_probs = {
            "PTS": 0.55,
            "AST": 0.52,
            "REB": 0.51,
        }
        
        print(f"  Example Adjustments:")
        for stat, prob in example_probs.items():
            adjusted = prob * adjustment_factor
            change = (adjusted - prob) * 100
            print(f"    {stat}: {prob:.1%} → {adjusted:.1%} (change: {change:+.1f}%)")
    
    print("\n" + "="*80)
    print("HOW TO USE IN API ENDPOINTS")
    print("="*80)
    
    print("""
1. In /player-props endpoint:
   ```python
   # After getting model probability
   rest_context = GameContext(
       player_name=line.player_name,
       rest_days=get_player_rest_days(line.player_name, game_date),
       back_to_back=is_back_to_back(line.player_name, game_date),
       # ... other fields
   )
   rest_risk = rest_predictor.predict_rest_risk(rest_context)
   adjusted_prob = predicted_prob * (1 - rest_risk)
   ```

2. In /bet-opportunities endpoint:
   ```python
   # Add rest risk to each opportunity
   opportunity.rest_risk = rest_risk
   opportunity.adjusted_prob = adjusted_prob
   ```

3. Store in database:
   ```python
   BetRecord(
       # ... other fields
       rest_risk=rest_risk,
       adjusted_probability=adjusted_prob,
   )
   ```

4. In dashboard:
   - Show original vs adjusted probabilities
   - Highlight high rest risk bets
   - Track performance impact of rest factor
    """)
    
    print("\n✅ Rest risk integration strategy documented")
    print("\nNext Steps:")
    print("  • Update /player-props to calculate rest risk")
    print("  • Update /bet-opportunities to include adjusted_prob")
    print("  • Store rest_risk in betting database")
    print("  • Display in frontend dashboard")
    print("  • Monitor impact on win rate")


if __name__ == "__main__":
    integrate_rest_risk()
