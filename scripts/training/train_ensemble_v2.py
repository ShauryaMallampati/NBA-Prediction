#!/usr/bin/env python3
"""
Train Enhanced Ensemble v2

Uses:
- RunningWorldState for consistent train/test features (55+ features)
- 4 diverse base models (XGBoost, LightGBM, CatBoost, ExtraTrees)
- Stacking meta-learner (Logistic Regression)
- FiveThirtyEight-inspired features (MOV Elo, Pythagorean, SOS)
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.pregame.train_ensemble_v2 import EnsembleTrainerV2, main

if __name__ == "__main__":
    trainer = main()
