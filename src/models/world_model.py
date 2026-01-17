"""
The World Model: A unified system integrating Pregame Ensemble, Live RNN, and Vision CNN.
This is the core "World Class" prediction engine.
"""
import logging
import torch
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

from src.models.pregame.ensemble_predictor import EnsemblePredictor as NBAEnsembleModel
# Lazy import vision model to avoid importing heavy packages at module import time
from src.common.hardware import pick_device

logger = logging.getLogger(__name__)

class NBAWorldModel:
    def __init__(self):
        self.device = pick_device("mps")
        self.models_dir = Path("artifacts/models")
        
        # 1. Pregame Ensemble (The "Brain")
        self.ensemble = NBAEnsembleModel()
        
        # 2. Vision CNN (The "Eyes") - lazy loaded to avoid heavy imports on startup
        self.vision_cnn = None
        self.vision_cnn_loaded = False
        
        self.load_models()
        
    def load_models(self):
        """Load all sub-models"""
        logger.info("🌍 Loading World Model components...")
        
        # Load Ensemble
        try:
            self.ensemble.load_models()
            if self.ensemble.loaded:
                logger.info("✅ Pregame Ensemble loaded")
            else:
                logger.warning("⚠️ Pregame Ensemble not found")
        except Exception as e:
            logger.warning(f"⚠️ Pregame Ensemble loading error: {e}")
            
        # Load Vision CNN (The "Eyes") - using our new VisionModel
        try:
            from src.models.vision import VisionModel
            
            # Try loading our new vision model
            self.vision_cnn = VisionModel()
            if self.vision_cnn.load(use_finetuned=True):
                self.vision_cnn_loaded = True
                logger.info(f"✅ Vision CNN loaded (finetuned: {self.vision_cnn.is_finetuned})")
            else:
                logger.warning("⚠️ Vision CNN failed to load (dependencies may be missing)")
        except ImportError as e:
            logger.warning(f"⚠️ Vision dependencies not available: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Vision CNN loading error: {e}")
            
    def predict_pregame(self, features: pd.DataFrame) -> pd.DataFrame:
        """Get pregame predictions from the ensemble"""
        if not self.ensemble.loaded:
            return pd.DataFrame()
        return self.ensemble.predict(features)
        
    # predict_live_win_prob removed (GRU deprecated)
            
    def analyze_video_clip(self, clip_tensor: torch.Tensor) -> Dict[str, float]:
        """
        Analyze video clip with CNN
        Args:
            clip_tensor: Tensor of shape (C, H, W)
        """
        if not self.vision_cnn_loaded:
            return {}
            
        try:
            with torch.no_grad():
                x = clip_tensor.unsqueeze(0).to(self.device)
                logits = self.vision_cnn(x)
                probs = torch.softmax(logits, dim=1).squeeze().cpu().numpy()
                return {f"class_{i}": float(p) for i, p in enumerate(probs)}
        except Exception as e:
            logger.error(f"CNN Prediction error: {e}")
            return {}

# Global instance
world_model = NBAWorldModel()
