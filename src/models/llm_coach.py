"""
LLM Coach / Reasoning Layer stub.
"""
from typing import Dict
from src.services.data.web_scraper import nba_scraper

class LLMCoach:
    def analyze_matchup(self, home, away, prob, date) -> Dict:
        # Fetch Context
        injuries = nba_scraper.get_injuries(home) + nba_scraper.get_injuries(away)
        news = nba_scraper.get_team_news(home) + nba_scraper.get_team_news(away)
        
        # Mock Logic (Placeholders for real LLM call)
        adj = 0.0
        reasoning = "Standard analysis."
        
        if len(injuries) > 2:
            adj = -0.05 if "Out" in str(injuries) else -0.02
            reasoning = "Significant injuries detected."
            
        return {
            "final_prob": prob + adj,
            "reasoning": reasoning
        }

llm_coach = LLMCoach()
