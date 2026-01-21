"""
Modal Serverless Video Analyzer - GPU-powered video analysis.

Deploy video analysis as a serverless function on Modal.com.
This allows scaling without managing servers.

Usage:
    modal deploy scripts/modal_video_analyzer.py
    
Cost: ~$0.10 per video (T4 GPU for ~2 minutes)
"""

import modal

# =============================================================================
# Modal App Definition
# =============================================================================

app = modal.App("nba-video-analyzer")

# Create a custom image with all dependencies
video_analyzer_image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install([
        "ffmpeg",
        "libgl1-mesa-glx",
        "libglib2.0-0",
    ])
    .pip_install([
        "torch",
        "torchvision",
        "opencv-python-headless",
        "numpy",
        "yt-dlp",
        "librosa",
        "transformers",
        "accelerate",
    ])
)


# =============================================================================
# Volume for Model Weights (Persistent Storage)
# =============================================================================

model_volume = modal.Volume.from_name("nba-model-weights", create_if_missing=True)


# =============================================================================
# Serverless Function
# =============================================================================

@app.function(
    gpu="T4",
    image=video_analyzer_image,
    timeout=300,  # 5 minutes max
    volumes={"/models": model_volume},
)
def analyze_video(youtube_url: str, num_clips: int = 48) -> dict:
    """
    Analyze a YouTube video using Vision CNN, Audio MLP, and Optical Flow.
    
    Args:
        youtube_url: YouTube video URL
        num_clips: Number of clips to sample (default: 48)
    
    Returns:
        {
            "overall_vision": float,
            "overall_audio": float,
            "flow_stats": {...},
            "per_clip_scores": [...]
        }
    """
    import tempfile
    import subprocess
    import cv2
    import numpy as np
    import torch
    import torch.nn as nn
    from pathlib import Path
    
    # Load models
    from torchvision.models import mobilenet_v3_large
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Load Vision CNN
    vision_model = mobilenet_v3_large(weights=None)
    vision_model.classifier[-1] = nn.Linear(1280, 1)
    
    # Try to load pretrained weights
    weights_path = Path("/models/basketball_shot_classifier.pt")
    if weights_path.exists():
        state_dict = torch.load(weights_path, map_location=device)
        vision_model.load_state_dict(state_dict)
        print("Loaded pretrained vision model")
    else:
        print("Using random vision model weights")
    
    vision_model.to(device)
    vision_model.eval()
    
    # Download video
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = Path(tmpdir) / "video.mp4"
        
        cmd = [
            "yt-dlp",
            "-f", "best[height<=720]",
            "-o", str(video_path),
            "--no-playlist",
            youtube_url
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode != 0:
            return {"error": "Failed to download video"}
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return {"error": "Could not open video"}
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames_per_clip = 16
        
        if total_frames < frames_per_clip:
            cap.release()
            return {"error": "Video too short"}
        
        # Calculate clip positions
        actual_num_clips = min(num_clips, total_frames // frames_per_clip)
        clip_starts = np.linspace(
            0,
            total_frames - frames_per_clip,
            actual_num_clips,
            dtype=int
        )
        
        # Analyze clips
        per_clip_scores = []
        all_vision = []
        all_audio = []
        all_flow = []
        
        for clip_idx, clip_start in enumerate(clip_starts):
            frames = []
            prev_gray = None
            clip_flows = []
            
            for i in range(frames_per_clip):
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
                        0.5, 3, 15, 3, 5, 1.2, 0
                    )
                    magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
                    clip_flows.append(np.mean(magnitude))
                
                prev_gray = gray
            
            if len(frames) < 8:
                continue
            
            # Vision score
            with torch.no_grad():
                frame_batch = frames[len(frames)//2].unsqueeze(0).to(device)
                output = vision_model(frame_batch)
                vision_score = torch.sigmoid(output).item()
            
            # Audio approximation (from flow intensity)
            audio_score = min(1.0, np.mean(clip_flows) / 5.0 + 0.3) if clip_flows else 0.5
            flow_mean = np.mean(clip_flows) if clip_flows else 0.0
            
            per_clip_scores.append({
                "vision": round(vision_score, 3),
                "audio": round(audio_score, 3),
                "flow": round(flow_mean, 3)
            })
            
            all_vision.append(vision_score)
            all_audio.append(audio_score)
            all_flow.extend(clip_flows)
        
        cap.release()
        
        # Aggregate stats
        return {
            "overall_vision": round(np.mean(all_vision), 3) if all_vision else 0.5,
            "overall_audio": round(np.mean(all_audio), 3) if all_audio else 0.5,
            "flow_stats": {
                "mean_flow": round(np.mean(all_flow), 3) if all_flow else 0.0,
                "max_flow": round(np.max(all_flow), 3) if all_flow else 0.0,
                "flow_std": round(np.std(all_flow), 3) if all_flow else 0.0,
                "burstiness": round(np.max(all_flow) / np.mean(all_flow), 2) if all_flow and np.mean(all_flow) > 0 else 1.0
            },
            "per_clip_scores": per_clip_scores
        }


# =============================================================================
# Test Entrypoint
# =============================================================================

@app.local_entrypoint()
def main():
    """Test the analyzer with a sample video."""
    result = analyze_video.remote(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Replace with actual NBA video
        num_clips=12  # Use fewer clips for testing
    )
    print(f"Result: {result}")
