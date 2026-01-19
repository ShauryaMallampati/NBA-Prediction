"""
Audio Analytics Module for Multi-Modal NBA Prediction.

This module extracts audio features from highlight videos to capture
"crowd momentum" as a signal for home-team advantage.

Research Rationale:
- Crowd noise intensity correlates with home-team momentum
- Cheering peaks often precede or follow scoring runs
- Audio-visual fusion improves sports prediction by ~5% (Amazon SageMaker 2021)

Pipeline:
1. Extract audio track from video file
2. Compute Mel Spectrogram and loudness curve
3. Detect cheering peaks and compute summary statistics
4. Return crowd momentum score [0.3, 0.7]
"""

import numpy as np
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import subprocess
import tempfile

logger = logging.getLogger(__name__)

# Optional imports (may not be installed)
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not installed. Audio analysis disabled.")


class AudioAnalytics:
    """
    Analyzes crowd noise from video highlights to compute momentum scores.
    
    Features extracted:
    - Mean loudness (RMS energy)
    - Max loudness (peak cheering)
    - Number of loudness peaks (crowd reactions)
    - Peak intensity standard deviation (consistency)
    """
    
    def __init__(self, sample_rate: int = 22050, n_mels: int = 64):
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        self.model = None  # Optional trained classifier
        self.model_loaded = False
        
    def load_model(self, model_path: Optional[Path] = None) -> bool:
        """Load trained audio classifier if available."""
        if model_path is None:
            model_path = Path("artifacts/models/audio/crowd_classifier.pt")
        
        if model_path.exists():
            try:
                import torch
                self.model = torch.load(model_path, map_location='cpu')
                self.model_loaded = True
                logger.info(f"✅ Audio model loaded from {model_path}")
                return True
            except Exception as e:
                logger.warning(f"Failed to load audio model: {e}")
        return False
    
    def extract_audio(self, video_path: Path) -> Optional[Path]:
        """Extract audio track from video file using ffmpeg."""
        temp_audio = Path(tempfile.gettempdir()) / f"temp_audio_{video_path.stem}.wav"
        
        try:
            # Use ffmpeg to extract audio
            cmd = [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # WAV format
                "-ar", str(self.sample_rate),
                "-ac", "1",  # Mono
                str(temp_audio)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and temp_audio.exists():
                logger.debug(f"   🎵 Audio extracted: {temp_audio}")
                return temp_audio
            else:
                logger.warning(f"   ⚠️ Audio extraction failed: {result.stderr[:100]}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.warning("   ⚠️ Audio extraction timed out")
            return None
        except FileNotFoundError:
            logger.warning("   ⚠️ ffmpeg not found. Install with: brew install ffmpeg")
            return None
        except Exception as e:
            logger.warning(f"   ⚠️ Audio extraction error: {e}")
            return None
    
    def compute_audio_features(self, audio_path: Path) -> Dict[str, float]:
        """
        Compute audio features from WAV file.
        
        Returns:
            Dict with keys: mean_loudness, max_loudness, num_peaks, peak_std
        """
        if not LIBROSA_AVAILABLE:
            return self._get_neutral_features()
        
        try:
            # Load audio
            y, sr = librosa.load(str(audio_path), sr=self.sample_rate)
            
            # Compute RMS energy (loudness)
            rms = librosa.feature.rms(y=y)[0]
            
            # Compute peaks (frames where loudness exceeds 90th percentile)
            threshold = np.percentile(rms, 90)
            peaks = np.where(rms > threshold)[0]
            num_peaks = len(peaks)
            
            # Peak intensities
            peak_intensities = rms[peaks] if len(peaks) > 0 else np.array([0.0])
            
            features = {
                "mean_loudness": float(np.mean(rms)),
                "max_loudness": float(np.max(rms)),
                "num_peaks": float(num_peaks),
                "peak_std": float(np.std(peak_intensities)),
            }
            
            logger.debug(f"   📊 Audio features: {features}")
            return features
            
        except Exception as e:
            logger.warning(f"   ⚠️ Audio feature extraction failed: {e}")
            return self._get_neutral_features()
    
    def _get_neutral_features(self) -> Dict[str, float]:
        """Return neutral features when audio analysis fails."""
        return {
            "mean_loudness": 0.0,
            "max_loudness": 0.0,
            "num_peaks": 0.0,
            "peak_std": 0.0,
        }
    
    def features_to_score(self, features: Dict[str, float]) -> float:
        """
        Convert audio features to crowd momentum score.
        
        If trained model exists, use it. Otherwise use heuristic.
        
        Returns:
            Score in range [0.3, 0.7], where 0.5 is neutral
        """
        # If no features, return neutral
        if features["mean_loudness"] == 0.0:
            return 0.5
        
        if self.model_loaded and self.model is not None:
            # Use trained classifier
            try:
                import torch
                x = torch.tensor([
                    features["mean_loudness"],
                    features["max_loudness"],
                    features["num_peaks"] / 100.0,  # Normalize
                    features["peak_std"],
                ], dtype=torch.float32).unsqueeze(0)
                
                with torch.no_grad():
                    score = torch.sigmoid(self.model(x)).item()
                return 0.3 + score * 0.4  # Map to [0.3, 0.7]
            except Exception as e:
                logger.warning(f"Model inference failed: {e}")
        
        # Heuristic fallback: louder crowd = higher home advantage
        # Normalize loudness to [0, 1] range (typical RMS is 0.01-0.15)
        normalized_loudness = min(1.0, features["mean_loudness"] / 0.1)
        
        # More peaks = more crowd engagement
        normalized_peaks = min(1.0, features["num_peaks"] / 50.0)
        
        # Combine: 70% loudness, 30% peak count
        raw_score = 0.7 * normalized_loudness + 0.3 * normalized_peaks
        
        # Map to [0.3, 0.7]
        return 0.3 + raw_score * 0.4
    
    def get_crowd_momentum_score(self, video_path: Path) -> Tuple[float, Dict]:
        """
        Main entry point: Extract audio and compute crowd momentum score.
        
        Args:
            video_path: Path to highlight video
            
        Returns:
            Tuple of (score, metadata)
            - score: float in [0.3, 0.7]
            - metadata: dict with features and method used
        """
        if not LIBROSA_AVAILABLE:
            logger.debug("   ⚠️ librosa not available, returning neutral audio score")
            return 0.5, {"method": "disabled", "reason": "librosa not installed"}
        
        # Extract audio
        audio_path = self.extract_audio(video_path)
        if audio_path is None:
            return 0.5, {"method": "failed", "reason": "audio extraction failed"}
        
        try:
            # Compute features
            features = self.compute_audio_features(audio_path)
            
            # Convert to score
            score = self.features_to_score(features)
            
            # Cleanup temp file
            if audio_path.exists():
                audio_path.unlink()
            
            metadata = {
                "method": "model" if self.model_loaded else "heuristic",
                "features": features,
                "score": score,
            }
            
            logger.info(f"   🎵 Audio Score: {score:.3f} (method={metadata['method']})")
            return score, metadata
            
        except Exception as e:
            logger.warning(f"   ⚠️ Audio analysis failed: {e}")
            return 0.5, {"method": "error", "reason": str(e)}
    
    def get_audio_momentum_delta(self, home_video: Path, away_video: Path) -> Tuple[float, Dict]:
        """
        Compute audio-based momentum delta for a matchup.
        
        Args:
            home_video: Path to home team's recent game highlight
            away_video: Path to away team's recent game highlight
            
        Returns:
            Tuple of (delta, metadata)
            - delta: float in [-0.05, 0.05]
            - metadata: dict with home/away scores
        """
        home_score, home_meta = self.get_crowd_momentum_score(home_video)
        away_score, away_meta = self.get_crowd_momentum_score(away_video)
        
        # Difference weighted by 0.1
        raw_diff = home_score - away_score
        delta = np.clip(raw_diff * 0.1, -0.05, 0.05)
        
        metadata = {
            "home_audio_score": home_score,
            "away_audio_score": away_score,
            "raw_diff": raw_diff,
            "delta": delta,
            "home_method": home_meta.get("method", "unknown"),
            "away_method": away_meta.get("method", "unknown"),
        }
        
        logger.info(f"   🎵 Audio Delta: {delta:+.4f} (Home={home_score:.3f}, Away={away_score:.3f})")
        return delta, metadata


# Global instance
audio_analytics = AudioAnalytics()
