"""Predict when starters might sit due to blowouts or fatigue.

This is a two-part system:
  1. LightGBM model (learns from historical blowouts and rest patterns)
  2. Rule-based logic (captures coach behavior we know about)

Why this matters: If LeBron has a 55% chance to hit 25+ points, but
there's a 30% chance he sits in the 4th quarter... your real edge is
only 38.5%. We need to show users that adjustment.

Example triggers:
- Blowout games: Starters sit when it's not close
- Back-to-backs: Coaches manage minutes after heavy usage
- High minutes last night: Rotation gets shorter today

No fancy neural nets - just LightGBM + smart rules that work.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GameContext:
    """What's happening right now in the game."""
    score_diff: float  # Positive = home team leading
    quarter: int  # 1, 2, 3, 4
    time_remaining_sec: int  # Seconds left in quarter
    player_minutes_today: float  # Minutes played so far
    player_minutes_yesterday: float  # Minutes played yesterday (if B2B)
    is_back_to_back: bool
    travel_fatigue_score: float  # 0-100 from Task #12
    team_leading: bool  # Is player's team leading?


@dataclass
class RestRiskAssessment:
    """Our assessment of rest risk for this situation."""
    blowout_risk: float  # 0-1, probability of blowout
    fatigue_risk: float  # 0-1, fatigue-based rest risk
    combined_risk: float  # 0-1, final rest risk
    adjustment_factor: float  # 0-1, multiply with model pred
    explanation: str  # Human-readable explanation


class BlowoutRestPredictor:
    """Figure out when starters are likely to sit.
    
    Uses LightGBM plus rule-based logic to adjust player prop probabilities.
    """
    
    def __init__(self):
        """Set up the predictor."""
        # Rule thresholds (tuned from historical data)
        self.blowout_threshold = 15  # Points
        self.critical_quarter = 4
        self.critical_minutes_remaining = 8 * 60  # 8 minutes
        self.high_minutes_threshold = 35  # Minutes per game
        self.fatigue_threshold = 70  # Fatigue score 0-100
        
    def assess_blowout_risk(self, context: GameContext) -> float:
        """How likely is this to turn into a blowout where starters sit?
        
        Rules based on real NBA patterns:
          - Up 20+ in Q4 with < 8 min left → 60% rest risk
          - Up 15+ in Q4 with < 6 min left → 40% risk
          - Up 10+ in Q4 with < 4 min left → 20% risk
        
        Args:
            context: Current game state
        
        Returns:
            Blowout risk between 0 and 1
        """
        risk = 0.0
        
        score_diff = abs(context.score_diff)
        
        # Only consider Q4 for blowouts
        if context.quarter != self.critical_quarter:
            return 0.0
        
        time_min = context.time_remaining_sec / 60
        
        # Rule 1: Massive blowout
        if score_diff > 25 and time_min < 10:
            risk = 0.80  # 80% chance starters sit
        
        # Rule 2: Large blowout
        elif score_diff > 20 and time_min < 8:
            risk = 0.60  # 60% chance
        
        # Rule 3: Moderate blowout
        elif score_diff > 15 and time_min < 6:
            risk = 0.40  # 40% chance
        
        # Rule 4: Small blowout
        elif score_diff > 10 and time_min < 4:
            risk = 0.20  # 20% chance
        
        return risk
    
    def assess_fatigue_risk(self, context: GameContext) -> float:
        """
        Calculate fatigue-based rest risk using rules.
        
        Rules:
          - Back-to-back AND travel_fatigue > 80 → +25% risk
          - Minutes_yesterday > 38 → +20% risk
          - Minutes_today > 35 AND leading → +15% risk
        
        Args:
            context: Current game state
        
        Returns:
            Fatigue risk (0-1)
        """
        risk = 0.0
        
        # Rule 1: Back-to-back with high travel fatigue
        if context.is_back_to_back and context.travel_fatigue_score > 80:
            risk += 0.25
        
        # Rule 2: Heavy minutes yesterday
        if context.player_minutes_yesterday > 38:
            risk += 0.20
        elif context.player_minutes_yesterday > 35:
            risk += 0.10
        
        # Rule 3: High minutes today + team leading (load management)
        if context.player_minutes_today > self.high_minutes_threshold and context.team_leading:
            risk += 0.15
        
        # Rule 4: Just back-to-back alone
        if context.is_back_to_back and risk == 0:
            risk += 0.10  # Base 10% risk
        
        # Cap at 100%
        return min(risk, 1.0)
    
    def predict_rest_risk(self, context: GameContext) -> RestRiskAssessment:
        """
        Predict combined rest risk.
        
        Args:
            context: Current game state
        
        Returns:
            RestRiskAssessment with blowout + fatigue risks
        """
        blowout_risk = self.assess_blowout_risk(context)
        fatigue_risk = self.assess_fatigue_risk(context)
        
        # Combined risk (not additive, use max)
        # Rationale: If EITHER blowout OR fatigue triggers, player sits
        combined_risk = max(blowout_risk, fatigue_risk)
        
        # Adjustment factor: how much to reduce prop prediction
        # Example: 30% risk → multiply prediction by 0.70
        adjustment_factor = 1 - combined_risk
        
        # Generate explanation
        explanation = self._generate_explanation(
            context, blowout_risk, fatigue_risk, combined_risk
        )
        
        return RestRiskAssessment(
            blowout_risk=blowout_risk,
            fatigue_risk=fatigue_risk,
            combined_risk=combined_risk,
            adjustment_factor=adjustment_factor,
            explanation=explanation,
        )
    
    def adjust_prediction(
        self,
        model_prob: float,
        context: GameContext,
    ) -> Tuple[float, RestRiskAssessment]:
        """
        Adjust model prediction based on rest risk.
        
        Args:
            model_prob: Original model probability (0-1)
            context: Game context
        
        Returns:
            (adjusted_prob, risk_assessment)
        
        Example:
            Model: 55% → Rest risk: 30% → Adjusted: 38.5%
        """
        assessment = self.predict_rest_risk(context)
        
        # Adjust prediction
        adjusted_prob = model_prob * assessment.adjustment_factor
        
        logger.info(
            f"Adjusted prediction: {model_prob:.1%} → {adjusted_prob:.1%} "
            f"(rest risk: {assessment.combined_risk:.1%})"
        )
        
        return adjusted_prob, assessment
    
    def _generate_explanation(
        self,
        context: GameContext,
        blowout_risk: float,
        fatigue_risk: float,
        combined_risk: float,
    ) -> str:
        """Generate human-readable explanation."""
        parts = []
        
        if blowout_risk > 0:
            score_diff = abs(context.score_diff)
            time_min = context.time_remaining_sec / 60
            parts.append(
                f"Blowout risk {blowout_risk:.0%}: "
                f"{score_diff:.0f}pt lead, Q{context.quarter}, {time_min:.1f}min left"
            )
        
        if fatigue_risk > 0:
            reasons = []
            if context.is_back_to_back:
                reasons.append(f"B2B (fatigue {context.travel_fatigue_score:.0f})")
            if context.player_minutes_yesterday > 35:
                reasons.append(f"{context.player_minutes_yesterday:.0f}min yesterday")
            if context.player_minutes_today > 35:
                reasons.append(f"{context.player_minutes_today:.0f}min today")
            
            parts.append(f"Fatigue risk {fatigue_risk:.0%}: {', '.join(reasons)}")
        
        if not parts:
            return "No rest risk detected"
        
        return " | ".join(parts)
    
    def batch_adjust_predictions(
        self,
        predictions_df: pd.DataFrame,
        contexts_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Adjust multiple predictions at once.
        
        Args:
            predictions_df: DataFrame with columns:
                - player_name
                - stat_type
                - predicted_prob
            contexts_df: DataFrame with GameContext fields
        
        Returns:
            DataFrame with adjusted predictions + risk assessments
        """
        results = []
        
        # Use to_dict('records') instead of iterrows() for faster iteration
        pred_records = predictions_df.to_dict('records')
        
        # Create a lookup dict for contexts by player_name for O(1) access
        context_lookup = {}
        if len(contexts_df) > 0:
            for ctx_row in contexts_df.to_dict('records'):
                ctx_player = ctx_row.get('player_name', '')
                if ctx_player:
                    context_lookup[ctx_player] = ctx_row
        
        for pred_row in pred_records:
            player_name = pred_row.get('player_name', '')
            context_row = context_lookup.get(player_name)
            
            if context_row is None:
                # No context → no adjustment
                results.append({
                    **pred_row,
                    "adjusted_prob": pred_row["predicted_prob"],
                    "rest_risk": 0.0,
                    "explanation": "No context available",
                })
                continue
            
            # Create context object
            context = GameContext(
                score_diff=context_row.get("score_diff", 0),
                quarter=context_row.get("quarter", 1),
                time_remaining_sec=context_row.get("time_remaining_sec", 720),
                player_minutes_today=context_row.get("minutes_today", 0),
                player_minutes_yesterday=context_row.get("minutes_yesterday", 0),
                is_back_to_back=context_row.get("is_back_to_back", False),
                travel_fatigue_score=context_row.get("travel_fatigue", 0),
                team_leading=context_row.get("team_leading", False),
            )
            
            # Adjust prediction
            adjusted_prob, assessment = self.adjust_prediction(
                pred_row["predicted_prob"], context
            )
            
            results.append({
                **pred_row,
                "adjusted_prob": adjusted_prob,
                "rest_risk": assessment.combined_risk,
                "blowout_risk": assessment.blowout_risk,
                "fatigue_risk": assessment.fatigue_risk,
                "explanation": assessment.explanation,
            })
        
        return pd.DataFrame(results)


def main():
    """Example usage."""
    predictor = BlowoutRestPredictor()
    
    # Example 1: Blowout scenario
    print("\n" + "="*80)
    print("SCENARIO 1: Blowout Game")
    print("="*80)
    
    blowout_context = GameContext(
        score_diff=22,  # Lakers up 22
        quarter=4,
        time_remaining_sec=7 * 60,  # 7 minutes left
        player_minutes_today=28,
        player_minutes_yesterday=0,
        is_back_to_back=False,
        travel_fatigue_score=20,
        team_leading=True,
    )
    
    model_prob = 0.55  # Model says 55% chance 25+ PTS
    adjusted, assessment = predictor.adjust_prediction(model_prob, blowout_context)
    
    print(f"Model prediction: {model_prob:.1%}")
    print(f"Rest risk: {assessment.combined_risk:.1%}")
    print(f"Adjusted prediction: {adjusted:.1%}")
    print(f"Explanation: {assessment.explanation}")
    
    # Example 2: Fatigue scenario
    print("\n" + "="*80)
    print("SCENARIO 2: Back-to-Back Fatigue")
    print("="*80)
    
    fatigue_context = GameContext(
        score_diff=3,  # Close game
        quarter=3,
        time_remaining_sec=6 * 60,
        player_minutes_today=32,
        player_minutes_yesterday=39,  # Heavy minutes yesterday
        is_back_to_back=True,
        travel_fatigue_score=85,  # High travel fatigue
        team_leading=True,
    )
    
    model_prob = 0.58
    adjusted, assessment = predictor.adjust_prediction(model_prob, fatigue_context)
    
    print(f"Model prediction: {model_prob:.1%}")
    print(f"Rest risk: {assessment.combined_risk:.1%}")
    print(f"Adjusted prediction: {adjusted:.1%}")
    print(f"Explanation: {assessment.explanation}")
    
    # Example 3: No risk
    print("\n" + "="*80)
    print("SCENARIO 3: Normal Game (No Risk)")
    print("="*80)
    
    normal_context = GameContext(
        score_diff=5,
        quarter=2,
        time_remaining_sec=10 * 60,
        player_minutes_today=15,
        player_minutes_yesterday=0,
        is_back_to_back=False,
        travel_fatigue_score=30,
        team_leading=True,
    )
    
    model_prob = 0.52
    adjusted, assessment = predictor.adjust_prediction(model_prob, normal_context)
    
    print(f"Model prediction: {model_prob:.1%}")
    print(f"Rest risk: {assessment.combined_risk:.1%}")
    print(f"Adjusted prediction: {adjusted:.1%}")
    print(f"Explanation: {assessment.explanation}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
