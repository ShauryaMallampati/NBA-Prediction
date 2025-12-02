"""
Automated Agent - Runs daily to:
1. Make predictions for today's games (9 AM)
2. Validate yesterday's predictions (1 AM)
3. Collect new games for training
4. Retrain models weekly
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import schedule
import time
from datetime import datetime
import logging
import subprocess

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/automated_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedAgent:
    """Automated agent for predictions, validation, and training"""
    
    def __init__(self):
        Path("logs").mkdir(exist_ok=True)
        
    def make_predictions(self):
        """Run prediction script for today's games"""
        logger.info("🎯 Starting prediction job...")
        try:
            result = subprocess.run(
                ['python', 'scripts/predict_today.py'],
                capture_output=True,
                text=True
            )
            logger.info(result.stdout)
            if result.returncode != 0:
                logger.error(f"Prediction failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Failed to run predictions: {e}")
    
    def validate_predictions(self):
        """Validate yesterday's predictions"""
        logger.info("🔍 Starting validation job...")
        try:
            result = subprocess.run(
                ['python', 'scripts/validate_predictions.py'],
                capture_output=True,
                text=True
            )
            logger.info(result.stdout)
            if result.returncode != 0:
                logger.error(f"Validation failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Failed to run validation: {e}")
    
    def collect_new_games(self):
        """Collect new games for training"""
        logger.info("📊 Collecting new games...")
        try:
            result = subprocess.run(
                ['python', 'scripts/collect_200_games.py'],
                capture_output=True,
                text=True
            )
            logger.info(result.stdout)
            if result.returncode != 0:
                logger.error(f"Collection failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Failed to collect games: {e}")
    
    def retrain_models(self):
        """Retrain models with new data"""
        logger.info("🎓 Retraining models...")
        try:
            result = subprocess.run(
                ['python', 'scripts/train_final.py'],
                capture_output=True,
                text=True
            )
            logger.info(result.stdout)
            if result.returncode != 0:
                logger.error(f"Training failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Failed to retrain models: {e}")
    
    def run_scheduled_jobs(self):
        """Set up scheduled jobs"""
        logger.info("🤖 Automated Agent Starting...")
        logger.info("📅 Scheduling jobs:")
        logger.info("  - Predictions: Daily at 9:00 AM")
        logger.info("  - Validation: Daily at 1:00 AM")
        logger.info("  - Collect Games: Weekly on Monday at 2:00 AM")
        logger.info("  - Retrain Models: Weekly on Monday at 3:00 AM")
        
        # Daily predictions at 9 AM (before games start)
        schedule.every().day.at("09:00").do(self.make_predictions)
        
        # Daily validation at 1 AM (after all games finished)
        schedule.every().day.at("01:00").do(self.validate_predictions)
        
        # Weekly data collection on Monday at 2 AM
        schedule.every().monday.at("02:00").do(self.collect_new_games)
        
        # Weekly retraining on Monday at 3 AM (after collection)
        schedule.every().monday.at("03:00").do(self.retrain_models)
        
        logger.info("✅ Agent is running. Press Ctrl+C to stop.\n")
        
        # Run forever
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    print("=" * 80)
    print("🤖 AUTOMATED NBA PREDICTION AGENT")
    print("=" * 80)
    print("\n📅 Schedule:")
    print("  ⏰ 09:00 AM - Make predictions for today's games")
    print("  ⏰ 01:00 AM - Validate yesterday's predictions")
    print("  ⏰ 02:00 AM Monday - Collect new games")
    print("  ⏰ 03:00 AM Monday - Retrain models")
    print("\n🚀 Starting automated agent...\n")
    
    agent = AutomatedAgent()
    
    try:
        agent.run_scheduled_jobs()
    except KeyboardInterrupt:
        print("\n\n🛑 Agent stopped by user")
        logger.info("Agent stopped by user")

if __name__ == "__main__":
    main()
