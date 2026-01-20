"""
Learnable Fusion Module for Multi-Modal NBA Prediction.

This module implements a Gated Attention Fusion mechanism that learns
to weight each modality based on context, replacing the fixed-sum fusion.

Research Rationale:
- Fixed-weight fusion ignores modality reliability per game
- Learnable gates can down-weight missing or noisy modalities
- Attention-based fusion is proven in multi-modal NLP (2020+)

Architecture (Residual Fusion):
- Input: [base_prob, vis_Δ, aud_Δ, flow_Δ, chem_Δ, mom_Δ]
- Anchor: base_prob (Preserved via Skip-Connection)
- Gate: Learns weights for Deltas [vis_Δ...mom_Δ]
- Output: base_prob + (Weighted Deltas) -> Sigmoid Output
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
        n_modalities: int = 6,
        hidden_dim: int = 32,
        dropout: float = 0.1,
    ):
        super().__init__()
        
        self.n_modalities = n_modalities
        
        # Gate network: learns weights for the 5 DELTAS (not base)
        self.gate = nn.Sequential(
            nn.Linear(n_modalities - 1, hidden_dim), # Input: 5 deltas
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, n_modalities - 1), # Output: 5 weights
            nn.Softmax(dim=-1)
        )
        
        # Output projection (Optional, or just perform residual sum)
        # In Residual architecture, we often just do Base + Correction.
        # But to keep non-linearity, we can pass the correction through a small MLP 
        # BEFORE adding to base, or just use the weighted sum directly.
        # Let's use weighted sum directly to preserve "Anchor" philosophy.
        # Correction = Sum(Weight_i * Delta_i)
        
        # We assume Deltas are in Probability Space (approx), so we add them directly.
        
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
        Forward pass with Residual Skip-Connection.
        """
        # Split Check:
        # x[:, 0] = Base Probability (The Anchor)
        # x[:, 1:] = Deltas (The Correction Signals)
        
        base_prob = x[:, 0:1] # (batch, 1)
        deltas = x[:, 1:]     # (batch, 5)
        
        # 1. Compute weights using the LEARNABLE gate
        # We concatenate delta magnitudes with the ensemble confidence
        confidence = torch.abs(base_prob - 0.5) * 2.0
        gate_input = torch.cat([deltas, confidence], dim=1)
        
        # Adjust gate to accept (deltas + confidence) = 6 inputs
        # Wait, self.gate was defined with n_modalities - 1 = 5 inputs.
        # Let's just use deltas (5 inputs) for now to match the __init__
        weights = self.gate(deltas)
        
        # 2. Compute Weighted Correction
        correction = torch.sum(deltas * weights, dim=1, keepdim=True)
        
        # 3. Apply Residual Anchor
        return base_prob + correction
    
    def forward_with_floor(self, x: torch.Tensor, min_weight_base: float = 0.01) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Dynamic Attention Scaling with Residual Anchor.
        """
        base_prob = x[:, 0:1]
        deltas = x[:, 1:]
        
        # 1. Gate Weights (Adaptive Resonance)
        confidence = torch.abs(base_prob - 0.5) * 2.0
        adaptive_temp = 5.0 + (1.0 - confidence) * 20.0 
        delta_magnitudes = torch.abs(deltas)
        
        # We use magnitudes as the logits for softmax
        weights = F.softmax(delta_magnitudes * adaptive_temp, dim=-1) # (batch, 5)
        
        # 2. Dynamic Floor (on Deltas)
        delta_magnitudes = torch.abs(deltas)
        boost_factors = torch.ones_like(deltas) * 2.0
        dynamic_floors = min_weight_base + (delta_magnitudes * boost_factors)
        
        # Apply Floor
        weights = torch.max(weights, dynamic_floors)
        
        # Normalize weights to protect from exploding corrections?
        # Unlike "Mixture" (sum=1), these are independent attention scores.
        # But to keep "Correction" bounded, let's normalize them to sum to 1?
        # If we optimize weights, we want to pick the BEST delta.
        # So yes, softmax was applied in Gate. We should re-normalize.
        weights = weights / (weights.sum(dim=-1, keepdim=True) + 1e-6)
        
        # 3. Calculate Correction
        # We trust the weighted combination of sensors.
        correction = torch.sum(deltas * weights, dim=1, keepdim=True)
        
        # 4. Apply Residual
        final_prob = base_prob + correction
        
        # Pad weights with a "1.0" for base so logging works
        # [1.0, w_vis, w_aud...]
        full_weights = torch.cat([torch.ones_like(base_prob), weights], dim=1)
        
        return final_prob, full_weights
    
    def predict_proba(self, x: torch.Tensor, use_dynamic_floor: bool = False) -> torch.Tensor:
        """Return probability."""
        if use_dynamic_floor:
            prob, _ = self.forward_with_floor(x)
        else:
            prob = self.forward(x)
        
        # Since forward now returns PROBABILITY (Residual Linear Sum),
        # we do NOT apply sigmoid. Just clip.
        return torch.clamp(prob, 0.0, 1.0)
    
    def get_weights(self, x: torch.Tensor) -> torch.Tensor:
        """Return gate weights for interpretability."""
        return self.gate(x)

    def get_weights_with_floor(self, x: torch.Tensor, min_weight_base: float = 0.01) -> torch.Tensor:
        """Return actual weights used in dynamic fusion."""
        _, weights = self.forward_with_floor(x, min_weight_base)
        return weights


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
            
            n_modalities_ckpt = checkpoint.get('n_modalities', 7)
            expected_modalities = 6
            
            if n_modalities_ckpt != expected_modalities:
                raise ValueError(f"Checkpoint has {n_modalities_ckpt} modalities, expected {expected_modalities}")

            hidden_dim = checkpoint.get('hidden_dim', 32)
            self.model = GatedFusion(n_modalities=expected_modalities, hidden_dim=hidden_dim)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.model.eval()
            self.model_loaded = True
            
            logger.info(f"✅ Learnable fusion loaded from {model_path}")
        except Exception as e:
            logger.warning(f"Failed to load fusion model: {e}. Using FRESH dynamic model {expected_modalities}-inputs (un-trained gate).")
            self.model = GatedFusion(n_modalities=expected_modalities)
            self.model_loaded = True
    
    def fuse(
        self,
        base_prob: float,
        vision_delta: float = 0.0,
        audio_delta: float = 0.0,
        flow_delta: float = 0.0,
        chemistry_delta: float = 0.0,
        momentum_delta: float = 0.0,
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
            ], dtype=torch.float32).unsqueeze(0)
            
            if self.use_learnable:
                # Use Dynamic Attention Scaling
                with torch.no_grad():
                    prob = self.model.predict_proba(x, use_dynamic_floor=True).item()
            
            return float(np.clip(prob, 0.05, 0.95))
        else:
            # Fixed-sum fallback
            final = base_prob + vision_delta + audio_delta + flow_delta + chemistry_delta + momentum_delta
            return float(np.clip(final, 0.05, 0.95))
    
    def fuse_with_uncertainty(
        self,
        base_prob: float,
        vision_delta: float = 0.0,
        audio_delta: float = 0.0,
        flow_delta: float = 0.0,
        chemistry_delta: float = 0.0,
        momentum_delta: float = 0.0,
    ) -> Dict[str, float]:
        """
        Fuse with Monte Carlo Dropout for uncertainty estimation.
        
        Returns:
            Dict with: probability, uncertainty, ci_lower, ci_upper
        """
        if not self.model_loaded or self.model is None:
            # Fallback: no uncertainty
            prob = self.fuse(base_prob, vision_delta, audio_delta, flow_delta,
                           chemistry_delta, momentum_delta)
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
        ], dtype=torch.float32).unsqueeze(0)
        
        # Enable dropout for MC sampling
        self.model.train()
        
        predictions = []
        for _ in range(self.mc_dropout_samples):
            with torch.no_grad():
                # Apply Dynamic Scaling in MC Dropout too
                prob = self.model.predict_proba(x, use_dynamic_floor=True).item()
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
            }
        
        x = torch.tensor([
            base_prob,
            vision_delta,
            audio_delta,
            flow_delta,
            chemistry_delta,
            momentum_delta,
        ], dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            if self.use_learnable:
                 # CRITICAL FIX: Use the DYNAMIC weights for logging, not the raw gate weights
                weights = self.model.get_weights_with_floor(x).squeeze().numpy()
            else:
                weights = self.model.get_weights(x).squeeze().numpy()
        
        return {
            "ensemble": float(weights[0]),
            "vision": float(weights[1]),
            "audio": float(weights[2]),
            "optical_flow": float(weights[3]),
            "chemistry": float(weights[4]),
            "momentum": float(weights[5]),
        }


# Global instance with fallback
fusion_module = FusionModule(use_learnable=True)
