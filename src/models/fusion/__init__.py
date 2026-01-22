"""Fusion module for multi-modal prediction."""
from .learnable_fusion import ExpertFusion, FusionModule, fusion_module

# Maintain alias for backward compatibility if needed, but ExpertFusion is the new standard
GatedFusion = ExpertFusion

__all__ = ['ExpertFusion', 'GatedFusion', 'FusionModule', 'fusion_module']
