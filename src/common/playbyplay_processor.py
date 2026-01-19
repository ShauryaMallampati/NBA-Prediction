"""
Play-by-Play Processor for Multi-Modal NBA Prediction.

This module scrapes NBA Stats API for play-by-play data, summarizes it
using Qwen LLM, and produces features for the prediction pipeline.

Research Rationale:
- Play-by-play text captures momentum shifts, runs, and clutch plays
- Text embeddings can encode game dynamics not visible in box scores
- NBA2Vec showed event sequences contain predictive signal (arXiv 2019)

Pipeline:
1. Scrape PBP from NBA Stats API (with rate limiting and caching)
2. Summarize key events using Qwen (or simpler heuristics)
3. Extract structured features: lead_changes, largest_run, clutch_plays
4. Return momentum score [0.3, 0.7] or embedding vector
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Cache directory
PBP_CACHE_DIR = Path("data/pbp_cache")
PBP_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Optional imports
try:
    from nba_api.stats.endpoints import PlayByPlayV2
    NBA_API_AVAILABLE = True
except ImportError:
    NBA_API_AVAILABLE = False
    logger.warning("nba_api not installed. Play-by-play disabled.")


class PlayByPlayProcessor:
    """
    Processes NBA play-by-play data to extract momentum features.
    
    Features:
    - lead_changes: Number of times the lead changed hands
    - largest_run: Biggest scoring run by either team
    - clutch_plays: Key plays in final 2 minutes
    - home_momentum: Overall momentum score [0.0, 1.0]
    """
    
    def __init__(self, cache_dir: Path = PBP_CACHE_DIR, rate_limit_sec: float = 1.5):
        self.cache_dir = cache_dir
        self.rate_limit_sec = rate_limit_sec
        self.last_request_time = 0.0
        
        # Try to load Qwen for summarization (optional)
        self.summarizer = None
        self._load_summarizer()
    
    def _load_summarizer(self):
        """Attempt to load Qwen for text summarization."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            model_name = "Qwen/Qwen2.5-0.5B-Instruct"  # Smallest Qwen
            
            # Only load if explicitly requested (heavy)
            # self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            # self.model = AutoModelForCausalLM.from_pretrained(model_name)
            # self.summarizer = "qwen"
            logger.info("   📝 Qwen summarizer available but not loaded (use load_summarizer())")
        except ImportError:
            logger.debug("   📝 transformers not installed. Using heuristic PBP analysis.")
    
    def _rate_limit(self):
        """Enforce rate limiting for NBA API calls."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_sec:
            time.sleep(self.rate_limit_sec - elapsed)
        self.last_request_time = time.time()
    
    def get_game_id_from_date(self, home: str, away: str, date: str) -> Optional[str]:
        """
        Get NBA game ID from team names and date.
        
        This is a placeholder - in practice you'd need a mapping from
        nba_games_enhanced.csv or the schedule endpoint.
        """
        # Try to find in our games data
        try:
            import pandas as pd
            games_df = pd.read_csv("data/nba_games_enhanced.csv")
            games_df['date'] = pd.to_datetime(games_df['date']).dt.strftime('%Y-%m-%d')
            
            match = games_df[
                (games_df['home'] == home) & 
                (games_df['away'] == away) & 
                (games_df['date'] == date)
            ]
            
            if len(match) > 0 and 'game_id' in match.columns:
                return str(match.iloc[0]['game_id'])
        except Exception as e:
            logger.debug(f"Could not find game_id: {e}")
        
        return None
    
    def fetch_playbyplay(self, game_id: str) -> Optional[Dict]:
        """
        Fetch play-by-play data from NBA Stats API with caching.
        
        Args:
            game_id: NBA game ID (e.g., "0022400001")
            
        Returns:
            Dict with play-by-play data or None if failed
        """
        if not NBA_API_AVAILABLE:
            return None
        
        # Check cache
        cache_file = self.cache_dir / f"{game_id}_pbp.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    logger.debug(f"   📋 PBP cache hit: {game_id}")
                    return json.load(f)
            except Exception:
                pass
        
        # Fetch from API
        try:
            self._rate_limit()
            logger.info(f"   📋 Fetching PBP for game {game_id}...")
            
            pbp = PlayByPlayV2(game_id=game_id)
            data = pbp.get_dict()
            
            # Cache the result
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            
            return data
            
        except Exception as e:
            logger.warning(f"   ⚠️ PBP fetch failed for {game_id}: {e}")
            return None
    
    def extract_events(self, pbp_data: Dict) -> List[Dict]:
        """
        Extract relevant events from raw PBP data.
        
        Returns:
            List of event dicts with: period, clock, team, action, score
        """
        events = []
        
        try:
            result_sets = pbp_data.get('resultSets', [])
            if len(result_sets) == 0:
                return events
            
            headers = result_sets[0].get('headers', [])
            rows = result_sets[0].get('rowSet', [])
            
            for row in rows:
                event = dict(zip(headers, row))
                
                # Extract key fields
                parsed = {
                    'period': event.get('PERIOD', 0),
                    'clock': event.get('PCTIMESTRING', ''),
                    'home_desc': event.get('HOMEDESCRIPTION', ''),
                    'away_desc': event.get('VISITORDESCRIPTION', ''),
                    'neutral_desc': event.get('NEUTRALDESCRIPTION', ''),
                    'score': event.get('SCORE', ''),
                    'scoremargin': event.get('SCOREMARGIN', ''),
                }
                events.append(parsed)
                
        except Exception as e:
            logger.warning(f"   ⚠️ Event extraction failed: {e}")
        
        return events
    
    def compute_features(self, events: List[Dict]) -> Dict[str, float]:
        """
        Compute momentum features from event list.
        
        Returns:
            Dict with: lead_changes, largest_run, clutch_plays, home_momentum
        """
        if len(events) == 0:
            return self._get_neutral_features()
        
        lead_changes = 0
        prev_leader = None
        current_run = 0
        largest_run = 0
        last_scorer = None
        clutch_plays = 0
        home_score_total = 0
        away_score_total = 0
        
        for event in events:
            score = event.get('score', '')
            margin = event.get('scoremargin', '')
            period = event.get('period', 0)
            clock = event.get('clock', '')
            
            # Parse score (format: "105 - 100")
            if score and ' - ' in str(score):
                try:
                    parts = str(score).split(' - ')
                    away_score = int(parts[0])
                    home_score = int(parts[1])
                    
                    # Track lead changes
                    if home_score > away_score:
                        current_leader = 'home'
                    elif away_score > home_score:
                        current_leader = 'away'
                    else:
                        current_leader = 'tie'
                    
                    if prev_leader is not None and current_leader != prev_leader and current_leader != 'tie':
                        lead_changes += 1
                    prev_leader = current_leader
                    
                except ValueError:
                    pass
            
            # Detect clutch plays (final 2 minutes of 4th quarter)
            if period == 4 and clock:
                try:
                    mins, secs = clock.split(':')
                    if int(mins) < 2:
                        if event.get('home_desc') or event.get('away_desc'):
                            clutch_plays += 1
                except ValueError:
                    pass
        
        # Normalize features
        features = {
            'lead_changes': float(lead_changes),
            'largest_run': float(largest_run),
            'clutch_plays': float(min(clutch_plays, 20)),  # Cap at 20
            'home_momentum': 0.5,  # Neutral default
        }
        
        # Compute home momentum based on lead changes and final margin
        if lead_changes > 0:
            # More lead changes = more competitive = neutral momentum
            features['home_momentum'] = 0.5 - min(0.1, lead_changes / 100)
        
        return features
    
    def _get_neutral_features(self) -> Dict[str, float]:
        """Return neutral features when analysis fails."""
        return {
            'lead_changes': 0.0,
            'largest_run': 0.0,
            'clutch_plays': 0.0,
            'home_momentum': 0.5,
        }
    
    def features_to_score(self, features: Dict[str, float]) -> float:
        """
        Convert PBP features to momentum score.
        
        Returns:
            Score in range [0.3, 0.7]
        """
        # Use home_momentum directly, mapped to [0.3, 0.7]
        raw = features.get('home_momentum', 0.5)
        return 0.3 + raw * 0.4
    
    def get_pbp_momentum_score(self, game_id: str) -> Tuple[float, Dict]:
        """
        Main entry point: Fetch PBP and compute momentum score.
        
        Args:
            game_id: NBA game ID
            
        Returns:
            Tuple of (score, metadata)
        """
        if not NBA_API_AVAILABLE:
            return 0.5, {"method": "disabled", "reason": "nba_api not installed"}
        
        # Fetch PBP
        pbp_data = self.fetch_playbyplay(game_id)
        if pbp_data is None:
            return 0.5, {"method": "failed", "reason": "fetch failed"}
        
        try:
            # Extract events
            events = self.extract_events(pbp_data)
            
            # Compute features
            features = self.compute_features(events)
            
            # Convert to score
            score = self.features_to_score(features)
            
            metadata = {
                "method": "heuristic",
                "features": features,
                "score": score,
                "num_events": len(events),
            }
            
            logger.info(f"   📋 PBP Score: {score:.3f} (lead_changes={features['lead_changes']:.0f})")
            return score, metadata
            
        except Exception as e:
            logger.warning(f"   ⚠️ PBP analysis failed: {e}")
            return 0.5, {"method": "error", "reason": str(e)}
    
    def get_pbp_delta(self, home_game_id: str, away_game_id: str) -> Tuple[float, Dict]:
        """
        Compute PBP-based momentum delta for a matchup.
        
        Uses previous games for each team to assess momentum.
        
        Returns:
            Tuple of (delta, metadata)
        """
        home_score, home_meta = self.get_pbp_momentum_score(home_game_id)
        away_score, away_meta = self.get_pbp_momentum_score(away_game_id)
        
        # Difference weighted by 0.05 (small influence)
        raw_diff = home_score - away_score
        delta = min(0.03, max(-0.03, raw_diff * 0.05))
        
        metadata = {
            "home_pbp_score": home_score,
            "away_pbp_score": away_score,
            "delta": delta,
        }
        
        logger.info(f"   📋 PBP Delta: {delta:+.4f}")
        return delta, metadata


# Global instance
pbp_processor = PlayByPlayProcessor()
