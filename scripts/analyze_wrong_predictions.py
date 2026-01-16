#!/usr/bin/env python3
"""
Wrong Prediction Analysis Script

Uses Gemini 2.5 Flash to analyze and explain why predictions were incorrect.
Generates brief, insightful analysis for each wrong prediction.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
PREDICTIONS_DIR = Path("data/predictions")
METRICS_DIR = Path("data/metrics")
OUTPUT_DIR = Path("data/analysis")

# Gemini model choice (Gemini 3 Flash Preview = Latest, smartest, and fastest)
GEMINI_MODEL = "gemini-3-flash-preview"


class WrongPredictionAnalyzer:
    """Analyzes wrong predictions using Gemini 2.5 Flash API."""
    
    def __init__(self):
        self._loaded = False
        self._gemini_model = None
        
    def load_model(self) -> bool:
        """Initialize Gemini API client."""
        gemini_key = os.environ.get("GEMINI_API_KEY")
        
        if not gemini_key:
            logger.error("❌ GEMINI_API_KEY environment variable not set")
            logger.info("   Set it with: export GEMINI_API_KEY='your-api-key'")
            return False
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            
            # Using Gemini 2.5 Flash (fast, high quality, generous free tier)
            self._gemini_model = genai.GenerativeModel(GEMINI_MODEL)
            self._loaded = True
            logger.info(f"✅ {GEMINI_MODEL} API configured successfully")
            return True
            
        except ImportError:
            logger.error("❌ google-generativeai package not installed")
            logger.info("   Install with: pip install google-generativeai")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to configure Gemini: {e}")
            return False
    
    def get_wrong_predictions(self, date: str) -> List[Dict[str, Any]]:
        """Load wrong predictions for a specific date."""
        predictions_file = PREDICTIONS_DIR / f"predictions_{date}.json"
        evaluations_file = PREDICTIONS_DIR / f"evaluations_{date}.json"
        
        if not predictions_file.exists():
            logger.warning(f"No predictions file for {date}")
            return []
        
        with open(predictions_file, 'r') as f:
            predictions = json.load(f)
        
        if evaluations_file.exists():
            with open(evaluations_file, 'r') as f:
                evaluations = json.load(f)
        else:
            evaluations = {}
        
        # Find wrong predictions
        wrong = []
        for pred in predictions:
            game_id = pred.get('game_id')
            if game_id in evaluations:
                eval_result = evaluations[game_id]
                if not eval_result.get('correct', True):
                    wrong.append({
                        **pred,
                        'actual_winner': eval_result.get('actual_winner'),
                        'home_score': eval_result.get('home_score'),
                        'away_score': eval_result.get('away_score')
                    })
        
        return wrong
    
    def analyze_prediction(self, prediction: Dict[str, Any]) -> str:
        """Generate analysis for a wrong prediction using Gemini."""
        if not self._loaded:
            if not self.load_model():
                return "Analysis unavailable - Gemini API not configured"
        
        home_team = prediction.get('home_team', 'Home')
        away_team = prediction.get('away_team', 'Away')
        predicted = prediction.get('prediction', 'Unknown')
        actual = prediction.get('actual_winner', 'Unknown')
        confidence = prediction.get('confidence', 50)
        home_score = prediction.get('home_score', '?')
        away_score = prediction.get('away_score', '?')
        
        prompt = f"""You are an NBA sports analyst. Analyze why this prediction was wrong.

PREDICTION DETAILS:
- Matchup: {away_team} @ {home_team}
- Our Prediction: {predicted} would win
- Actual Result: {actual} won ({away_team} {away_score} - {home_team} {home_score})
- Our Confidence: {confidence}%

Provide a brief analysis (2-3 sentences max) explaining why our prediction was wrong.
Consider factors like: injuries, recent team form, home court advantage, key player performances, or matchup issues.
Be specific and insightful."""

        try:
            response = self._gemini_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return f"Analysis unavailable: {str(e)}"
    
    async def analyze_date(self, date: str) -> List[Dict[str, Any]]:
        """Analyze all wrong predictions for a date."""
        wrong_predictions = self.get_wrong_predictions(date)
        
        if not wrong_predictions:
            logger.info(f"No wrong predictions found for {date}")
            return []
        
        logger.info(f"Analyzing {len(wrong_predictions)} wrong predictions for {date}")
        
        results = []
        for pred in wrong_predictions:
            analysis = self.analyze_prediction(pred)
            
            results.append({
                **pred,
                'analysis': analysis,
                'model_used': GEMINI_MODEL,
                'analyzed_at': datetime.now().isoformat()
            })
        
        # Save results
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_file = OUTPUT_DIR / f"analysis_{date}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"✅ Saved analysis to {output_file}")
        return results


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze wrong predictions using Gemini AI")
    parser.add_argument(
        "--date", 
        type=str, 
        default=None,
        help="Date to analyze (YYYY-MM-DD), defaults to yesterday"
    )
    args = parser.parse_args()
    
    target_date = args.date or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    logger.info(f"📊 Analyzing wrong predictions for {target_date}")
    logger.info(f"🤖 Using model: {GEMINI_MODEL}")
    
    analyzer = WrongPredictionAnalyzer()
    results = await analyzer.analyze_date(target_date)
    
    if results:
        print(f"\n📋 Analysis Results for {target_date}:")
        print("=" * 60)
        for r in results:
            print(f"\n🏀 {r['away_team']} @ {r['home_team']}")
            print(f"   Predicted: {r['prediction']} | Actual: {r['actual_winner']}")
            print(f"   Score: {r.get('away_score', '?')} - {r.get('home_score', '?')}")
            print(f"   Analysis: {r['analysis']}")
    else:
        print(f"No wrong predictions to analyze for {target_date}")


if __name__ == "__main__":
    asyncio.run(main())
