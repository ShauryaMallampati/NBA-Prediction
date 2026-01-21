"""
Video Analyzer Core - CNN + Audio + Flow analysis with enhanced sampling.

This module runs the actual video analysis:
- 48 clips (enhanced from 12)
- 16 frames per clip
- Total: 768 frames analyzed
"""

import cv2
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class VideoAnalyzerCore:
    """
    Core video analyzer with enhanced 48-clip sampling.
    
    Features:
    - Vision CNN (MobileNetV3) for visual dominance
    - Audio MLP for crowd energy
    - Optical flow for game intensity
    - Per-clip scores for timeline visualization
    """
    
    def __init__(
        self,
        num_clips: int = 48,
        frames_per_clip: int = 16,
        vision_model_path: Optional[str] = None,
        audio_model_path: Optional[str] = None,
    ):
        self.num_clips = num_clips
        self.frames_per_clip = frames_per_clip
        
        # Model paths (defaults)
        project_root = Path(__file__).parent.parent.parent.parent
        self.vision_model_path = vision_model_path or str(
            project_root / "artifacts" / "models" / "vision" / "basketball_shot_classifier.pt"
        )
        self.audio_model_path = audio_model_path or str(
            project_root / "artifacts" / "models" / "audio" / "crowd_classifier.pt"
        )
        
        # Lazy load models
        self._vision_model = None
        self._audio_model = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        logger.info(f"VideoAnalyzerCore initialized: {num_clips} clips, {frames_per_clip} frames each")
    
    def _load_vision_model(self):
        """Lazy load vision model."""
        if self._vision_model is not None:
            print("[VISION] Model already loaded, skipping.")
            return
        
        print(f"[VISION] Loading vision model from: {self.vision_model_path}")
        
        try:
            from torchvision.models import mobilenet_v3_large
            
            # Create model
            self._vision_model = mobilenet_v3_large(weights=None)
            self._vision_model.classifier[-1] = nn.Linear(1280, 1)
            print(f"[VISION] Created MobileNetV3 architecture")
            
            # Load weights - NO FALLBACK, must exist
            if Path(self.vision_model_path).exists():
                state_dict = torch.load(self.vision_model_path, map_location=self._device)
                self._vision_model.load_state_dict(state_dict)
                print(f"[VISION] ✅ Loaded trained weights from {self.vision_model_path}")
            else:
                raise FileNotFoundError(f"[VISION] ❌ VISION MODEL NOT FOUND: {self.vision_model_path}")
            
            self._vision_model.to(self._device)
            self._vision_model.eval()
            print(f"[VISION] ✅ Vision model ready on device: {self._device}")
            
        except Exception as e:
            print(f"[VISION] ❌ CRITICAL ERROR loading vision model: {e}")
            raise RuntimeError(f"Vision model loading failed: {e}")
    
    def _load_audio_model(self):
        """
        Load real audio analyzer with trained classifier.
        NO FALLBACKS - will raise if model can't be loaded.
        """
        print(f"[AUDIO] Loading audio model from: {self.audio_model_path}")
        
        try:
            from src.models.vision.audio_analytics import AudioAnalytics
            print("[AUDIO] AudioAnalytics import successful")
            
            self._audio_analyzer = AudioAnalytics()
            model_loaded = self._audio_analyzer.load_model(Path(self.audio_model_path))
            
            if model_loaded:
                print(f"[AUDIO] ✅ Audio classifier loaded from {self.audio_model_path}")
                print(f"[AUDIO] Model architecture: {self._audio_analyzer.model}")
            else:
                raise RuntimeError(f"[AUDIO] ❌ AUDIO MODEL FAILED TO LOAD from {self.audio_model_path}")
            
            self._audio_model = self._audio_analyzer  # Reference for compatibility
            
        except ImportError as e:
            print(f"[AUDIO] ❌ CRITICAL: AudioAnalytics import failed: {e}")
            raise RuntimeError(f"AudioAnalytics import failed: {e}")
        except Exception as e:
            print(f"[AUDIO] ❌ CRITICAL ERROR loading audio model: {e}")
            raise RuntimeError(f"Audio model loading failed: {e}")
    
    def _get_real_audio_score(self, video_path: Path) -> float:
        """
        Extract real crowd energy from video audio track.
        NO FALLBACKS - will raise if audio extraction fails.
        
        Returns:
            Crowd energy score in [0.3, 0.7] range
        """
        if self._audio_analyzer is None:
            raise RuntimeError("[AUDIO] Audio analyzer not initialized!")
        
        print(f"[AUDIO] Extracting audio from: {video_path}")
        
        try:
            score, metadata = self._audio_analyzer.get_crowd_momentum_score(video_path)
            print(f"[AUDIO] ✅ Real audio score: {score:.3f}")
            print(f"[AUDIO]    Method: {metadata.get('method', 'unknown')}")
            if 'features' in metadata:
                print(f"[AUDIO]    Features: {metadata['features']}")
            return score
        except Exception as e:
            print(f"[AUDIO] ❌ Audio extraction failed: {e}")
            raise RuntimeError(f"Audio score extraction failed: {e}")
    
    def analyze(self, video_path: Path) -> dict:
        """
        Analyze a video file.
        
        Returns:
            {
                "overall_vision": float,
                "overall_audio": float,
                "flow_stats": {mean, max, std, burstiness},
                "per_clip_scores": [
                    {"vision": float, "audio": float, "flow": float},
                    ...
                ]
            }
        """
        print("=" * 60)
        print("[ANALYZE] Starting video analysis...")
        print(f"[ANALYZE] Video path: {video_path}")
        print("=" * 60)
        
        # Load models
        print("\n[ANALYZE] Step 1: Loading models...")
        self._load_vision_model()
        self._load_audio_model()
        print("[ANALYZE] ✅ All models loaded successfully")
        
        # Open video
        print(f"\n[ANALYZE] Step 2: Opening video file...")
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        print(f"[ANALYZE] Video info: {total_frames} frames, {fps:.1f} FPS")
        
        if total_frames < self.frames_per_clip:
            cap.release()
            raise ValueError(f"Video too short: {total_frames} frames")
        
        # Calculate clip positions (evenly distributed)
        actual_num_clips = min(self.num_clips, total_frames // self.frames_per_clip)
        clip_starts = np.linspace(
            0, 
            total_frames - self.frames_per_clip, 
            actual_num_clips, 
            dtype=int
        )
        print(f"[ANALYZE] Will analyze {actual_num_clips} clips")
        
        # Analyze each clip
        per_clip_scores = []
        all_vision_scores = []
        all_audio_scores = []
        all_flow_magnitudes = []
        
        # Get real audio score from the video (uses librosa + trained classifier)
        print(f"\n[ANALYZE] Step 3: Extracting audio score...")
        overall_real_audio = self._get_real_audio_score(video_path)
        print(f"[ANALYZE] Overall audio energy: {overall_real_audio:.3f}")
        
        print(f"\n[ANALYZE] Step 4: Analyzing {actual_num_clips} clips...")
        for clip_idx, clip_start in enumerate(clip_starts):
            # Extract frames for this clip
            frames = []
            prev_gray = None
            clip_flows = []
            
            for i in range(self.frames_per_clip):
                cap.set(cv2.CAP_PROP_POS_FRAMES, clip_start + i)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # Preprocess for CNN
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (224, 224))
                frame_tensor = torch.from_numpy(frame_resized).float() / 255.0
                frame_tensor = (frame_tensor - torch.tensor([0.485, 0.456, 0.406])) / torch.tensor([0.229, 0.224, 0.225])
                frame_tensor = frame_tensor.permute(2, 0, 1)
                frames.append(frame_tensor)
                
                # Optical flow
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.resize(gray, (224, 224))
                
                if prev_gray is not None:
                    flow = cv2.calcOpticalFlowFarneback(
                        prev_gray, gray, None,
                        pyr_scale=0.5, levels=3, winsize=15,
                        iterations=3, poly_n=5, poly_sigma=1.2, flags=0
                    )
                    magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
                    clip_flows.append(np.mean(magnitude))
                
                prev_gray = gray
            
            if len(frames) < self.frames_per_clip // 2:
                continue
            
            # Vision score for this clip - NO FALLBACK
            if self._vision_model is None:
                raise RuntimeError("[VISION] Vision model not loaded!")
            
            with torch.no_grad():
                # Use middle frame as representative
                frame_batch = frames[len(frames)//2].unsqueeze(0).to(self._device)
                output = self._vision_model(frame_batch)
                vision_score = torch.sigmoid(output).item()
            
            # Audio score: real audio base + flow modulation for per-clip variation
            # Real audio provides overall crowd energy, flow adds moment-by-moment variation
            flow_modulation = (np.mean(clip_flows) / 10.0) if clip_flows else 0.0
            audio_score = min(1.0, overall_real_audio + flow_modulation * 0.3)
            
            # Flow intensity
            flow_mean = np.mean(clip_flows) if clip_flows else 0.0
            
            # Convert to native Python floats for Pydantic serialization
            per_clip_scores.append({
                "vision": float(round(vision_score, 3)),
                "audio": float(round(audio_score, 3)),
                "flow": float(round(flow_mean, 3))
            })
            
            all_vision_scores.append(vision_score)
            all_audio_scores.append(audio_score)
            all_flow_magnitudes.extend(clip_flows)
            
            # Log every 6 clips
            if (clip_idx + 1) % 6 == 0:
                print(f"[ANALYZE]    Processed {clip_idx + 1}/{actual_num_clips} clips | Last vision: {vision_score:.3f}")
        
        cap.release()
        
        # Calculate aggregates and convert to native Python types (Pydantic compatibility)
        overall_vision = float(np.mean(all_vision_scores)) if all_vision_scores else 0.5
        overall_audio = float(np.mean(all_audio_scores)) if all_audio_scores else 0.5
        
        flow_stats = {
            "mean_flow": float(round(np.mean(all_flow_magnitudes), 3)) if all_flow_magnitudes else 0.0,
            "max_flow": float(round(np.max(all_flow_magnitudes), 3)) if all_flow_magnitudes else 0.0,
            "flow_std": float(round(np.std(all_flow_magnitudes), 3)) if all_flow_magnitudes else 0.0,
            "burstiness": float(round(
                np.max(all_flow_magnitudes) / np.mean(all_flow_magnitudes), 2
            )) if all_flow_magnitudes and np.mean(all_flow_magnitudes) > 0 else 1.0
        }
        
        print(f"\n[ANALYZE] Step 5: Results")
        print(f"[ANALYZE] ✅ Overall Vision Score: {overall_vision:.3f}")
        print(f"[ANALYZE] ✅ Overall Audio Score: {overall_audio:.3f}")
        print(f"[ANALYZE] ✅ Flow Stats: {flow_stats}")
        print(f"[ANALYZE] ✅ Clips Analyzed: {len(per_clip_scores)}")
        print("=" * 60)
        
        return {
            "overall_vision": float(round(overall_vision, 3)),
            "overall_audio": float(round(overall_audio, 3)),
            "flow_stats": flow_stats,
            "per_clip_scores": per_clip_scores
        }


# =============================================================================
# Test
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python video_analyzer_core.py <video_path>")
        sys.exit(1)
    
    analyzer = VideoAnalyzerCore(num_clips=12)  # Use 12 for quick test
    result = analyzer.analyze(Path(sys.argv[1]))
    
    print(f"Overall Vision: {result['overall_vision']}")
    print(f"Overall Audio: {result['overall_audio']}")
    print(f"Flow Stats: {result['flow_stats']}")
    print(f"Clips analyzed: {len(result['per_clip_scores'])}")
