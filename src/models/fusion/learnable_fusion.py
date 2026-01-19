"""
Learnable Fusion Module for Multi-Modal NBA Prediction.

This module implements a Gated Attention Fusion mechanism that learns
to weight each modality based on context, replacing the fixed-sum fusion.

Research Rationale:
- Fixed-weight fusion ignores modality reliability per game
- Learnable gates can down-weight missing or noisy modalities
- Attention-based fusion is proven in multi-modal NLP (2020+)

Architecture:
- Input: [base_prob, vis_Δ, aud_Δ, flow_Δ, chem_Δ, mom_Δ, pbp_Δ]
- Gate network: MLP → Softmax weights
- Output: Weighted combination → Sigmoid → P(home_win)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class GatedFusion(nn.Module):
    """
    Gated Mixture-of-Experts style fusion.
    
    Learns to weight each modality based on its input values.
    Missing modalities (set to 0) are automatically down-weighted.
    """
    
    def __init__(
        self,
        n_modalities: int = 7,
        hidden_dim: int = 32,
        dropout: float = 0.1,
    ):
        super().__init__()
        
        self.n_modalities = n_modalities
        
        # Gate network: learns modality weights
        self.gate = nn.Sequential(
            nn.Linear(n_modalities, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, n_modalities),
            nn.Softmax(dim=-1)
        )
        
        # Output projection: combines weighted modalities
        self.output = nn.Sequential(
            nn.Linear(n_modalities, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )
        
        # Initialize weights
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights with small values."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Tensor of shape (batch, n_modalities)
               Expected order: [base_prob, vis_Δ, aud_Δ, flow_Δ, chem_Δ, mom_Δ, pbp_Δ]
               
        Returns:
            Tensor of shape (batch, 1) with probability in [0, 1]
        """
        # Compute attention weights
        weights = self.gate(x)  # (batch, n_modalities)
        
        # Apply weights (element-wise)
        weighted = x * weights  # (batch, n_modalities)
        
        # Compute output
        logits = self.output(weighted)  # (batch, 1)
        
        return logits
    
    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Return probability (sigmoid applied)."""
        logits = self.forward(x)
        return torch.sigmoid(logits)
    
    def get_weights(self, x: torch.Tensor) -> torch.Tensor:
        """Return gate weights for interpretability."""
        return self.gate(x)


class FusionModule:
    """
    High-level fusion module wrapping GatedFusion for inference.
    
    Handles:
    - Loading pretrained weights
    - Fixed-sum fallback when model unavailable
    - MC Dropout for uncertainty quantification
    """
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        use_learnable: bool = True,
        mc_dropout_samples: int = 50,
    ):
        self.use_learnable = use_learnable
        self.mc_dropout_samples = mc_dropout_samples
        self.model = None
        self.model_loaded = False
        
        if model_path is None:
            model_path = Path("artifacts/models/fusion/gated_fusion.pt")
        
        if use_learnable and model_path.exists():
            self._load_model(model_path)
    
    def _load_model(self, model_path: Path):
        """Load pretrained fusion model."""
        try:
            checkpoint = torch.load(model_path, map_location='cpu')
            
            n_modalities = checkpoint.get('n_modalities', 7)
            self.model = GatedFusion(n_modalities=n_modalities)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()
            self.model_loaded = True
            
            logger.info(f"✅ Learnable fusion loaded from {model_path}")
        except Exception as e:
            logger.warning(f"Failed to load fusion model: {e}. Using fixed-sum fallback.")
            self.model_loaded = False
    
    def fuse(
        self,
        base_prob: float,
        vision_delta: float = 0.0,
        audio_delta: float = 0.0,
        flow_delta: float = 0.0,
        chemistry_delta: float = 0.0,
        momentum_delta: float = 0.0,
        pbp_delta: float = 0.0,
    ) -> float:
        """
        Fuse modality outputs into final probability.
        
        Args:
            base_prob: Base probability from ensemble [0, 1]
            *_delta: Deltas from each modality [-0.1, 0.1]
            
        Returns:
            Final probability [0.05, 0.95]
        """
        if self.model_loaded and self.model is not None:
            # Learnable fusion
            x = torch.tensor([
                base_prob,
                vision_delta,
                audio_delta,
                flow_delta,
                chemistry_delta,
                momentum_delta,
                pbp_delta,
            ], dtype=torch.float32).unsqueeze(0)
            
            with torch.no_grad():
                prob = self.model.predict_proba(x).item()
            
            return float(np.clip(prob, 0.05, 0.95))
        else:
            # Fixed-sum fallback
            final = base_prob + vision_delta + audio_delta + flow_delta + chemistry_delta + momentum_delta + pbp_delta
            return float(np.clip(final, 0.05, 0.95))
    
    def fuse_with_uncertainty(
        self,
        base_prob: float,
        vision_delta: float = 0.0,
        audio_delta: float = 0.0,
        flow_delta: float = 0.0,
        chemistry_delta: float = 0.0,
        momentum_delta: float = 0.0,
        pbp_delta: float = 0.0,
    ) -> Dict[str, float]:
        """
        Fuse with Monte Carlo Dropout for uncertainty estimation.
        
        Returns:
            Dict with: probability, uncertainty, ci_lower, ci_upper
        """
        if not self.model_loaded or self.model is None:
            # Fallback: no uncertainty
            prob = self.fuse(base_prob, vision_delta, audio_delta, flow_delta,
                           chemistry_delta, momentum_delta, pbp_delta)
            return {
                "probability": prob,
                "uncertainty": 0.0,
                "ci_lower": prob,
                "ci_upper": prob,
            }
        
        x = torch.tensor([
            base_prob,
            vision_delta,
            audio_delta,
            flow_delta,
            chemistry_delta,
            momentum_delta,
            pbp_delta,
        ], dtype=torch.float32).unsqueeze(0)
        
        # Enable dropout for MC sampling
        self.model.train()
        
        predictions = []
        for _ in range(self.mc_dropout_samples):
            with torch.no_grad():
                prob = self.model.predict_proba(x).item()
                predictions.append(prob)
        
        # Disable dropout
        self.model.eval()
        
        mean_prob = float(np.mean(predictions))
        std_prob = float(np.std(predictions))
        ci_lower = float(np.percentile(predictions, 2.5))
        ci_upper = float(np.percentile(predictions, 97.5))
        
        return {
            "probability": np.clip(mean_prob, 0.05, 0.95),
            "uncertainty": std_prob,
            "ci_lower": np.clip(ci_lower, 0.05, 0.95),
            "ci_upper": np.clip(ci_upper, 0.05, 0.95),
        }
    
    def get_modality_weights(
        self,
        base_prob: float,
        vision_delta: float = 0.0,
        audio_delta: float = 0.0,
        flow_delta: float = 0.0,
        chemistry_delta: float = 0.0,
        momentum_delta: float = 0.0,
        pbp_delta: float = 0.0,
    ) -> Dict[str, float]:
        """
        Get learned weights for each modality (for interpretability).
        
        Returns:
            Dict mapping modality name to weight [0, 1]
        """
        if not self.model_loaded or self.model is None:
            # Fixed weights fallback
            return {
                "ensemble": 1.0,
                "vision": 0.15,
                "audio": 0.10,
                "optical_flow": 0.08,
                "chemistry": 0.10,
                "momentum": 0.12,
                "pbp": 0.05,
            }
        
        x = torch.tensor([
            base_prob,
            vision_delta,
            audio_delta,
            flow_delta,
            chemistry_delta,
            momentum_delta,
            pbp_delta,
        ], dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            weights = self.model.get_weights(x).squeeze().numpy()
        
        return {
            "ensemble": float(weights[0]),
            "vision": float(weights[1]),
            "audio": float(weights[2]),
            "optical_flow": float(weights[3]),
            "chemistry": float(weights[4]),
            "momentum": float(weights[5]),
            "pbp": float(weights[6]),
        }


# Global instance with fallback
fusion_module = FusionModule(use_learnable=True)
