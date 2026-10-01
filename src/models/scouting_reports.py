"""Generate scouting reports that read like a real analyst wrote them.

We take the model's predictions and SHAP explanations and turn them into
natural language that tells you what's actually happening in the matchup.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ScoutingReportGenerator:
    """Turn predictions into readable scouting reports."""
    
    def __init__(self):
        self.templates = {
            "high_confidence_home": """
## 🏀 Scouting Report: {home_team} vs {away_team}

**Prediction**: {home_team} WIN ({confidence:.0f}% confidence)

### Why {home_team} Wins
{explanation}

### Key Factors
{factors}

### Model Consensus
All {model_count} models agree: {consensus}

---
*Generated {timestamp}*
""",
            "high_confidence_away": """
## 🏀 Scouting Report: {home_team} vs {away_team}

**Prediction**: {away_team} WIN ({confidence:.0f}% confidence)

### Why {away_team} Wins
{explanation}

### Key Factors
{factors}

### Model Consensus
{model_count} models agree: {consensus}

---
*Generated {timestamp}*
""",
            "close_game": """
## 🏀 Scouting Report: {home_team} vs {away_team}

**Prediction**: Close Game - Slight edge to {predicted_winner}

### Analysis
This matchup is too close to call with high confidence ({confidence:.0f}%).

### Key Factors
{factors}

### Betting Angle
Consider avoiding this game or looking for prop bets instead.

---
*Generated {timestamp}*
"""
        }
    
    def generate_report(
        self,
        home_team: str,
        away_team: str,
        home_win_prob: float,
        away_win_prob: float,
        confidence: float,
        shap_explanation: Optional[Dict] = None,
        model_votes: Optional[Dict] = None
    ) -> str:
        """
        Generate a scouting report for a game.
        
        Args:
            home_team: Home team name
            away_team: Away team name
            home_win_prob: Home win probability (0-100)
            away_win_prob: Away win probability (0-100)
            confidence: Model confidence (0-100)
            shap_explanation: Optional SHAP explanation dict
            model_votes: Optional dict of individual model votes
            
        Returns:
            Markdown-formatted scouting report
        """
        # Determine template
        if confidence >= 70:
            if home_win_prob > away_win_prob:
                template_key = "high_confidence_home"
            else:
                template_key = "high_confidence_away"
        else:
            template_key = "close_game"
        
        # Build factors list
        factors = ""
        if shap_explanation and "top_features" in shap_explanation:
            for i, f in enumerate(shap_explanation["top_features"][:3], 1):
                impact = "+" if f["impact"] == "positive" else "-"
                factors += f"- {impact} **{f['feature'].replace('_', ' ').title()}**: {f['contribution']} impact\n"
        else:
            factors = "- Home court advantage\n- Recent team form\n- Historical matchup data\n"
        
        # Build consensus string
        if model_votes:
            home_votes = sum(1 for v in model_votes.values() if v == "HOME")
            away_votes = len(model_votes) - home_votes
            consensus = f"{max(home_votes, away_votes)}/{len(model_votes)} models"
            model_count = len(model_votes)
        else:
            consensus = "Majority of models"
            model_count = 3
        
        # Generate explanation
        if shap_explanation and "explanation" in shap_explanation:
            explanation = shap_explanation["explanation"]
        else:
            if home_win_prob > away_win_prob:
                explanation = f"{home_team} has a significant advantage based on our ensemble analysis."
            else:
                explanation = f"{away_team} is the stronger team based on current metrics."
        
        # Format report
        report = self.templates[template_key].format(
            home_team=home_team,
            away_team=away_team,
            confidence=confidence,
            explanation=explanation,
            factors=factors,
            consensus=consensus,
            model_count=model_count,
            predicted_winner=home_team if home_win_prob > away_win_prob else away_team,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        
        return report.strip()


# Global instance
report_generator = ScoutingReportGenerator()
