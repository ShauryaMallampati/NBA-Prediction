"""
Supabase Client for NBA Intelligence Platform

Provides helper functions for storing predictions and evaluation results.
Uses the supabase-py library.
"""

import os
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("supabase-py not installed. Run: pip install supabase")


class SupabaseClient:
    """Wrapper for Supabase operations."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """Initialize the Supabase client from environment variables."""
        if self._initialized:
            return self.client is not None
            
        if not SUPABASE_AVAILABLE:
            logger.error("Supabase library not available")
            return False
            
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            logger.warning("SUPABASE_URL or SUPABASE_KEY not set in environment")
            return False
            
        try:
            self.client = create_client(url, key)
            self._initialized = True
            logger.info("✅ Supabase client initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            return False
    
    def insert_prediction(self, prediction: Dict[str, Any]) -> bool:
        """Insert a single prediction into the predictions table."""
        if not self.initialize():
            return False
            
        try:
            data = {
                "game_id": prediction.get("game_id"),
                "date": prediction.get("date"),
                "home_team": prediction.get("home_team"),
                "away_team": prediction.get("away_team"),
                "prediction": prediction.get("prediction"),
                # Schema uses short names: home_win_prob, away_win_prob
                "home_win_prob": prediction.get("home_win_probability"),
                "away_win_prob": prediction.get("away_win_probability"),
                "confidence": prediction.get("confidence"),
            }
            
            self.client.table("predictions").upsert(data, on_conflict="game_id,date").execute()
            return True
        except Exception as e:
            logger.error(f"Failed to insert prediction: {e}")
            return False
    
    def insert_predictions_batch(self, predictions: List[Dict[str, Any]]) -> int:
        """Insert multiple predictions. Returns count of successful inserts."""
        if not self.initialize():
            return 0
            
        success_count = 0
        for pred in predictions:
            if self.insert_prediction(pred):
                success_count += 1
        
        logger.info(f"Inserted {success_count}/{len(predictions)} predictions to Supabase")
        return success_count
    
    def insert_evaluation(self, evaluation: Dict[str, Any]) -> bool:
        """Insert daily evaluation results."""
        if not self.initialize():
            return False
            
        try:
            data = {
                "date": evaluation.get("date"),
                "total_games": evaluation.get("total_games"),
                "correct": evaluation.get("correct"),
                "accuracy": evaluation.get("accuracy"),
                "avg_confidence": evaluation.get("avg_confidence"),
                "model_version": evaluation.get("model_version", "ensemble_v2"),
            }
            
            self.client.table("evaluations").upsert(data, on_conflict="date").execute()
            logger.info(f"✅ Evaluation for {data['date']} saved to Supabase")
            return True
        except Exception as e:
            logger.error(f"Failed to insert evaluation: {e}")
            return False
    
    def get_accuracy_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get aggregated accuracy statistics from evaluations."""
        if not self.initialize():
            # Fall back to local CSV
            return self._get_accuracy_from_csv()
            
        try:
            response = self.client.table("evaluations")\
                .select("*")\
                .order("date", desc=True)\
                .limit(days)\
                .execute()
            
            data = response.data
            if not data:
                return self._get_accuracy_from_csv()
            
            total_games = sum(d.get("total_games", 0) for d in data)
            total_correct = sum(d.get("correct", 0) for d in data)
            
            if total_games > 0:
                accuracy = round((total_correct / total_games) * 100, 1)
            else:
                accuracy = 0.0
            
            return {
                "current_accuracy": accuracy,
                "total_games": total_games,
                "total_correct": total_correct,
                "days_evaluated": len(data),
                "source": "supabase"
            }
        except Exception as e:
            logger.error(f"Failed to get accuracy from Supabase: {e}")
            return self._get_accuracy_from_csv()
    
    def _get_accuracy_from_csv(self) -> Dict[str, Any]:
        """Fallback: get accuracy from local CSV file."""
        csv_path = Path("data/metrics/daily_accuracy.csv")
        
        if not csv_path.exists():
            return {
                "current_accuracy": None,
                "total_games": 0,
                "total_correct": 0,
                "days_evaluated": 0,
                "source": "missing"
            }
        
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            
            if df.empty:
                return {
                    "current_accuracy": None,
                    "total_games": 0,
                    "total_correct": 0,
                    "days_evaluated": 0,
                    "source": "csv_empty"
                }
            
            total_games = df["total_games"].sum()
            total_correct = df["correct"].sum()
            
            if total_games > 0:
                accuracy = round((total_correct / total_games) * 100, 1)
            else:
                accuracy = None
            
            return {
                "current_accuracy": accuracy,
                "total_games": int(total_games),
                "total_correct": int(total_correct),
                "days_evaluated": len(df),
                "source": "csv"
            }
        except Exception as e:
            logger.error(f"Failed to read CSV: {e}")
            return {
                "current_accuracy": None,
                "total_games": 0,
                "total_correct": 0,
                "days_evaluated": 0,
                "source": "error"
            }
    
    def get_predictions_for_date(self, date_str: str) -> List[Dict[str, Any]]:
        """Get all predictions for a specific date."""
        if not self.initialize():
            return []
            
        try:
            response = self.client.table("predictions")\
                .select("*")\
                .eq("date", date_str)\
                .execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Failed to get predictions: {e}")
            return []
            
    def insert_news(self, news_items: List[Dict[str, Any]]) -> int:
        """Insert scraped news into 'news_archive' table (Memory)."""
        if not self.initialize() or not news_items:
            return 0
        
        success = 0
        try:
            for item in news_items:
                data = {
                    "headline": item.get("headline"),
                    "link": item.get("link"),
                    "source": item.get("source"),
                    "team": item.get("team"),
                    "scraped_at": datetime.now().isoformat()
                }
                # Assuming 'news_archive' table exists or will be created
                self.client.table("news_archive").upsert(data, on_conflict="link").execute()
                success += 1
            logger.info(f"💾 Saved {success} news items to Supabase Memory")
            return success
        except Exception as e:
            logger.warning(f"Failed to save news to Supabase (Table might be missing): {e}")
            return 0


# Singleton instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get or create the Supabase client singleton."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client


if __name__ == "__main__":
    # Test the client
    from dotenv import load_dotenv
    load_dotenv()
    
    client = get_supabase_client()
    if client.initialize():
        print("✅ Supabase connection successful!")
        
        # Test accuracy fetch
        stats = client.get_accuracy_stats()
        print(f"Accuracy Stats: {stats}")
    else:
        print("❌ Failed to connect to Supabase")
