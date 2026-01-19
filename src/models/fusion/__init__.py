"""Fusion module for multi-modal prediction."""
from .learnable_fusion import GatedFusion, FusionModule, fusion_module

__all__ = ['GatedFusion', 'FusionModule', 'fusion_module']
