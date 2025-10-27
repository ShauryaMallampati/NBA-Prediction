"""Kelly Criterion bet sizing with multivariate optimization.

The Kelly Criterion formula is: f* = (bp - q) / b
where:
- f* = fraction of bankroll to wager
- b = odds received (decimal odds - 1)
- p = probability of winning
- q = probability of losing (1 - p)

For multiple simultaneous bets, we use fractional Kelly to reduce risk.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class KellyCriterion:
    """Kelly Criterion bet sizing calculator."""

    def __init__(
        self,
        bankroll: float = 1000.0,
        kelly_fraction: float = 0.25,
        min_edge: float = 0.05,
        max_bet_pct: float = 0.05,
    ):
        """
        Initialize Kelly calculator.

        Args:
            bankroll: Total bankroll in dollars
            kelly_fraction: Fraction of full Kelly to use (0.25 = quarter kelly, safer)
            min_edge: Minimum edge required to place a bet (5% default)
            max_bet_pct: Maximum % of bankroll to risk on single bet (5% default)
        """
        self.bankroll = bankroll
        self.kelly_fraction = kelly_fraction
        self.min_edge = min_edge
        self.max_bet_pct = max_bet_pct

        logger.info(
            f"🎯 Kelly Criterion initialized:"
            f"\n  Bankroll: ${bankroll:,.2f}"
            f"\n  Kelly Fraction: {kelly_fraction:.0%}"
            f"\n  Min Edge: {min_edge:.1%}"
            f"\n  Max Bet %: {max_bet_pct:.1%}"
        )

    def calculate_kelly(
        self,
        probability: float,
        odds: float,
    ) -> float:
        """
        Calculate Kelly fraction for single bet.

        Args:
            probability: Probability of winning (0-1)
            odds: Decimal odds (e.g., 2.0 for -110 line)

        Returns:
            Kelly fraction (percentage of bankroll to wager)
        """
        if not 0 < probability < 1:
            return 0.0

        # Convert decimal odds to american odds
        # odds = 1 + b, so b = odds - 1
        b = odds - 1
        p = probability
        q = 1 - p

        # Kelly formula: f* = (bp - q) / b
        kelly_raw = (b * p - q) / b if b != 0 else 0

        # Apply kelly fraction (e.g., 0.25 for quarter kelly)
        kelly = kelly_raw * self.kelly_fraction

        # Ensure kelly is not negative (no negative Kelly betting)
        kelly = max(0, kelly)

        return kelly

    def calculate_edge(self, probability: float, odds: float) -> float:
        """
        Calculate edge vs market odds.

        Args:
            probability: Our estimated probability
            odds: Market decimal odds

        Returns:
            Edge as percentage
        """
        market_prob = 1 / odds  # Implied probability from odds
        edge = probability - market_prob
        return edge

    def size_single_bet(
        self,
        probability: float,
        odds: float,
        min_odds: float = 1.5,
        max_odds: float = 3.0,
    ) -> Dict:
        """
        Size a single bet using Kelly Criterion.

        Args:
            probability: Our estimated win probability (0-1)
            odds: Decimal odds offered
            min_odds: Minimum odds to consider (-110 ≈ 1.91)
            max_odds: Maximum odds to consider (3.0)

        Returns:
            Dict with bet sizing and metrics
        """
        # Validate inputs
        if not (0 < probability < 1):
            logger.warning(f"Invalid probability: {probability}")
            return {
                "bet_size": 0,
                "kelly_pct": 0,
                "edge": 0,
                "reason": "Invalid probability",
            }

        if odds < min_odds or odds > max_odds:
            return {
                "bet_size": 0,
                "kelly_pct": 0,
                "edge": 0,
                "reason": f"Odds {odds} outside range [{min_odds}, {max_odds}]",
            }

        # Calculate edge
        edge = self.calculate_edge(probability, odds)

        # Check minimum edge requirement
        if edge < self.min_edge:
            return {
                "bet_size": 0,
                "kelly_pct": 0,
                "edge": edge,
                "reason": f"Edge {edge:.2%} < minimum {self.min_edge:.2%}",
            }

        # Calculate Kelly
        kelly_pct = self.calculate_kelly(probability, odds)

        # Apply maximum bet size limit
        max_bet = self.bankroll * self.max_bet_pct
        kelly_bet = self.bankroll * kelly_pct
        bet_size = min(kelly_bet, max_bet)

        return {
            "bet_size": bet_size,
            "kelly_pct": kelly_pct,
            "kelly_raw_pct": self.calculate_kelly(probability, odds) / self.kelly_fraction,
            "edge": edge,
            "expected_value": bet_size * edge,
            "roi": edge * (odds - 1),  # ROI if we win
            "prob_win": probability,
            "odds": odds,
        }

    def size_multiple_bets(
        self,
        bets: List[Dict],
        correlation_matrix: Optional[np.ndarray] = None,
    ) -> Dict:
        """
        Size multiple simultaneous bets with correlation consideration.

        Args:
            bets: List of dicts with keys:
                - 'stat': stat name (PTS, AST, etc)
                - 'probability': win probability (0-1)
                - 'odds': decimal odds
            correlation_matrix: Correlation between outcomes (optional)

        Returns:
            Dict with:
                - 'allocations': List of bet sizes for each prop
                - 'total_allocation': Total $ to wager
                - 'recommended_allocation': Conservative recommendation
                - 'portfolio_metrics': Expected portfolio stats
        """
        if not bets:
            return {"allocations": [], "total_allocation": 0}

        allocations = []
        individual_bets = []

        # Calculate individual Kelly sizes
        for bet in bets:
            bet_result = self.size_single_bet(
                probability=bet["probability"],
                odds=bet["odds"],
            )
            bet_result["stat"] = bet.get("stat", f"Prop{len(individual_bets)}")
            allocations.append(bet_result)
            individual_bets.append(bet_result)

        # Filter only recommended bets
        recommended = [b for b in allocations if b["bet_size"] > 0]

        # Calculate portfolio metrics
        total_allocation = sum(b["bet_size"] for b in recommended)
        total_ev = sum(b["expected_value"] for b in recommended)

        # If no bets meet criteria, return empty
        if not recommended:
            logger.warning("No bets meet Kelly Criterion criteria")
            return {
                "allocations": allocations,
                "total_allocation": 0,
                "recommended_allocation": 0,
                "portfolio_metrics": {
                    "expected_value": 0,
                    "expected_roi": 0,
                    "portfolio_risk": 0,
                },
                "reason": "No bets exceed minimum edge requirement",
            }

        # Conservative: use half of Kelly allocation
        conservative_allocation = total_allocation * 0.5

        # Portfolio statistics
        portfolio_metrics = {
            "num_bets": len(recommended),
            "total_allocation": total_allocation,
            "average_bet_size": total_allocation / len(recommended),
            "expected_value": total_ev,
            "expected_roi": total_ev / self.bankroll,
            "Kelly_pct_of_bankroll": total_allocation / self.bankroll,
        }

        return {
            "allocations": allocations,
            "total_allocation": total_allocation,
            "recommended_allocation": conservative_allocation,
            "portfolio_metrics": portfolio_metrics,
        }

    def get_kelly_recommendation(
        self,
        predictions: Dict[str, Dict],
        odds_dict: Optional[Dict[str, float]] = None,
        use_conservative: bool = True,
    ) -> Dict:
        """
        Get Kelly Criterion bet sizing recommendation from predictions.

        Args:
            predictions: Dict with pred stat -> {calibrated, raw, confidence}
            odds_dict: Dict with stat -> decimal odds (optional, uses default)
            use_conservative: Use conservative (half kelly) sizing

        Returns:
            Betting recommendation with sizes for each stat
        """
        # Default odds (convert from common lines)
        default_odds = {
            "PTS": 1.909,  # -110 line
            "AST": 1.909,
            "REB": 1.909,
            "STL": 1.909,
            "BLK": 1.909,
        }

        # Use provided odds or defaults
        if odds_dict:
            default_odds.update(odds_dict)

        # Build bet list from predictions
        bets = []
        for stat, pred in predictions.items():
            if isinstance(pred, dict) and "calibrated" in pred:
                bets.append({
                    "stat": stat,
                    "probability": pred["calibrated"],
                    "odds": default_odds.get(stat, 1.909),
                })

        # Size portfolio
        sizing = self.size_multiple_bets(bets)

        # Generate recommendations
        recommendations = []
        for alloc in sizing["allocations"]:
            if alloc["bet_size"] > 0:
                allocation = alloc["bet_size"]
                if use_conservative:
                    allocation *= 0.5  # Half Kelly

                recommendations.append({
                    "stat": alloc["stat"],
                    "prediction": "OVER" if alloc["edge"] > 0 else "UNDER",
                    "bet_size": allocation,
                    "confidence": alloc["edge"],
                    "expected_value": alloc["expected_value"] * (0.5 if use_conservative else 1),
                    "kelly_pct": alloc["kelly_pct"],
                    "prob": alloc["prob_win"],
                })

        logger.info(
            f"📊 Kelly Criterion Betting Recommendation:"
            f"\n  Total Portfolio Allocation: ${sizing['total_allocation']:,.2f}"
            f"\n  Recommended (Conservative): ${sizing['recommended_allocation']:,.2f}"
            f"\n  Expected Portfolio EV: ${sizing['portfolio_metrics'].get('expected_value', 0):,.2f}"
            f"\n  Recommended Bets: {len(recommendations)}"
        )

        return {
            "recommendations": recommendations,
            "portfolio_metrics": sizing["portfolio_metrics"],
            "total_allocation": sizing["total_allocation"],
            "conservative_allocation": sizing["recommended_allocation"],
        }


def calculate_bet_kelly(
    probability: float,
    decimal_odds: float,
    bankroll: float = 1000,
    kelly_fraction: float = 0.25,
) -> float:
    """
    Quick utility to calculate Kelly bet size.

    Args:
        probability: Win probability (0-1)
        decimal_odds: Decimal odds (e.g., 2.0)
        bankroll: Total bankroll
        kelly_fraction: Fraction of Kelly to use

    Returns:
        Recommended bet size in dollars
    """
    b = decimal_odds - 1
    p = probability
    q = 1 - p

    kelly_raw = (b * p - q) / b
    kelly = max(0, kelly_raw * kelly_fraction)

    return bankroll * kelly


if __name__ == "__main__":
    # Example usage
    kelly = KellyCriterion(
        bankroll=10000,
        kelly_fraction=0.25,
        min_edge=0.05,
        max_bet_pct=0.05,
    )

    # Example predictions
    predictions = {
        "PTS": {"calibrated": 0.65, "confidence": 0.3},
        "AST": {"calibrated": 0.55, "confidence": 0.1},
        "REB": {"calibrated": 0.52, "confidence": 0.04},
        "STL": {"calibrated": 0.48, "confidence": -0.04},
        "BLK": {"calibrated": 0.50, "confidence": 0.0},
    }

    # Get recommendation
    recommendation = kelly.get_kelly_recommendation(predictions, use_conservative=True)

    print("\n" + "=" * 80)
    print("KELLY CRITERION BET SIZING")
    print("=" * 80)

    print("\n📋 Recommended Bets:")
    for rec in recommendation["recommendations"]:
        print(
            f"  {rec['stat']:>3s}: ${rec['bet_size']:>7.2f} @ {rec['prob']:.1%} "
            f"({rec['prediction']:>5s}) | EV: ${rec['expected_value']:.2f}"
        )

    print(f"\n💰 Portfolio Summary:")
    print(f"  Total Allocation: ${recommendation['total_allocation']:,.2f}")
    print(f"  Conservative (50% Kelly): ${recommendation['conservative_allocation']:,.2f}")
    print(
        f"  Expected Portfolio EV: ${recommendation['portfolio_metrics']['expected_value']:,.2f}"
    )

    print("\n" + "=" * 80)
