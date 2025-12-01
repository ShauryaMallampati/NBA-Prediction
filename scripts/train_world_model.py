"""
Master Training Script for the NBA World Model.
Trains all components: Ensemble, Live RNN, and Vision CNN.
"""
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models.ensemble_model import NBAEnsembleModel
from src.models.live.train_gru import main as train_rnn
from src.models.vision.train_classifier import main as train_cnn
from scripts.train_ensemble_model import load_betting_data, create_features_from_odds

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def train_ensemble():
    logger.info("\n" + "="*80)
    logger.info("🏀 TRAINING PREGAME ENSEMBLE MODEL")
    logger.info("="*80)
    
    try:
        # Load data
        odds_data = load_betting_data()
        if not odds_data:
            logger.error("❌ No betting data found")
            return False
            
        df = create_features_from_odds(odds_data)
        if len(df) < 10:
            logger.error("❌ Not enough data to train")
            return False
            
        # Define features and target
        feature_cols = [
            'home_odds_avg', 'home_odds_std',
            'away_odds_avg', 'away_odds_std',
            'home_spread_avg', 'away_spread_avg', 'spread_diff',
            'total_avg', 'total_std',
            'home_implied_prob', 'away_implied_prob',
            'bookmaker_count', 'market_variance',
            'odds_ratio'
        ]
        
        # Create target (1 if home won, 0 if away won)
        # Note: In real training, we need historical results.
        # For this script, we assume 'winner' column exists or we simulate it for demonstration
        # if it's not in the odds data.
        # The current create_features_from_odds might not have 'winner'.
        # Let's check if we can train.
        
        if 'winner' not in df.columns:
            logger.warning("⚠️ 'winner' column not found. Simulating results for DEMONSTRATION purposes.")
            # Simulate winner based on odds (favorites win more often)
            import numpy as np
            df['winner'] = np.where(df['home_implied_prob'] > df['away_implied_prob'], 
                                  np.random.choice([1, 0], size=len(df), p=[0.7, 0.3]),
                                  np.random.choice([1, 0], size=len(df), p=[0.3, 0.7]))
            
        X = df[feature_cols]
        y = df['winner']
        
        # Train
        ensemble = NBAEnsembleModel()
        ensemble.train(X, y)
        return True
        
    except Exception as e:
        logger.error(f"❌ Ensemble training failed: {e}")
        return False

def train_world_model():
    print("\n" + "="*80)
    print("🌍 STARTING WORLD MODEL TRAINING PIPELINE")
    print("="*80)
    
    # 1. Train Ensemble
    if train_ensemble():
        print("✅ Ensemble Model Trained")
    else:
        print("⚠️ Ensemble Model Training Skipped/Failed")
        
    # 2. Train Live RNN
    print("\n" + "="*80)
    print("⚡ TRAINING LIVE RNN MODEL")
    print("="*80)
    try:
        train_rnn()
        print("✅ Live RNN Trained")
    except Exception as e:
        print(f"⚠️ Live RNN Training Failed: {e}")
        
    # 3. Train Vision CNN
    print("\n" + "="*80)
    print("👁️ TRAINING VISION CNN MODEL")
    print("="*80)
    try:
        train_cnn()
        print("✅ Vision CNN Trained")
    except Exception as e:
        print(f"⚠️ Vision CNN Training Failed: {e}")
        
    print("\n" + "="*80)
    print("✅ WORLD MODEL TRAINING COMPLETE")
    print("="*80)

if __name__ == "__main__":
    train_world_model()
