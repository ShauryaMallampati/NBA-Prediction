#!/usr/bin/env python3
"""
🏀 STREAMING WORLD MODEL EVALUATION
=====================================
This script evaluates the FULL World Model on the 2025-26 season
using REAL VIDEO from YouTube.

Process for EACH game:
1. Download YouTube highlight video (~100MB)
2. Run Vision CNN on video frames
3. Run full World Model prediction (Ensemble + Momentum + Chemistry + Vision)
4. Save prediction vs actual result
5. DELETE video to save space
6. Repeat for all games

Usage:
    poetry run python scripts/streaming_world_model_eval.py --season 2025-26

Dependencies:
    pip install yt-dlp opencv-python torch
"""

import os
import sys
import json
import cv2
import torch
import numpy as np
import pandas as pd
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, Optional
import time

# Add project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.pregame.train_ensemble import EnsembleTrainer
from src.models.chemistry_gnn import get_chemistry_model
from src.models.momentum.momentum_transformer import MomentumAnalytics
from src.common.features import RunningWorldState

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
TEMP_VIDEO_DIR = Path("data/temp_video")
RESULTS_DIR = Path("artifacts/evaluation/real_video")
TEMP_VIDEO_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Team name mappings for YouTube search
TEAM_NAMES = {
    "Lakers": "Los Angeles Lakers", "Celtics": "Boston Celtics",
    "Warriors": "Golden State Warriors", "Nuggets": "Denver Nuggets",
    "Bucks": "Milwaukee Bucks", "76ers": "Philadelphia 76ers",
    "Heat": "Miami Heat", "Suns": "Phoenix Suns",
    "Cavaliers": "Cleveland Cavaliers", "Mavericks": "Dallas Mavericks",
    "Clippers": "LA Clippers", "Kings": "Sacramento Kings",
    "Timberwolves": "Minnesota Timberwolves", "Thunder": "Oklahoma City Thunder",
    "Pelicans": "New Orleans Pelicans", "Knicks": "New York Knicks",
    "Nets": "Brooklyn Nets", "Hawks": "Atlanta Hawks",
    "Bulls": "Chicago Bulls", "Raptors": "Toronto Raptors",
    "Pacers": "Indiana Pacers", "Magic": "Orlando Magic",
    "Hornets": "Charlotte Hornets", "Wizards": "Washington Wizards",
    "Pistons": "Detroit Pistons", "Grizzlies": "Memphis Grizzlies",
    "Spurs": "San Antonio Spurs", "Trail Blazers": "Portland Trail Blazers",
    "Jazz": "Utah Jazz", "Rockets": "Houston Rockets",
}


class StreamingWorldModelEvaluator:
    def __init__(self, model_dir: str = "artifacts/models/pregame"):
        logger.info(f"📦 Loading World Model components from {model_dir}...")
        
        # Load Ensemble
        self.ensemble = EnsembleTrainer(output_dir=model_dir)
        self.ensemble.load_models()
        logger.info("✅ Ensemble loaded")
        
        # Load Chemistry
        self.chemistry = get_chemistry_model()
        logger.info(f"✅ Chemistry loaded: {self.chemistry.loaded}")
        
        # Load Momentum
        # Check for momentum model in custom directory
        momentum_path = Path(model_dir) / "momentum/momentum_transformer.pt"
        if momentum_path.exists():
            self.momentum = MomentumAnalytics(model_path=str(momentum_path))
        else:
            # Fallback to default path (may have leakage logic warnings)
            logger.warning(f"⚠️ Custom momentum model not found at {momentum_path}. Using default.")
            self.momentum = MomentumAnalytics()
            
        logger.info(f"✅ Momentum loaded: {self.momentum.loaded}")
        
        # Baseline State for streaming simulation
        self.world_state = RunningWorldState()
        
        # Performance metrics
        self.results = []
        
        # Load Vision CNN (direct PyTorch loading with correct architecture)
        try:
            import torch
            import torch.nn as nn
            
            # Define the Simple3DCNN architecture (matches train_vision_cnn.py)
            class Simple3DCNN(nn.Module):
                """Simple 3D CNN for video classification."""
                def __init__(self, num_classes: int = 8, num_frames: int = 16):
                    super().__init__()
                    self.features = nn.Sequential(
                        nn.Conv3d(3, 32, kernel_size=(3, 7, 7), stride=(1, 2, 2), padding=(1, 3, 3)),
                        nn.BatchNorm3d(32),
                        nn.ReLU(inplace=True),
                        nn.MaxPool3d(kernel_size=(1, 3, 3), stride=(1, 2, 2), padding=(0, 1, 1)),
                        nn.Conv3d(32, 64, kernel_size=(3, 3, 3), padding=1),
                        nn.BatchNorm3d(64),
                        nn.ReLU(inplace=True),
                        nn.MaxPool3d(kernel_size=(2, 2, 2), stride=(2, 2, 2)),
                        nn.Conv3d(64, 128, kernel_size=(3, 3, 3), padding=1),
                        nn.BatchNorm3d(128),
                        nn.ReLU(inplace=True),
                        nn.MaxPool3d(kernel_size=(2, 2, 2), stride=(2, 2, 2)),
                        nn.Conv3d(128, 256, kernel_size=(3, 3, 3), padding=1),
                        nn.BatchNorm3d(256),
                        nn.ReLU(inplace=True),
                        nn.AdaptiveAvgPool3d((1, 1, 1)),
                    )
                    self.classifier = nn.Sequential(
                        nn.Flatten(),
                        nn.Dropout(0.5),
                        nn.Linear(256, 128),
                        nn.ReLU(inplace=True),
                        nn.Dropout(0.3),
                        nn.Linear(128, num_classes)
                    )
                def forward(self, x):
                    x = x.permute(0, 2, 1, 3, 4)  # (B, T, C, H, W) -> (B, C, T, H, W)
                    x = self.features(x)
                    x = self.classifier(x)
                    return x
            
            vision_path = Path("artifacts/models/vision/basketball_shot_classifier.pt")
            if vision_path.exists():
                ckpt = torch.load(vision_path, map_location='cpu')
                num_classes = ckpt.get('num_classes', 8)
                num_frames = ckpt.get('num_frames', 16)
                
                self.vision_model = Simple3DCNN(num_classes=num_classes, num_frames=num_frames)
                self.vision_model.load_state_dict(ckpt['model_state_dict'])
                self.vision_model.eval()
                
                self.vision_labels = ckpt.get('labels', {})
                best_acc = ckpt.get('best_val_acc', 0)
                if best_acc > 100:
                    best_acc = best_acc / 100
                
                logger.info(f"✅ Vision CNN loaded: {num_classes} classes, {best_acc:.2f}% accuracy")
                self.vision_loaded = True
                self.vision_num_frames = num_frames
            else:
                logger.warning("⚠️ Vision CNN checkpoint not found")
                self.vision_model = None
                self.vision_loaded = False
        except Exception as e:
            logger.warning(f"⚠️ Vision CNN not loaded: {e}")
            import traceback
            traceback.print_exc()
            self.vision_model = None
            self.vision_loaded = False
        
        # Load historical games for team strength calculation (Ensemble proxy)
        try:
            self.games_df = pd.read_csv("data/nba_games_enhanced.csv")
            self.games_df['date'] = pd.to_datetime(self.games_df['date'])
            logger.info(f"✅ Historical data loaded: {len(self.games_df)} games")
        except Exception as e:
            logger.warning(f"⚠️ Historical data not loaded: {e}")
            self.games_df = None
        
        # Results storage
        # self.results = [] # Moved above
        
        # Video cache for historical analysis (pregame only!)
        self.video_cache_dir = Path("data/video_cache")
        self.video_cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_videos_per_team = 5  # Keep last 5 videos per team
        self.min_games_for_vision = 1  # Use vision from game 1 (even with just 1 video)
        self.team_vision_cache = {}  # {team: [list of (date, score) tuples]}
        logger.info(f"📁 Video cache dir: {self.video_cache_dir}")
        
        # Build playlist index from NBA official playlist
        self.playlist_index = {}
        self._build_playlist_index()
    
    def _build_playlist_index(self):
        """Build index of games from NBA official highlights playlists (2024-25 & 2025-26)."""
        playlists = [
            # 2025-26 Season
            "https://www.youtube.com/playlist?list=PLlVlyGVtvuVlek5UOvwJaRDtuAI1FgGZf",
            # 2024-25 Season (for historical context)
            "https://www.youtube.com/playlist?list=PLlVlyGVtvuVnv4qfRHDDBXm2e757jt9I3"
        ]
        
        logger.info("📋 Building playlist index (2024-26)...")
        
        for url in playlists:
            try:
                cmd = [
                    "yt-dlp", "--flat-playlist", 
                    "--print", "%(title)s|||%(id)s",
                    url
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if '|||' in line:
                            try:
                                title, video_id = line.split('|||')
                                # Parse: "BULLS at NETS | FULL GAME HIGHLIGHTS | January 16, 2026"
                                parts = title.split('|')
                                if len(parts) >= 3 and 'FULL GAME HIGHLIGHTS' in parts[1]:
                                    teams_part = parts[0].strip()
                                    date_part = parts[2].strip()
                                    
                                    # Strip "EXTENDED:" prefix
                                    if teams_part.startswith("EXTENDED:"):
                                        teams_part = teams_part[9:].strip()
                                    
                                    if ' at ' in teams_part:
                                        away, home = teams_part.split(' at ')
                                        away = away.strip().upper().replace(" ", "")
                                        home = home.strip().upper().replace(" ", "")
                                        
                                        key = f"{home}_{away}_{date_part}"
                                        self.playlist_index[key] = video_id
                            except:
                                continue
                else:
                    logger.warning(f"Failed to index playlist {url}")
                    
            except Exception as e:
                logger.warning(f"Error indexing playlist {url}: {e}")
                
        logger.info(f"✅ Indexed {len(self.playlist_index)} videos from {len(playlists)} playlists")
    
    def download_video(self, home: str, away: str, date: str) -> Optional[Path]:
        """Download YouTube highlight for a game using playlist index."""
        # Convert date to playlist format: "January 16, 2026"
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        date_str = date_obj.strftime("%B %d, %Y")  # Playlist usually has comma
        
        # Normalize team names to uppercase short form (no spaces)
        # "Trail Blazers" -> "TRAILBLAZERS"
        # "76ers" -> "76ERS"
        home_upper = home.upper().replace(" ", "")
        away_upper = away.upper().replace(" ", "")
        
        # Try to find video in playlist index
        # We try multiple date formats just in case
        possible_keys = [
            f"{home_upper}_{away_upper}_{date_str}",  # "BULLS_NETS_January 16, 2026"
            f"{home_upper}_{away_upper}_{date_obj.strftime('%B %d %Y')}", # No comma
            f"{home_upper}_{away_upper}_{date_obj.strftime('%b %d, %Y')}", # Short month
        ]
        
        video_id = None
        for key in possible_keys:
            if key in self.playlist_index:
                video_id = self.playlist_index[key]
                logger.info(f"🎯 Found in playlist: {key}")
                break
        
        # If not found, try fuzzy match on date only (if strictly one game per matchup per day)
        if not video_id:
            for idx_key, vid_id in self.playlist_index.items():
                # Check if teams match and date is close or matches
                if home_upper in idx_key and away_upper in idx_key:
                    # Very simple date check - if month and day match
                    if date_obj.strftime("%B %d") in idx_key:
                        video_id = vid_id
                        logger.info(f"🎯 Fuzzy match in playlist: {idx_key}")
                        break
        
        output_path = TEMP_VIDEO_DIR / f"temp_{date}_{home}_{away}.mp4"
        
        # Clean up any existing temp video
        for old_file in TEMP_VIDEO_DIR.glob("temp_*.mp4"):
            try:
                old_file.unlink()
            except:
                pass
        
        try:
            if video_id:
                # Direct download from video ID
                url = f"https://www.youtube.com/watch?v={video_id}"
                logger.info(f"📥 Downloading from playlist: {video_id}")
            else:
                # Fallback to search
                home_full = TEAM_NAMES.get(home, home)
                away_full = TEAM_NAMES.get(away, away)
                date_str_search = date_obj.strftime("%B %d %Y")
                query = f"{away_full} vs {home_full} Full Game Highlights {date_str_search}"
                url = f"ytsearch1:{query}"
                logger.info(f"🔍 Searching (not in playlist): {query}")
            
            cmd = [
                "yt-dlp",
                url,
                "-o", str(output_path),
                "-f", "best[height<=480]",  # Lower quality for speed
                "--max-filesize", "150M",
                "--no-playlist",
                # Removed --quiet and --no-warnings to see errors
            ]
            
            logger.info(f"📂 Output path: {output_path}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)  # 60s timeout
            
            if result.returncode == 0 and output_path.exists():
                file_size = output_path.stat().st_size / (1024 * 1024)
                logger.info(f"✅ Downloaded: {file_size:.1f} MB")
                return output_path
            else:
                # Log the error
                if result.stderr:
                    logger.warning(f"yt-dlp error: {result.stderr[:200]}")
                if result.stdout:
                    logger.info(f"yt-dlp output: {result.stdout[:200]}")
                logger.warning(f"Return code: {result.returncode}, File exists: {output_path.exists()}")
                return None
                
        except Exception as e:
            logger.warning(f"Download failed: {e}")
            return None
    
    def analyze_video_with_cnn(self, video_path: Path) -> float:
        """
        Run Vision CNN (3D) on video and return visual form score.
        
        The 3D CNN expects input of shape: (batch, num_frames, 3, H, W)
        We sample multiple 16-frame clips and average the predictions.
        """
        if not self.vision_loaded or self.vision_model is None:
            return 0.5  # Neutral if no CNN
        
        try:
            cap = cv2.VideoCapture(str(video_path))
            
            if not cap.isOpened():
                return 0.5
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            num_frames = getattr(self, 'vision_num_frames', 16)
            
            if total_frames < num_frames:
                cap.release()
                return 0.5
            
            # Sample 5 non-overlapping clips of 16 frames each
            num_clips = min(5, total_frames // num_frames)
            clip_starts = np.linspace(0, total_frames - num_frames, num_clips, dtype=int)
            
            all_scores = []
            
            for clip_start in clip_starts:
                frames = []
                for i in range(num_frames):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, clip_start + i)
                    ret, frame = cap.read()
                    
                    if not ret:
                        break
                    
                    # Preprocess frame
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_resized = cv2.resize(frame_rgb, (224, 224))
                    
                    # Normalize (ImageNet stats)
                    frame_tensor = torch.from_numpy(frame_resized).float() / 255.0
                    frame_tensor = (frame_tensor - torch.tensor([0.485, 0.456, 0.406])) / torch.tensor([0.229, 0.224, 0.225])
                    frame_tensor = frame_tensor.permute(2, 0, 1)  # HWC -> CHW
                    frames.append(frame_tensor)
                
                if len(frames) < num_frames:
                    continue
                
                # Stack frames: (num_frames, 3, H, W) -> (1, num_frames, 3, H, W)
                clip_tensor = torch.stack(frames).unsqueeze(0)
                
                # Run 3D CNN
                with torch.no_grad():
                    logits = self.vision_model(clip_tensor)
                    probs = torch.softmax(logits, dim=1)
                    
                    # Score: probability of "make" classes
                    # Labels: 2p0=miss, 2p1=make, 3p0=miss, 3p1=make, etc.
                    # Make classes: indices 1, 3, 5, 7
                    make_prob = probs[0, [1, 3, 5, 7]].sum().item()
                    all_scores.append(make_prob)
            
            cap.release()
            
            if len(all_scores) == 0:
                return 0.5
            
            # Average score across clips, normalized to 0.3-0.7 range
            avg_score = np.mean(all_scores)
            vision_score = 0.3 + (avg_score * 0.4)  # Map to [0.3, 0.7]
            
            return vision_score
            
        except Exception as e:
            logger.warning(f"CNN analysis failed: {e}")
            return 0.5
    
    def warm_up_state(self, cutoff_date: str):
        """Pre-process all games before the simulation start to initialize ELO and streaks."""
        logger.info(f"🔥 Warming up World State with games before {cutoff_date}...")
        df = pd.read_csv("data/nba_games_enhanced.csv")
        df['date'] = pd.to_datetime(df['date'])
        
        # Get all games before cutoff
        past_games = df[df['date'] < cutoff_date].sort_values('date')
        
        # Update state sequentially without predicting
        for _, row in past_games.iterrows():
            self.world_state.update(row['home'], row['away'], row['date'], row['home_win'])
            
        logger.info(f"✅ State warmed up for {len(self.world_state.elo_ratings)} teams")

    def predict_game(self, home: str, away: str, date: str, 
                     home_vision_score: float, away_vision_score: float,
                     row: pd.Series = None) -> float:
        """
        Run HIGH-FIDELITY World Model prediction using real Ensemble + State.
        """
        # 1. Get Live Features from Running State
        features = self.world_state.get_team_features(home, away, date)
        
        # 2. Add Vision Scores to features if model expects them (optional bridge)
        # Actually, we use Late Fusion for Vision as per the architecture diagram
        
        # 3. COMPONENT 1: REAL ENSEMBLE (XGBoost + LightGBM + CatBoost)
        X = pd.DataFrame([features])
        # Ensure we only use columns the model was trained on
        model_features = self.ensemble.feature_names
        # Reorder to match model's expected order
        X_input = X[model_features]
        
        base_prob = self.ensemble.predict_ensemble(X_input)[0]
        
        # 4. COMPONENT 2: MOMENTUM TRANSFORMER
        momentum_delta, _ = self.momentum.get_matchup_momentum_delta(
            home, away, current_date=date, games_df=self.games_df
        )
        
        # 5. COMPONENT 3: CHEMISTRY GNN (progressive)
        chem_diff = self.chemistry.get_chemistry_differential(
            home, away, current_date=date, games_df=self.games_df
        )
        chem_delta = chem_diff * 0.1
        
        # 6. COMPONENT 4: VISION CNN (REAL from video!)
        vision_diff = home_vision_score - away_vision_score
        vision_delta = vision_diff * 0.15
        
        # LATE FUSION (4 COMPONENTS)
        final_prob = base_prob + momentum_delta + chem_delta + vision_delta
        final_prob = np.clip(final_prob, 0.05, 0.95)
        
        return final_prob

    # Removed _get_team_strength and _get_past_games as they are covered by WorldState
    
    def _get_past_games(self, team: str, current_date: str, limit: int = 5) -> list:
        """Get past N games for a team before the current date."""
        try:
            target_date = pd.to_datetime(current_date)
            past_games = self.games_df[
                ((self.games_df['home'] == team) | (self.games_df['away'] == team)) &
                (self.games_df['date'] < target_date)
            ].sort_values('date', ascending=False).head(limit)
            return past_games.to_dict('records')
        except Exception as e:
            logger.warning(f"Error getting past games for {team}: {e}")
            return []
    
    def _download_past_game_video(self, game: dict) -> Optional[Path]:
        """Download video for a past game and cache it."""
        home = game['home']
        away = game['away']
        date = game['date'].strftime('%Y-%m-%d') if hasattr(game['date'], 'strftime') else str(game['date'])[:10]
        
        # Check if already cached
        cache_key = f"{date}_{home}_{away}"
        cache_path = self.video_cache_dir / f"{cache_key}.mp4"
        
        if cache_path.exists():
            return cache_path
        
        # Download using existing method
        video_path = self.download_video(home, away, date)
        
        if video_path and video_path.exists():
            # Move to cache
            try:
                import shutil
                shutil.move(str(video_path), str(cache_path))
                return cache_path
            except:
                return video_path
        
        return None
    
    def get_team_vision_score(self, team: str, current_date: str) -> tuple:
        """
        Get vision score for a team based on their PAST games (pregame only!).
        Returns (score, num_games_analyzed).
        """
        # Get past games for this team
        past_games = self._get_past_games(team, current_date, limit=self.max_videos_per_team)
        
        if len(past_games) < self.min_games_for_vision:
            logger.info(f"   📊 {team}: Only {len(past_games)} past games (need {self.min_games_for_vision}) → neutral")
            return 0.5, len(past_games)  # Not enough history = neutral
        
        # Analyze each past game's video
        scores = []
        for game in past_games[:self.max_videos_per_team]:
            video_path = self._download_past_game_video(game)
            if video_path:
                score = self.analyze_video_with_cnn(video_path)
                scores.append(score)
        
        if len(scores) == 0:
            return 0.5, 0
        
        # Weight recent games higher (exponential decay)
        weights = [0.35, 0.25, 0.20, 0.12, 0.08][:len(scores)]
        weights = [w / sum(weights) for w in weights]  # Normalize
        
        weighted_score = sum(s * w for s, w in zip(scores, weights))
        return weighted_score, len(scores)
    
    def _cleanup_old_cache(self):
        """Remove old cached videos - keep only last 5 games per team to save disk space."""
        import re
        from collections import defaultdict
        
        team_videos = defaultdict(list)  # {team: [(path, mtime), ...]}
        
        for cache_file in self.video_cache_dir.glob("*.mp4"):
            # Parse team from filename like "cache_2025-01-15_Celtics_Heat.mp4"
            name = cache_file.stem
            parts = name.split("_")
            if len(parts) >= 4:
                home, away = parts[2], parts[3]
                mtime = cache_file.stat().st_mtime
                team_videos[home].append((cache_file, mtime))
                team_videos[away].append((cache_file, mtime))
        
        # For each team, keep only the 5 most recent videos
        files_to_delete = set()
        for team, videos in team_videos.items():
            sorted_videos = sorted(videos, key=lambda x: x[1], reverse=True)  # newest first
            for path, _ in sorted_videos[self.max_videos_per_team:]:
                files_to_delete.add(path)
        
        for old_file in files_to_delete:
            try:
                old_file.unlink()
                logger.info(f"🗑️ Cleaned old cache: {old_file.name}")
            except:
                pass
    
    def evaluate_game(self, row: pd.Series) -> Dict:
        """
        Evaluate a single game using PREGAME data only.
        Vision CNN analyzes each team's PAST games (not current game!).
        """
        home = row['home']
        away = row['away']
        date = row['date'].strftime('%Y-%m-%d')
        actual_home_win = row['home_win']
        
        logger.info(f"🎮 {away} @ {home} ({date})")
        
        # ============================================================
        # STEP 1: Get HISTORICAL vision scores (pregame only!)
        # ============================================================
        logger.info(f"   📹 Analyzing {home}'s past games...")
        home_vision, home_games_analyzed = self.get_team_vision_score(home, date)
        
        logger.info(f"   📹 Analyzing {away}'s past games...")
        away_vision, away_games_analyzed = self.get_team_vision_score(away, date)
        
        video_used = (home_games_analyzed >= self.min_games_for_vision or 
                      away_games_analyzed >= self.min_games_for_vision)
        
        logger.info(f"   📊 Vision: {home}={home_vision:.3f} ({home_games_analyzed} games), {away}={away_vision:.3f} ({away_games_analyzed} games)")
        
        # ============================================================
        # STEP 2: Run World Model prediction (all pregame data)
        # ============================================================
        predicted_prob = self.predict_game(home, away, date, home_vision, away_vision, row=row)
        predicted_home_win = 1 if predicted_prob > 0.5 else 0
        correct = predicted_home_win == actual_home_win
        
        # ============================================================
        # STEP 3: Cache the CURRENT game's video for future use
        # ============================================================
        # This game's video will be used for FUTURE predictions
        current_video = self.download_video(home, away, date)
        if current_video:
            try:
                cache_key = f"{date}_{home}_{away}"
                cache_path = self.video_cache_dir / f"{cache_key}.mp4"
                import shutil
                shutil.move(str(current_video), str(cache_path))
                logger.info(f"   💾 Cached video for future predictions")
            except Exception as e:
                if current_video.exists():
                    current_video.unlink()
        
        # Update World State with the ACTUAL result after prediction
        # (keeping the simulation progressive)
        self.world_state.update(home, away, date, actual_home_win)
        
        # Cleanup old cache periodically
        if len(self.results) % 20 == 0:
            self._cleanup_old_cache()
        
        result = {
            "date": date,
            "home": home,
            "away": away,
            "home_pts": row['home_pts'],
            "away_pts": row['away_pts'],
            "actual_home_win": int(actual_home_win),
            "predicted_prob": round(predicted_prob, 4),
            "predicted_home_win": predicted_home_win,
            "correct": correct,
            "video_used": video_used,
            "home_vision_score": round(home_vision, 3),
        }
        
        self.results.append(result)
        
        # Running accuracy
        correct_count = sum(r['correct'] for r in self.results)
        total = len(self.results)
        accuracy = correct_count / total * 100
        
        status = "✅" if correct else "❌"
        logger.info(f"   {status} Predicted: {'HOME' if predicted_home_win else 'AWAY'} | "
                   f"Actual: {'HOME' if actual_home_win else 'AWAY'} | "
                   f"Running Acc: {accuracy:.2f}% ({correct_count}/{total})")
        
        return result
    
    def run_evaluation(self, season: str = "2025-26"):
        """Run full streaming evaluation."""
        print("=" * 70)
        print("🏀 STREAMING WORLD MODEL EVALUATION - REAL VIDEO")
        print("=" * 70)
        
        # Load games
        df = pd.read_csv("data/nba_games_enhanced.csv")
        df['date'] = pd.to_datetime(df['date'])
        
        if season == "2025-26":
            # Start from Oct 21 (first regular season game in playlist)
            games = df[(df['date'] >= '2025-10-21') & (df['date'] <= '2026-06-30')]
        else:
            games = df[(df['date'] >= '2024-10-01') & (df['date'] <= '2025-06-30')]
        
        games = games.sort_values('date').reset_index(drop=True)
        print(f"\n📅 Evaluating {len(games)} games from {season} season")
        print(f"   Date range: {games['date'].min().strftime('%Y-%m-%d')} to {games['date'].max().strftime('%Y-%m-%d')}")
        print()
        
        # WARM UP STATE
        self.warm_up_state(games['date'].min().strftime('%Y-%m-%d'))
        
        start_time = time.time()
        
        for idx, row in games.iterrows():
            self.evaluate_game(row)
            
            # Save intermediate results every 10 games for robustness
            if len(self.results) % 10 == 0 and len(self.results) > 0:
                self._save_results(season, partial=True)
                logger.info(f"📊 Checkpoint: {sum(r['correct'] for r in self.results)}/{len(self.results)} correct ({sum(r['correct'] for r in self.results)/len(self.results)*100:.1f}%)")
        
        # Final save
        self._save_results(season, partial=False)
        
        elapsed = time.time() - start_time
        
        # Final summary
        print("\n" + "=" * 70)
        print("📊 FINAL RESULTS")
        print("=" * 70)
        
        correct = sum(r['correct'] for r in self.results)
        total = len(self.results)
        videos_used = sum(r['video_used'] for r in self.results)
        
        print(f"   Total Games: {total}")
        print(f"   Correct Predictions: {correct}")
        print(f"   ACCURACY: {correct/total*100:.2f}%")
        print(f"   Videos Successfully Analyzed: {videos_used}/{total} ({videos_used/total*100:.1f}%)")
        print(f"   Time Elapsed: {elapsed/3600:.1f} hours")
        print("=" * 70)
    
    def _save_results(self, season: str, partial: bool = False):
        """Save results to JSON."""
        suffix = "_partial" if partial else "_final"
        output_file = RESULTS_DIR / f"real_video_eval_{season}{suffix}.json"
        
        correct = sum(r['correct'] for r in self.results)
        total = len(self.results)
        
        data = {
            "season": season,
            "timestamp": datetime.now().isoformat(),
            "total_games": total,
            "correct_predictions": correct,
            "accuracy": correct / total if total > 0 else 0,
            "games": self.results,
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"💾 Results saved to {output_file}")


def main():
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", default="2025-26", choices=["2024-25", "2025-26", "all"])
    args = parser.parse_args()
    
    # DETERMINE MODEL DIRECTORY
    # Basic logic: Use historical model if available to avoid data leakage
    hist_dir = Path("artifacts/models/historical_2024")
    
    if hist_dir.exists() and (hist_dir / "xgb_model.pkl").exists():
        logger.info(f"🔙 Using Historical Models ({hist_dir}) for valid time-series evaluation")
        model_dir = str(hist_dir)
    else:
        logger.warning("⚠️ Historical models not found. Using 'pregame' (WARNING: Potential Data Leakage if trained on 2026 data)")
        model_dir = "artifacts/models/pregame"
    
    # Determine seasons to run
    if args.season == "all":
        seasons = ["2024-25", "2025-26"]
    else:
        seasons = [args.season]

    # Initialize evaluator ONCE - state will persist across seasons when running "all"
    evaluator = StreamingWorldModelEvaluator(model_dir=model_dir)
    
    for season in seasons:
        logger.info(f"\n{'='*60}\n🏀 STARTING SIMULATION FOR SEASON: {season}\n{'='*60}")
        evaluator.run_evaluation(season)


if __name__ == "__main__":
    main()
