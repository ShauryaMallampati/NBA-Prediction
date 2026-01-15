"""
Vision CNN Model for NBA Video Analysis

Uses pre-trained VideoMAE or TimeSformer to extract features from NBA game footage.
Designed to work with minimal local storage by using HuggingFace's model hub.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import numpy as np

logger = logging.getLogger(__name__)

# Model paths
VISION_MODEL_DIR = Path("artifacts/models/vision")
FINETUNED_MODEL_PATH = VISION_MODEL_DIR / "finetuned_vision_model.pt"


class VisionModel:
    """
    Pre-trained video feature extractor for NBA game analysis.
    
    Uses VideoMAE (Video Masked Autoencoders) pre-trained on Kinetics-400,
    which includes sports activities and transfers well to basketball.
    """
    
    def __init__(self, model_name: str = "MCG-NJU/videomae-base"):
        """
        Initialize the Vision model.
        
        Args:
            model_name: HuggingFace model identifier
                - "MCG-NJU/videomae-base" (default, 87M params)
                - "MCG-NJU/videomae-large" (304M params, better but slower)
                - "facebook/timesformer-base-finetuned-k400" (TimeSformer alternative)
        """
        self.model_name = model_name
        self.model = None
        self.processor = None
        self.device = None
        self._loaded = False
        self._finetuned = False
        
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._loaded
    
    @property
    def is_finetuned(self) -> bool:
        """Check if using finetuned model."""
        return self._finetuned
        
    def load(self, use_finetuned: bool = True) -> bool:
        """
        Load the vision model.
        
        Args:
            use_finetuned: If True and finetuned model exists, use it.
        
        Returns:
            True if model loaded successfully.
        """
        try:
            import torch
            from transformers import VideoMAEForVideoClassification, VideoMAEImageProcessor
            
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading Vision model on {self.device}...")
            
            # Check for finetuned model first
            if use_finetuned and FINETUNED_MODEL_PATH.exists():
                try:
                    self.model = torch.load(FINETUNED_MODEL_PATH, map_location=self.device)
                    self.processor = VideoMAEImageProcessor.from_pretrained(self.model_name)
                    self._finetuned = True
                    logger.info("✅ Loaded finetuned Vision model")
                except Exception as e:
                    logger.warning(f"Failed to load finetuned model: {e}, falling back to pretrained")
                    self._finetuned = False
            
            # Load pretrained from HuggingFace if no finetuned model
            if not self._finetuned:
                self.processor = VideoMAEImageProcessor.from_pretrained(self.model_name)
                self.model = VideoMAEForVideoClassification.from_pretrained(self.model_name)
                self.model.to(self.device)
                logger.info(f"✅ Loaded pretrained Vision model: {self.model_name}")
            
            self.model.eval()
            self._loaded = True
            return True
            
        except ImportError as e:
            logger.error(f"Missing dependencies: {e}. Run: pip install transformers torch torchvision")
            return False
        except Exception as e:
            logger.error(f"Failed to load Vision model: {e}")
            return False
    
    def extract_features(self, video_frames: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract feature embeddings from video frames.
        
        Args:
            video_frames: numpy array of shape (num_frames, height, width, 3)
                         RGB format, values 0-255
        
        Returns:
            Feature vector of shape (hidden_size,) or None if failed
        """
        if not self._loaded:
            if not self.load():
                return None
        
        try:
            import torch
            
            # VideoMAE expects 16 frames typically
            num_frames = video_frames.shape[0]
            if num_frames < 16:
                # Pad with last frame
                padding = np.repeat(video_frames[-1:], 16 - num_frames, axis=0)
                video_frames = np.concatenate([video_frames, padding], axis=0)
            elif num_frames > 16:
                # Sample 16 evenly spaced frames
                indices = np.linspace(0, num_frames - 1, 16, dtype=int)
                video_frames = video_frames[indices]
            
            # Process frames
            inputs = self.processor(list(video_frames), return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Extract features (not class logits)
            with torch.no_grad():
                outputs = self.model(**inputs, output_hidden_states=True)
                
                # Use the [CLS] token from the last hidden state
                if hasattr(outputs, 'hidden_states') and outputs.hidden_states:
                    features = outputs.hidden_states[-1][:, 0, :]  # [batch, hidden_size]
                else:
                    # Fall back to logits if hidden states not available
                    features = outputs.logits
                
                features = features.cpu().numpy().squeeze()
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return None
    
    def extract_features_from_url(self, video_url: str, max_frames: int = 32) -> Optional[np.ndarray]:
        """
        Extract features from a video URL.
        
        Args:
            video_url: URL to video file
            max_frames: Maximum frames to sample
            
        Returns:
            Feature vector or None if failed
        """
        try:
            import cv2
            import tempfile
            import requests
            
            # Download video to temp file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as f:
                response = requests.get(video_url, stream=True, timeout=30)
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                temp_path = f.name
            
            try:
                # Read frames
                cap = cv2.VideoCapture(temp_path)
                frames = []
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                frame_indices = np.linspace(0, total_frames - 1, min(max_frames, total_frames), dtype=int)
                
                current_frame = 0
                while cap.isOpened() and len(frames) < max_frames:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    if current_frame in frame_indices:
                        # Convert BGR to RGB
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frames.append(frame)
                    current_frame += 1
                
                cap.release()
                
                if len(frames) < 8:
                    logger.warning(f"Only got {len(frames)} frames from video")
                    return None
                
                frames = np.array(frames)
                return self.extract_features(frames)
                
            finally:
                os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Failed to process video URL: {e}")
            return None
    
    def predict_action(self, video_frames: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Predict basketball action/activity from video frames.
        
        Args:
            video_frames: numpy array of shape (num_frames, height, width, 3)
        
        Returns:
            Dictionary with predicted action and confidence
        """
        if not self._loaded:
            if not self.load():
                return None
        
        try:
            import torch
            
            # Process frames
            num_frames = video_frames.shape[0]
            if num_frames < 16:
                padding = np.repeat(video_frames[-1:], 16 - num_frames, axis=0)
                video_frames = np.concatenate([video_frames, padding], axis=0)
            elif num_frames > 16:
                indices = np.linspace(0, num_frames - 1, 16, dtype=int)
                video_frames = video_frames[indices]
            
            inputs = self.processor(list(video_frames), return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)
                pred_idx = probs.argmax(-1).item()
                confidence = probs[0, pred_idx].item()
            
            # Map to Kinetics-400 label (or custom labels if finetuned)
            label = self.model.config.id2label.get(pred_idx, f"class_{pred_idx}")
            
            return {
                "action": label,
                "confidence": confidence,
                "top_5": self._get_top_k_predictions(probs, k=5)
            }
            
        except Exception as e:
            logger.error(f"Action prediction failed: {e}")
            return None
    
    def _get_top_k_predictions(self, probs, k: int = 5) -> List[Dict[str, Any]]:
        """Get top-k predictions with labels and probabilities."""
        import torch
        
        top_probs, top_indices = torch.topk(probs[0], k)
        results = []
        for prob, idx in zip(top_probs.tolist(), top_indices.tolist()):
            label = self.model.config.id2label.get(idx, f"class_{idx}")
            results.append({"action": label, "probability": prob})
        return results


# Singleton instance
_vision_model: Optional[VisionModel] = None


def get_vision_model() -> VisionModel:
    """Get or create the Vision model singleton."""
    global _vision_model
    if _vision_model is None:
        _vision_model = VisionModel()
    return _vision_model


# Basketball-specific action labels for finetuned model
BASKETBALL_ACTIONS = [
    "three_point_shot", "two_point_shot", "free_throw", "layup", "dunk",
    "pass", "assist", "steal", "block", "rebound",
    "turnover", "foul", "dribble", "screen", "fast_break",
    "iso_play", "pick_and_roll", "post_up", "cut", "transition_defense"
]


if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    model = VisionModel()
    
    if model.load():
        print("✅ Vision model loaded successfully!")
        print(f"   Model: {model.model_name}")
        print(f"   Device: {model.device}")
        print(f"   Finetuned: {model.is_finetuned}")
        
        # Test with random frames if no video provided
        if len(sys.argv) > 1:
            video_url = sys.argv[1]
            print(f"\n🎬 Extracting features from: {video_url}")
            features = model.extract_features_from_url(video_url)
            if features is not None:
                print(f"   Feature shape: {features.shape}")
                print(f"   Feature mean: {features.mean():.4f}")
        else:
            # Test with random dummy frames
            dummy_frames = np.random.randint(0, 255, (16, 224, 224, 3), dtype=np.uint8)
            features = model.extract_features(dummy_frames)
            if features is not None:
                print(f"\n🧪 Test with random frames:")
                print(f"   Feature shape: {features.shape}")
    else:
        print("❌ Failed to load Vision model")
        print("   Install dependencies: pip install transformers torch torchvision")
