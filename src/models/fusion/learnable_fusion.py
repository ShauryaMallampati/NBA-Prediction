"""
Learnable fusion module for multi-modal NBA prediction.

Gated attention mechanism that dynamically weights each modality based on context.
Replaces fixed-weight fusion with learned attention over deltas.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ExpertFusion:
    """Deterministic fusion using domain-expert weights."""
    
    def __init__(self, n_modalities: int = 6, weights: Optional[List[float]] = None):
        self.n_modalities = n_modalities
        
        if weights is not None:
            # Use provided custom weights
            self.weights = torch.tensor(weights)
        else:
            # Default Static weights: [Vision, Audio, Flow, Chemistry, Momentum]
            # Defaulting to Aggressive profile if not specified
            self.weights = torch.tensor([0.35, 0.10, 0.10, 0.20, 0.25])
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Apply weighted correction to base probability."""
        base_prob = x[:, 0:1]
        deltas = x[:, 1:]
        
        # Expand weights to match batch size
        w = self.weights.to(x.device).unsqueeze(0).expand(x.size(0), -1)
        correction = torch.sum(deltas * w, dim=1, keepdim=True)
        return base_prob + correction

    def forward_with_floor(self, x: torch.Tensor, min_weight_base: float = 0.01) -> Tuple[torch.Tensor, torch.Tensor]:
        """Weighted correction with floor logic and non-linear veto mitigation."""
        base_prob = x[:, 0:1]
        deltas = x[:, 1:] # [Vis, Aud, Flow, Chem, Mom]
        
        # Expert weights: [Vision, Audio, Flow, Chemistry, Momentum]
        w = self.weights.to(x.device).unsqueeze(0).expand(x.size(0), -1)
        
        # --- NON-LINEAR VETO LOGIC (The "Anti-Slump" Engine) ---
        # If stats say Win (>0.75) but Vision is neutral/negative (delta <= 0), 
        # the model is effectively 'blind' to a fatigue loss. We must amplify the negative delta.
        vis_delta = deltas[:, 0:1]
        
        # Condition 1: Favoring Home heavily but Vision is mediocre
        veto_mask = ((base_prob > 0.75) & (vis_delta < 0.02)).squeeze(-1)
        amplified_deltas = deltas.clone()
        # Triple the impact of negative Vision/Momentum when favorites are 'vibe-checked'
        amplified_deltas[veto_mask, 0] *= 3.0  # Vision
        amplified_deltas[veto_mask, 4] *= 3.0  # Momentum
        
        # Apply dynamic floor based on delta magnitudes
        delta_magnitudes = torch.abs(amplified_deltas)
        boost_factors = torch.ones_like(amplified_deltas) * 2.0
        dynamic_floors = min_weight_base + (delta_magnitudes * boost_factors)
        
        # Use expert weights but respect the floor if deltas are massive
        w_final = torch.max(w, dynamic_floors)
        w_final = w_final / (w_final.sum(dim=-1, keepdim=True) + 1e-6)
        
        correction = torch.sum(amplified_deltas * w_final, dim=1, keepdim=True)
        
        # Final probability calculation
        final_prob = base_prob + correction
        
        # Additional "Panic Dampening" for extreme favorites with zero visual momentum
        # This prevents 85% favorites from staying above 80% if they look like trash on tape.
        panic_mask = ((base_prob > 0.80) & (vis_delta < 0.0)).squeeze(-1)
        final_prob[panic_mask] = (final_prob[panic_mask] + 0.5) / 2.0  # Shrink toward neutral
        
        # Pad for logging: [Base Weight (1.0), Vis, Aud, Flow, Chem, Mom]
        full_weights = torch.cat([torch.ones_like(base_prob), w_final], dim=1)
        
        return final_prob, full_weights

    def predict_proba(self, x: torch.Tensor, use_dynamic_floor: bool = True) -> torch.Tensor:
        if use_dynamic_floor:
            prob, _ = self.forward_with_floor(x)
        else:
            prob = self.forward(x)
        return torch.clamp(prob, 0.0, 1.0)


class FusionModule:
    """
    High-level fusion module using ExpertWeightedFusion.
    
    Handles:
    - Weighted modality fusion
    - MC Dropout simulation (now using perturbation since gate is fixed)
    - Interpretability
    """
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        use_learnable: bool = False, # Force false now
        mc_dropout_samples: int = 50,
        custom_weights: Optional[List[float]] = None,
    ):
        self.use_learnable = False
        self.mc_dropout_samples = mc_dropout_samples
        self.model = ExpertFusion(n_modalities=6, weights=custom_weights)
        self.model_loaded = True
        
        weight_str = ", ".join([f"{w:.2f}" for w in self.model.weights.tolist()])
        logger.info(f"✅ Expert-Weighted Fusion Architecture initialized (Determinism Enabled)")
        logger.info(f"   ⚖️ Weights: [{weight_str}]")
    
    def fuse(
        self,
        base_prob: float,
        vision_delta: float = 0.0,
        audio_delta: float = 0.0,
        flow_delta: float = 0.0,
        chemistry_delta: float = 0.0,
        momentum_delta: float = 0.0,
    ) -> float:
        """Fuse modality outputs into final probability."""
        x = torch.tensor([
            base_prob, vision_delta, audio_delta, flow_delta, chemistry_delta, momentum_delta
        ], dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            prob = self.model.predict_proba(x, use_dynamic_floor=True).item()
        
        return float(np.clip(prob, 0.05, 0.95))
    
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
        Since the weights are now fixed, 'Uncertainty' represents the sensitivity 
        to small fluctuations in modality inputs (Monte Carlo Perturbation).
        """
        x_base = torch.tensor([
            base_prob, vision_delta, audio_delta, flow_delta, chemistry_delta, momentum_delta
        ], dtype=torch.float32).unsqueeze(0)
        
        predictions = []
        for _ in range(self.mc_dropout_samples):
            # Perturb deltas slightly to estimate sensitivity
            noise = torch.randn_like(x_base[:, 1:]) * 0.005 
            x_noisy = x_base.clone()
            x_noisy[:, 1:] += noise
            
            with torch.no_grad():
                prob = self.model.predict_proba(x_noisy, use_dynamic_floor=True).item()
                predictions.append(prob)
        
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
        """Provides weights used for this specific fusion instance."""
        x = torch.tensor([
            base_prob, vision_delta, audio_delta, flow_delta, chemistry_delta, momentum_delta
        ], dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            _, weights = self.model.forward_with_floor(x)
            w = weights.squeeze().numpy()
        
        return {
            "ensemble": float(w[0]),
            "vision": float(w[1]),
            "audio": float(w[2]),
            "optical_flow": float(w[3]),
            "chemistry": float(w[4]),
            "momentum": float(w[5]),
        }


# Global instance
fusion_module = FusionModule()
