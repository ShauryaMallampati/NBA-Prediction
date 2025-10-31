"""Basketball-Reference scraper for player load management and validation data.

This module scrapes Basketball-Reference to:
1. Get player season stats (games played, minutes, trends)
2. Detect load management patterns (11, 14, 25+ game cycles)
3. Track recent form (hot vs cold stretches)
4. Provide validation data for model predictions

Key insight from expert bettors:
"If a player is averaging 11 games on, 14 games off..."
This scraper detects exactly that pattern for rest risk adjustment.
"""

import time
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

from src.common.logger import setup_logger

logger = setup_logger(__name__)


class BasketballReferenceLoader:
    """Polite scraper for Basketball-Reference data."""

    BASE_URL = "https://www.basketball-reference.com"
    RATE_LIMIT_DELAY = 3.0  # seconds between requests (polite scraping)

    def __init__(self) -> None:
        """Initialize scraper with rate limiting."""
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        self.last_request_time = 0.0

    def _rate_limit(self) -> None:
        """Enforce polite rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def _safe_get(self, url: str) -> Optional[str]:
        """Make a safe GET request with error handling."""
        try:
            self._rate_limit()
            logger.debug(f"GET {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)[:100]}")
            return None

    def get_season_schedule(self, season: int) -> pd.DataFrame:
        """Scrape season schedule from Basketball-Reference.
        
        Args:
            season: Season year (e.g., 2023)
            
        Returns:
            DataFrame with game information
        """
        url = f"{self.BASE_URL}/leagues/NBA_{season}_games.html"
        html = self._safe_get(url)
        
        if not html:
            logger.warning(f"Could not fetch schedule for season {season}")
            return pd.DataFrame()
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", {"id": "schedule"})
            
            if not table:
                logger.warning(f"No schedule table found for season {season}")
                return pd.DataFrame()
            
            # Use pandas to parse the HTML table
            df = pd.read_html(str(table))[0]
            logger.info(f"Scraped {len(df)} games for season {season}")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing schedule table: {str(e)[:100]}")
            return pd.DataFrame()

    def get_player_season_stats(self, season: int) -> pd.DataFrame:
        """Scrape season-long player statistics.
        
        Args:
            season: Season year (e.g., 2023)
            
        Returns:
            DataFrame with player season stats (G, MP, PPG, RPG, APG, SPG, BPG, etc.)
        """
        url = f"{self.BASE_URL}/leagues/NBA_{season}_per_game.html"
        html = self._safe_get(url)
        
        if not html:
            logger.warning(f"Could not fetch season stats for {season}")
            return pd.DataFrame()
        
        try:
            # Read all tables and find the per_game table
            tables = pd.read_html(html)
            
            # Basketball-Reference puts player stats in first table
            df = tables[0]
            
            # Clean up column names
            df.columns = df.columns.str.lower().str.strip()
            
            # Filter out header rows
            df = df[df['player'] != 'Player'].copy()
            
            logger.info(f"Scraped season stats for {len(df)} players in season {season}")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing season stats table: {str(e)[:100]}")
            return pd.DataFrame()

    def get_player_game_log(self, player_id: str, season: int) -> pd.DataFrame:
        """Scrape player's game-by-game log for a season.
        
        This is critical for detecting load management patterns.
        
        Args:
            player_id: BR player ID (e.g., 'jamesle01')
            season: Season year (e.g., 2023)
            
        Returns:
            DataFrame with game-by-game stats including games_played indicator
        """
        url = f"{self.BASE_URL}/players/{player_id[0]}/{player_id}/gamelog/{season}"
        html = self._safe_get(url)
        
        if not html:
            logger.warning(f"Could not fetch game log for {player_id} season {season}")
            return pd.DataFrame()
        
        try:
            tables = pd.read_html(html)
            
            # Game log is usually first or second table
            df = None
            for table in tables:
                if 'Date' in table.columns or 'G#' in table.columns:
                    df = table
                    break
            
            if df is None or df.empty:
                logger.warning(f"No game log found for {player_id} season {season}")
                return pd.DataFrame()
            
            # Extract minutes played as proxy for games played
            df = df[['Date', 'G#', 'GS', 'MP', 'FG', 'FGA', 'FG%', 'FT', 'FTA', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PTS']].copy()
            
            # Create games_played indicator (1 if MP > 0, 0 if DNP)
            df['games_played'] = (pd.to_numeric(df['MP'], errors='coerce').fillna(0) > 0).astype(int)
            
            logger.info(f"Scraped {len(df)} games for {player_id} season {season}")
            return df
            
        except Exception as e:
            logger.error(f"Error parsing game log for {player_id}: {str(e)[:100]}")
            return pd.DataFrame()

    def detect_load_management(self, games_played_array: List[int]) -> Dict[str, float]:
        """Detect load management patterns from games_played array.
        
        Analyzes the pattern of games played vs sat out over a season.
        Example: [1, 1, 1, 0, 1, 1, 1, 1, 0, ...] suggests 8-games-on, 1-game-off pattern.
        
        Args:
            games_played_array: List of 1s (played) and 0s (sat out) over season
            
        Returns:
            Dictionary with pattern info:
            - on_games: Average games played in consecutive stretches
            - off_games: Average games sat out in consecutive stretches
            - consistency: How consistent is the pattern (0-1)
            - rest_risk: Estimated rest risk for next game
        """
        if not games_played_array or len(games_played_array) < 10:
            return {
                "on_games": 0.0,
                "off_games": 0.0,
                "consistency": 0.0,
                "rest_risk": 0.0,
            }
        
        arr = np.array(games_played_array)
        
        try:
            # Detect stretches of consecutive 1s and 0s
            on_stretches = []
            off_stretches = []
            
            current_state = arr[0]
            current_length = 1
            
            for i in range(1, len(arr)):
                if arr[i] == current_state:
                    current_length += 1
                else:
                    if current_state == 1:
                        on_stretches.append(current_length)
                    else:
                        off_stretches.append(current_length)
                    current_state = arr[i]
                    current_length = 1
            
            # Don't forget last stretch
            if current_state == 1:
                on_stretches.append(current_length)
            else:
                off_stretches.append(current_length)
            
            # Compute statistics
            avg_on = np.mean(on_stretches) if on_stretches else 0.0
            avg_off = np.mean(off_stretches) if off_stretches else 0.0
            
            # Consistency: how similar are the on/off stretches?
            on_std = np.std(on_stretches) if len(on_stretches) > 1 else 0.0
            off_std = np.std(off_stretches) if len(off_stretches) > 1 else 0.0
            
            # Consistency score: lower std = more consistent (0 = perfect pattern, 1 = erratic)
            consistency = 1.0 - min(1.0, (on_std + off_std) / (avg_on + avg_off + 1e-6))
            
            # Rest risk: likelihood of sitting next game
            # If avg_off > 0, there's a pattern of sitting out
            rest_risk = (avg_off / (avg_on + avg_off)) if (avg_on + avg_off) > 0 else 0.0
            
            return {
                "on_games": float(avg_on),
                "off_games": float(avg_off),
                "consistency": float(consistency),
                "rest_risk": float(rest_risk),
            }
            
        except Exception as e:
            logger.error(f"Error detecting load management: {str(e)}")
            return {
                "on_games": 0.0,
                "off_games": 0.0,
                "consistency": 0.0,
                "rest_risk": 0.0,
            }

    def get_recent_form(self, df_game_log: pd.DataFrame, last_n_games: int = 10) -> Dict[str, float]:
        """Analyze recent form from game log.
        
        Compares recent performance to season average.
        
        Args:
            df_game_log: Game log DataFrame
            last_n_games: Number of recent games to analyze
            
        Returns:
            Dictionary with recent form analysis
        """
        if df_game_log.empty or len(df_game_log) < 5:
            return {
                "recent_ppg": 0.0,
                "recent_rpg": 0.0,
                "recent_apg": 0.0,
                "recent_trend": 0.0,  # positive = improving, negative = declining
                "recent_consistency": 0.0,
            }
        
        try:
            # Get numeric columns
            df = df_game_log.copy()
            for col in ['PTS', 'TRB', 'AST']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Recent games
            recent = df.tail(last_n_games)
            
            recent_ppg = float(recent['PTS'].mean()) if 'PTS' in recent.columns else 0.0
            recent_rpg = float(recent['TRB'].mean()) if 'TRB' in recent.columns else 0.0
            recent_apg = float(recent['AST'].mean()) if 'AST' in recent.columns else 0.0
            
            # Trend: compare first half vs second half of recent games
            if len(recent) >= 2:
                mid = len(recent) // 2
                first_half_avg = recent['PTS'].iloc[:mid].mean()
                second_half_avg = recent['PTS'].iloc[mid:].mean()
                trend = float(second_half_avg - first_half_avg)
            else:
                trend = 0.0
            
            # Consistency in recent games
            consistency = float(recent['PTS'].std()) if len(recent) > 1 else 0.0
            
            return {
                "recent_ppg": recent_ppg,
                "recent_rpg": recent_rpg,
                "recent_apg": recent_apg,
                "recent_trend": trend,
                "recent_consistency": consistency,
            }
            
        except Exception as e:
            logger.error(f"Error calculating recent form: {str(e)}")
            return {
                "recent_ppg": 0.0,
                "recent_rpg": 0.0,
                "recent_apg": 0.0,
                "recent_trend": 0.0,
                "recent_consistency": 0.0,
            }

    def extract_player_season_data(self, player_id: str, player_name: str, season: int) -> Dict[str, float]:
        """Extract all relevant data for a player in a season.
        
        Combines game log analysis and load management detection.
        
        Args:
            player_id: BR player ID
            player_name: Player name
            season: Season year
            
        Returns:
            Dictionary with comprehensive player data
        """
        # Get game log
        df_game_log = self.get_player_game_log(player_id, season)
        
        if df_game_log.empty:
            logger.warning(f"No game log for {player_name} ({player_id})")
            return {}
        
        # Detect load management
        games_played_list = df_game_log['games_played'].tolist() if 'games_played' in df_game_log.columns else []
        load_mgmt = self.detect_load_management(games_played_list)
        
        # Get recent form
        recent_form = self.get_recent_form(df_game_log, last_n_games=10)
        
        # Combine all data
        player_data = {
            "player_id": player_id,
            "player_name": player_name,
            "season": season,
            "games_played": len([x for x in games_played_list if x == 1]),
            "games_missed": len([x for x in games_played_list if x == 0]),
        }
        player_data.update(load_mgmt)
        player_data.update(recent_form)
        
        logger.info(f"Extracted data for {player_name}: {load_mgmt['on_games']:.1f}on/{load_mgmt['off_games']:.1f}off pattern")
        
        return player_data

