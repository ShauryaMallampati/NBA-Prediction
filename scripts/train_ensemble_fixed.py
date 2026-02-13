#!/usr/bin/env python3
"""
🎯 TRAIN FIXED ENSEMBLE (with proper feature engineering)
=========================================================

This script trains the ensemble model WITH proper feature engineering:
- Elo ratings (computed progressively, no leakage)
- Rest features (days since last game)
- Win/loss streaks
- Rolling averages (last 5/10 games)

All features are computed from PAST data only (no data leakage).

Usage:
    poetry run python scripts/train_ensemble_fixed.py

Output:
    artifacts/models/pregame_fixed/
        - xgb_model.pkl
        - lgb_model.pkl
        - cat_model.pkl
        - ensemble_metadata.json
"""

import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.pregame.train_ensemble import EnsembleTrainer
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 70)
    logger.info("🎯 TRAINING FIXED ENSEMBLE (with feature engineering)")
    logger.info("=" * 70)
    
    # Create output directory for fixed model
    output_dir = "artifacts/models/pregame_fixed"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize trainer
    trainer = EnsembleTrainer(output_dir=output_dir)
    
    # Load and prepare data (this now computes features!)
    logger.info("\n📊 Loading data and computing features...")
    X, y = trainer.load_data("data/nba_games_enhanced.csv")
    
    logger.info(f"\n✅ Features computed:")
    logger.info(f"   Total features: {len(trainer.feature_names)}")
    logger.info(f"   Feature names: {trainer.feature_names[:20]}...")
    
    # Train models
    logger.info("\n🌳 Training XGBoost...")
    xgb_metrics = trainer.train_xgboost(X, y)
    
    logger.info("\n🌲 Training LightGBM...")
    lgb_metrics = trainer.train_lightgbm(X, y)
    
    logger.info("\n🐱 Training CatBoost...")
    cat_metrics = trainer.train_catboost(X, y)
    
    # Save models
    logger.info("\n💾 Saving models...")
    trainer.save_models()
    
    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("✅ FIXED ENSEMBLE TRAINING COMPLETE")
    logger.info("=" * 70)
    logger.info(f"   Output dir: {output_dir}")
    logger.info(f"   Features:   {len(trainer.feature_names)}")
    logger.info(f"   XGBoost CV: {xgb_metrics.get('accuracy', 0):.1%}")
    logger.info(f"   LightGBM CV: {lgb_metrics.get('accuracy', 0):.1%}")
    logger.info(f"   CatBoost CV: {cat_metrics.get('accuracy', 0):.1%}")
    logger.info("=" * 70)
    
    # Compare to baseline
    logger.info("\n📈 Expected improvement:")
    logger.info("   Old (no features): ~58%")
    logger.info("   New (with features): ~65%+ (should match Elo baseline)")
    logger.info("   Full model (+ modalities): ~71%+ target")


if __name__ == "__main__":
    main()
