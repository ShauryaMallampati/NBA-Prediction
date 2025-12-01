"""
Automated Training Pipeline
Continuously collects new data and retrains the ensemble model
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import logging
import pandas as pd
import time
from datetime import datetime
import schedule
import json

from scripts.collect_working_data import collect_working_endpoints_data
from scripts.train_ensemble_model import (
    load_betting_data,
    create_features_from_odds,
    create_synthetic_labels
)
from src.models.ensemble_model import NBAEnsembleModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutoTrainingPipeline:
    """Automated pipeline for continuous model retraining"""
    
    def __init__(
        self,
        collection_interval_hours: int = 6,
        retraining_interval_hours: int = 24,
        min_new_games: int = 5
    ):
        """
        Initialize auto-training pipeline
        
        Args:
            collection_interval_hours: How often to collect new data
            retraining_interval_hours: How often to retrain models
            min_new_games: Minimum new games before retraining
        """
        self.collection_interval = collection_interval_hours
        self.retraining_interval = retraining_interval_hours
        self.min_new_games = min_new_games
        
        self.ensemble = NBAEnsembleModel()
        self.last_training_size = 0
        self.training_history = []
        
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
    
    def collect_new_data(self):
        """Collect new betting odds data"""
        logger.info("="*80)
        logger.info("📥 COLLECTING NEW DATA")
        logger.info("="*80)
        
        try:
            # Collect from working endpoints
            collect_working_endpoints_data()
            logger.info("✅ Data collection complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error collecting data: {e}")
            return False
    
    def check_for_new_data(self) -> int:
        """
        Check how many new games are available
        
        Returns:
            Number of new games since last training
        """
        try:
            data = load_betting_data()
            if not data:
                return 0
            
            df = create_features_from_odds(data)
            current_size = len(df)
            new_games = current_size - self.last_training_size
            
            logger.info(f"📊 Current games: {current_size}, New games: {new_games}")
            
            return new_games
            
        except Exception as e:
            logger.error(f"❌ Error checking data: {e}")
            return 0
    
    def retrain_model(self):
        """Retrain the ensemble model with latest data"""
        logger.info("="*80)
        logger.info("🔄 RETRAINING ENSEMBLE MODEL")
        logger.info("="*80)
        
        try:
            # Load latest data
            data = load_betting_data()
            if not data:
                logger.error("❌ No data available for training")
                return False
            
            # Create features
            df = create_features_from_odds(data)
            
            if len(df) == 0:
                logger.error("❌ No features created")
                return False
            
            logger.info(f"📊 Training on {len(df)} games")
            
            # Create labels
            y = create_synthetic_labels(df)
            
            # Select features
            feature_cols = [
                'home_odds_avg', 'home_odds_std',
                'away_odds_avg', 'away_odds_std',
                'home_spread_avg', 'away_spread_avg', 'spread_diff',
                'total_avg', 'total_std',
                'home_implied_prob', 'away_implied_prob',
                'bookmaker_count', 'market_variance',
                'odds_ratio'
            ]
            
            X = df[feature_cols]
            
            # Train ensemble
            results = self.ensemble.train(X, y, use_stacking=False)
            
            # Update tracking
            self.last_training_size = len(df)
            
            # Record training history
            training_record = {
                'timestamp': datetime.now().isoformat(),
                'num_games': len(df),
                'num_features': len(feature_cols),
                'best_accuracy': max(results.values()),
                'model_results': results
            }
            
            self.training_history.append(training_record)
            
            # Save training history
            with open('models/ensemble/training_history.json', 'w') as f:
                json.dump(self.training_history, f, indent=2)
            
            logger.info("✅ Retraining complete")
            logger.info(f"🎯 Best accuracy: {max(results.values()):.4f}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error retraining model: {e}")
            return False
    
    def run_training_cycle(self):
        """Run a complete training cycle"""
        logger.info("\n" + "="*80)
        logger.info(f"🔄 TRAINING CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)
        
        # Check for new data
        new_games = self.check_for_new_data()
        
        if new_games >= self.min_new_games:
            logger.info(f"✅ {new_games} new games available - triggering retraining")
            self.retrain_model()
        else:
            logger.info(f"⏸️  Only {new_games} new games - waiting for {self.min_new_games} minimum")
    
    def run_collection_cycle(self):
        """Run a data collection cycle"""
        logger.info("\n" + "="*80)
        logger.info(f"📥 COLLECTION CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)
        
        self.collect_new_data()
    
    def start(self, run_immediately: bool = True):
        """
        Start the automated pipeline
        
        Args:
            run_immediately: Run initial collection and training
        """
        logger.info("="*80)
        logger.info("🚀 STARTING AUTOMATED TRAINING PIPELINE")
        logger.info("="*80)
        logger.info(f"📥 Data collection: Every {self.collection_interval} hours")
        logger.info(f"🔄 Model retraining: Every {self.retraining_interval} hours")
        logger.info(f"📊 Minimum new games: {self.min_new_games}")
        
        # Run immediately if requested
        if run_immediately:
            logger.info("\n🚀 Running initial collection and training...")
            self.collect_new_data()
            self.retrain_model()
        
        # Schedule regular collection
        schedule.every(self.collection_interval).hours.do(self.run_collection_cycle)
        
        # Schedule regular training
        schedule.every(self.retraining_interval).hours.do(self.run_training_cycle)
        
        logger.info("\n✅ Pipeline started - running continuously...")
        logger.info("Press Ctrl+C to stop\n")
        
        # Run scheduled jobs
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("\n⏸️  Pipeline stopped by user")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='NBA Ensemble Model Auto-Training Pipeline'
    )
    parser.add_argument(
        '--collection-interval',
        type=int,
        default=6,
        help='Hours between data collection (default: 6)'
    )
    parser.add_argument(
        '--training-interval',
        type=int,
        default=24,
        help='Hours between model retraining (default: 24)'
    )
    parser.add_argument(
        '--min-games',
        type=int,
        default=5,
        help='Minimum new games before retraining (default: 5)'
    )
    parser.add_argument(
        '--no-immediate',
        action='store_true',
        help='Skip immediate training on startup'
    )
    
    args = parser.parse_args()
    
    # Create pipeline
    pipeline = AutoTrainingPipeline(
        collection_interval_hours=args.collection_interval,
        retraining_interval_hours=args.training_interval,
        min_new_games=args.min_games
    )
    
    # Start pipeline
    pipeline.start(run_immediately=not args.no_immediate)


if __name__ == "__main__":
    main()
