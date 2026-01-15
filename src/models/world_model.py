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

from src.models.ensemble_model import NBAEnsembleModel
from src.models.live.model import GRUWinProb
# Lazy import vision model to avoid importing heavy packages at module import time
from src.common.hardware import pick_device

logger = logging.getLogger(__name__)

class NBAWorldModel:
    def __init__(self):
        self.device = pick_device("mps")
        self.models_dir = Path("artifacts/models")
        
        # 1. Pregame Ensemble (The "Brain")
        self.ensemble = NBAEnsembleModel()
        
        # 2. Live RNN (The "Pulse")
        self.live_rnn = GRUWinProb().to(self.device)
        self.live_rnn_loaded = False
        
        # 3. Vision CNN (The "Eyes") - lazy loaded to avoid heavy imports on startup
        self.vision_cnn = None
        self.vision_cnn_loaded = False
        
        self.load_models()
        
    def load_models(self):
        """Load all sub-models"""
        logger.info("🌍 Loading World Model components...")
        
        # Load Ensemble
        if self.ensemble.load():
            logger.info("✅ Pregame Ensemble loaded")
        else:
            logger.warning("⚠️ Pregame Ensemble not found")
            
        # Load Live RNN
        rnn_path = self.models_dir / "live_gru_winprob.pt"
        if rnn_path.exists():
            try:
                # Try loading as TorchScript first (as saved in train_gru.py)
                self.live_rnn = torch.jit.load(str(rnn_path), map_location=self.device)
                self.live_rnn_loaded = True
                logger.info("✅ Live RNN loaded")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load Live RNN: {e}")
        else:
            logger.warning("⚠️ Live RNN model file not found")
            
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
        if not self.ensemble.is_trained:
            return pd.DataFrame()
        return self.ensemble.predict_with_probabilities(features)
        
    def predict_live_win_prob(self, sequence: np.ndarray) -> float:
        """
        Get live win probability from RNN
        Args:
            sequence: Numpy array of shape (seq_len, input_size)
        """
        if not self.live_rnn_loaded:
            return 0.5
            
        try:
            with torch.no_grad():
                x = torch.tensor(sequence, dtype=torch.float32).unsqueeze(0).to(self.device)
                prob = self.live_rnn(x).item()
                return prob
        except Exception as e:
            logger.error(f"RNN Prediction error: {e}")
            return 0.5
            
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
