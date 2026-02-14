"""
"""Explain why the model makes each prediction using SHAP.

Instead of just saying "Lakers 65% to win", we can show you exactly
why - which features pushed the prediction that way.
"""

import shap
import numpy as np
import pandas as pd
import pickle
import json
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class SHAPExplainer:
    """Break down predictions so you understand what's driving them."""
    
    def __init__(self, model_dir: str = "artifacts/models/pregame"):
        self.model_dir = Path(model_dir)
        self.explainer = None
        self.feature_names = []
        self._load_model()
    
    async def load_async(self):
        """Async version of model loading for SHAP."""
        import asyncio
        try:
            xgb_path = self.model_dir / "xgb_model.pkl"
            metadata_path = self.model_dir / "ensemble_metadata.json"
            
            async def read_pickle(path):
                with open(path, 'rb') as f:
                    return pickle.load(f)
            
            async def read_json(path):
                with open(path, 'r') as f:
                    return json.load(f)

            if xgb_path.exists():
                model = await asyncio.to_thread(read_pickle, xgb_path)
                base_model = model.estimators_[0].estimator if hasattr(model, 'estimators_') else model
                self.explainer = await asyncio.to_thread(shap.TreeExplainer, base_model)
                logger.info("✅ SHAP explainer initialized async")
            
            if metadata_path.exists():
                metadata = await asyncio.to_thread(read_json, metadata_path)
                self.feature_names = metadata.get('feature_names', [])
        except Exception as e:
            logger.error(f"Failed to initialize SHAP explainer async: {e}")

    def _load_model(self):
        """Load the XGBoost model for SHAP analysis (sync)."""
        try:
            xgb_path = self.model_dir / "xgb_model.pkl"
            metadata_path = self.model_dir / "ensemble_metadata.json"
            
            if xgb_path.exists():
                with open(xgb_path, 'rb') as f:
                    model = pickle.load(f)
                    # CalibratedClassifierCV wraps the actual model
                    base_model = model.estimators_[0].estimator if hasattr(model, 'estimators_') else model
                    self.explainer = shap.TreeExplainer(base_model)
                    logger.info("✅ SHAP explainer initialized with XGBoost model")
            
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    self.feature_names = metadata.get('feature_names', [])
                    
        except Exception as e:
            logger.error(f"Failed to initialize SHAP explainer: {e}")
            self.explainer = None
    
    def explain_prediction(self, features: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate SHAP explanation for a single prediction.
        
        Args:
            features: DataFrame with feature values
            
        Returns:
            Dictionary with SHAP values and top contributing features
        """
        if self.explainer is None:
            return {"error": "SHAP explainer not initialized"}
        
        try:
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(features)
            
            # Handle multi-class output
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Class 1 = home win
            
            # Get feature importance for this prediction
            feature_importance = []
            for i, fname in enumerate(self.feature_names[:len(shap_values[0])]):
                importance = float(shap_values[0][i])
                feature_importance.append({
                    "feature": fname,
                    "shap_value": round(importance, 4),
                    "impact": "positive" if importance > 0 else "negative",
                    "contribution": f"{abs(importance)*100:.1f}%"
                })
            
            # Sort by absolute impact
            feature_importance.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
            
            # Top 5 most impactful features
            top_5 = feature_importance[:5]
            
            # Generate human-readable explanation
            explanation = self._generate_explanation(top_5)
            
            return {
                "top_features": top_5,
                "all_features": feature_importance,
                "explanation": explanation,
                "base_value": float(self.explainer.expected_value) if hasattr(self.explainer, 'expected_value') else 0.5
            }
            
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            return {"error": str(e)}
    
    def _generate_explanation(self, top_features: List[Dict]) -> str:
        """Generate a human-readable explanation from SHAP values."""
        if not top_features:
            return "Unable to generate explanation."
        
        positive = [f for f in top_features if f["impact"] == "positive"]
        negative = [f for f in top_features if f["impact"] == "negative"]
        
        parts = []
        
        if positive:
            pos_names = ", ".join([f["feature"].replace("_", " ") for f in positive[:2]])
            parts.append(f"Key factors favoring home team: {pos_names}")
        
        if negative:
            neg_names = ", ".join([f["feature"].replace("_", " ") for f in negative[:2]])
            parts.append(f"Key factors against: {neg_names}")
        
        return ". ".join(parts) if parts else "Balanced prediction based on multiple factors."


# Global instance
shap_explainer = SHAPExplainer()
