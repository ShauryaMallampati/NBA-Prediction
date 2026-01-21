"""
Video Analyzer API - FastAPI endpoint for YouTube video analysis.

This module provides a REST API for analyzing NBA game highlight videos.
It downloads videos from YouTube, runs Vision CNN + Audio MLP + Optical Flow,
and generates AI-powered scouting reports using Qwen3-4B.
"""

import asyncio
import json
import re
import tempfile
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import uvicorn

# Local imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.video_metadata import extract_game_info_from_title, get_video_metadata
from src.services.llm_reporter import LLMReporter
from src.models.vision.video_analyzer_core import VideoAnalyzerCore

# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="NBA Video Intelligence API",
    description="AI-powered game analysis from YouTube highlights",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Request/Response Models
# =============================================================================

class AnalyzeRequest(BaseModel):
    url: str
    generate_report: bool = True  # Whether to generate LLM report


class ClipAnalysis(BaseModel):
    clip_index: int
    timestamp_approx: str
    vision_score: float
    audio_energy: float
    flow_intensity: float


class AnalysisResponse(BaseModel):
    success: bool
    video_url: str
    title: str
    duration_seconds: float
    upload_date: Optional[str]
    
    # Team info (parsed from title)
    home_team: str
    away_team: str
    
    # Aggregate scores
    overall_vision_score: float
    overall_audio_energy: float
    flow_stats: dict
    
    # Per-clip timeline (48 clips for charts)
    clip_timeline: list[ClipAnalysis]
    
    # Peak moments
    peak_visual_moment: str
    peak_audio_moment: str
    
    # AI-generated report
    ai_scouting_report: Optional[str]
    
    # Processing info
    frames_analyzed: int
    processing_time_seconds: float


# =============================================================================
# Global Model Instances (lazy loaded)
# =============================================================================

_analyzer: Optional[VideoAnalyzerCore] = None
_llm_reporter: Optional[LLMReporter] = None


def get_analyzer() -> VideoAnalyzerCore:
    global _analyzer
    if _analyzer is None:
        # Use 24 clips for faster processing (was 48)
        _analyzer = VideoAnalyzerCore(num_clips=24)
    return _analyzer


def get_llm_reporter() -> LLMReporter:
    global _llm_reporter
    if _llm_reporter is None:
        # Use real Qwen3-4B LLM for intelligent report generation
        _llm_reporter = LLMReporter(use_template_only=False)
    return _llm_reporter


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
async def root():
    return {"status": "ok", "message": "NBA Video Intelligence API"}


@app.get("/health")
async def health():
    """Detailed health check including model status."""
    analyzer_status = "not_loaded"
    vision_loaded = False
    audio_loaded = False
    
    global _analyzer
    if _analyzer:
        analyzer_status = "loaded"
        vision_loaded = _analyzer._vision_model is not None
        audio_loaded = _analyzer._audio_analyzer is not None and _analyzer._audio_analyzer.model_loaded
    
    return {
        "status": "healthy",
        "analyzer": {
            "status": analyzer_status,
            "vision_model": vision_loaded,
            "audio_model": audio_loaded
        },
        "timestamp": datetime.now().isoformat()
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_video(request: AnalyzeRequest):
    """
    Analyze a YouTube NBA highlight video.
    
    Returns:
    - Team names (parsed from title)
    - Vision dominance scores (48-point timeline)
    - Crowd energy analysis
    - Optical flow intensity
    - AI-generated scouting report
    """
    import time
    start_time = time.time()
    
    print("\n" + "=" * 70)
    print("[API] NEW ANALYSIS REQUEST")
    print(f"[API] URL: {request.url}")
    print(f"[API] Generate Report: {request.generate_report}")
    print("=" * 70)
    
    try:
        # 1. Get video metadata
        print("\n[API] Step 1: Fetching video metadata...")
        metadata = await asyncio.to_thread(get_video_metadata, request.url)
        if not metadata:
            print("[API] ❌ Could not fetch video metadata")
            raise HTTPException(status_code=400, detail="Could not fetch video metadata")
        print(f"[API] ✅ Title: {metadata.get('title', 'N/A')}")
        print(f"[API] ✅ Duration: {metadata.get('duration', 'N/A')} seconds")
        
        # 2. Parse team names from title
        print("\n[API] Step 2: Parsing team names...")
        game_info = extract_game_info_from_title(metadata["title"])
        print(f"[API] ✅ Home: {game_info['home_team']}, Away: {game_info['away_team']}")
        
        # 3. Download video to temp file
        print("\n[API] Step 3: Downloading video...")
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = Path(tmpdir) / "video.mp4"
            
            # Download using yt-dlp
            download_cmd = [
                "yt-dlp",
                "-f", "best[height<=720]",
                "-o", str(video_path),
                "--no-playlist",
                request.url
            ]
            
            print(f"[API] Running: {' '.join(download_cmd)}")
            result = subprocess.run(download_cmd, capture_output=True, timeout=120)
            if result.returncode != 0 or not video_path.exists():
                print(f"[API] ❌ Download failed: {result.stderr.decode()[:200]}")
                raise HTTPException(status_code=400, detail="Failed to download video")
            print(f"[API] ✅ Downloaded to: {video_path}")
            print(f"[API] ✅ File size: {video_path.stat().st_size / 1024 / 1024:.1f} MB")
            
            # 4. Run analysis (48 clips)
            print("\n[API] Step 4: Running video analysis...")
            analyzer = get_analyzer()
            analysis = await asyncio.to_thread(analyzer.analyze, video_path)
            print("[API] ✅ Analysis complete")
            
            # 5. Build clip timeline

            clip_timeline = []
            duration = metadata.get("duration", 300)  # default 5 min
            
            for i, clip_data in enumerate(analysis["per_clip_scores"]):
                timestamp_sec = (i / len(analysis["per_clip_scores"])) * duration
                minutes = int(timestamp_sec // 60)
                seconds = int(timestamp_sec % 60)
                
                clip_timeline.append(ClipAnalysis(
                    clip_index=i,
                    timestamp_approx=f"{minutes}:{seconds:02d}",
                    vision_score=clip_data["vision"],
                    audio_energy=clip_data["audio"],
                    flow_intensity=clip_data["flow"]
                ))
            
            # 6. Find peak moments
            vision_scores = [c.vision_score for c in clip_timeline]
            audio_scores = [c.audio_energy for c in clip_timeline]
            
            peak_vision_idx = vision_scores.index(max(vision_scores))
            peak_audio_idx = audio_scores.index(max(audio_scores))
            
            peak_visual_moment = clip_timeline[peak_vision_idx].timestamp_approx
            peak_audio_moment = clip_timeline[peak_audio_idx].timestamp_approx
            
            # 7. Generate AI report (optional)
            ai_report = None
            if request.generate_report:
                llm = get_llm_reporter()
                ai_report = await asyncio.to_thread(
                    llm.generate_scouting_report,
                    home_team=game_info["home_team"],
                    away_team=game_info["away_team"],
                    vision_score=analysis["overall_vision"],
                    audio_energy=analysis["overall_audio"],
                    flow_stats=analysis["flow_stats"],
                    peak_visual_moment=peak_visual_moment,
                    peak_audio_moment=peak_audio_moment
                )
            
            processing_time = time.time() - start_time
            
            return AnalysisResponse(
                success=True,
                video_url=request.url,
                title=metadata["title"],
                duration_seconds=duration,
                upload_date=metadata.get("upload_date"),
                home_team=game_info["home_team"],
                away_team=game_info["away_team"],
                overall_vision_score=analysis["overall_vision"],
                overall_audio_energy=analysis["overall_audio"],
                flow_stats=analysis["flow_stats"],
                clip_timeline=clip_timeline,
                peak_visual_moment=peak_visual_moment,
                peak_audio_moment=peak_audio_moment,
                ai_scouting_report=ai_report,
                frames_analyzed=len(analysis["per_clip_scores"]) * 16,  # actual clips × 16 frames
                processing_time_seconds=round(processing_time, 2)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"Analysis failed: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)  # Console log
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Run Server
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
