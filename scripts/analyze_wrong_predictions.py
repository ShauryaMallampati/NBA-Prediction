#!/usr/bin/env python3
"""
Wrong Prediction Analysis Script

Uses Qwen2.5-3B to analyze and explain why predictions were incorrect.
Combines box score analysis with web-scraped storylines.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
PREDICTIONS_DIR = Path("data/predictions")
METRICS_DIR = Path("data/metrics")
OUTPUT_DIR = Path("data/analysis")


class WrongPredictionAnalyzer:
    """Analyzes wrong predictions using Qwen2.5-3B."""
    
    def __init__(self, model_name: str = "Qwen/Qwen2.5-3B-Instruct"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self._loaded = False
        
    def load_model(self) -> bool:
        """Load Qwen2.5-3B model."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            logger.info(f"Loading {self.model_name}...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, 
                trust_remote_code=True
            )
            
            # Use float16 for memory efficiency
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            
            self._loaded = True
            logger.info("✅ Qwen2.5-3B loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
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
    
    async def scrape_game_storyline(self, home_team: str, away_team: str, date: str) -> str:
        """Scrape game storyline from web sources."""
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            # Try ESPN
            search_query = f"{away_team} vs {home_team} {date} NBA game recap"
            
            # For now, return basic info (real implementation would scrape)
            return f"Game between {away_team} @ {home_team} on {date}"
            
        except Exception as e:
            logger.warning(f"Failed to scrape storyline: {e}")
            return ""
    
    def analyze_prediction(
        self, 
        prediction: Dict[str, Any],
        storyline: str = ""
    ) -> str:
        """Generate analysis for a wrong prediction using Qwen2.5."""
        if not self._loaded:
            if not self.load_model():
                return "Model not available - cannot generate analysis"
        
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

{f'GAME STORYLINE: {storyline}' if storyline else ''}

Provide a brief analysis (2-3 sentences) explaining what factors we might have missed or misjudged. Focus on basketball-specific reasons like injuries, hot streaks, matchup advantages, or situational factors."""

        try:
            import torch
            
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=200,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract just the assistant's response
            if "assistant" in response.lower():
                response = response.split("assistant")[-1].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
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
            storyline = await self.scrape_game_storyline(
                pred.get('home_team', ''),
                pred.get('away_team', ''),
                date
            )
            
            analysis = self.analyze_prediction(pred, storyline)
            
            results.append({
                **pred,
                'analysis': analysis,
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
    
    parser = argparse.ArgumentParser(description="Analyze wrong predictions")
    parser.add_argument(
        "--date", 
        type=str, 
        default=None,
        help="Date to analyze (YYYY-MM-DD), defaults to yesterday"
    )
    args = parser.parse_args()
    
    target_date = args.date or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    logger.info(f"📊 Analyzing wrong predictions for {target_date}")
    
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
