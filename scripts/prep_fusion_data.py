
import pandas as pd
import numpy as np
import logging
from pathlib import Path
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleFeatureEngine:
    def __init__(self):
        self.team_elo = {}  # team -> rating
        self.team_streak = {} # team -> current streak (+wins, -losses)
        self.team_form = {} # team -> list of last 5 margins
        self.k_factor = 20
        
    def get_elo(self, team):
        return self.team_elo.get(team, 1500.0)
    
    def update_elo(self, home, away, home_win):
        r_home = self.get_elo(home)
        r_away = self.get_elo(away)
        
        # Expected home win prob
        e_home = 1 / (1 + 10 ** ((r_away - r_home) / 400))
        
        actual = 1.0 if home_win else 0.0
        delta = self.k_factor * (actual - e_home)
        
        self.team_elo[home] = r_home + delta
        self.team_elo[away] = r_away - delta
        
        return e_home # Pre-update probability
        
    def update_streak(self, team, won):
        current = self.team_streak.get(team, 0)
        if won:
            self.team_streak[team] = current + 1 if current > 0 else 1
        else:
            self.team_streak[team] = current - 1 if current < 0 else -1
            
    def update_form(self, team, margin):
        # margin is positive if team won, negative if lost
        history = self.team_form.get(team, [])
        history.append(margin)
        if len(history) > 5:
            history.pop(0)
        self.team_form[team] = history
        
    def get_form_score(self, team):
        history = self.team_form.get(team, [])
        if not history:
            return 0.0
        return np.mean(history) # Avg margin last 5 games

def prepare_fusion_data():
    logger.info("🚀 Starting Fusion Data Preparation (Standalone)...")
    
    # 1. Load Data
    games_path = Path("data/nba_games_enhanced.csv")
    if not games_path.exists():
        logger.error("❌ nba_games_enhanced.csv not found!")
        return
    
    df = pd.read_csv(games_path)
    
    # Sort by date essential for rolling stats
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Filter for training period
    # We run stats on ALL data to warm up Elo, but only SAVE pre-2024
    cutoff_date = pd.to_datetime('2024-10-01')
    
    engine = SimpleFeatureEngine()
    dataset = []
    
    logger.info(f"📊 Processing {len(df)} games to generate features...")
    
    for _, row in tqdm(df.iterrows(), total=len(df)):
        home = row['home']
        away = row['away']
        home_score = row['home_pts']
        away_score = row['away_pts']
        home_win = 1 if home_score > away_score else 0
        date = row['date']
        
        # 1. PREDICT PHASE (Get features BEFORE update)
        
        # A. Base Prob (Elo)
        base_prob = 1 / (1 + 10 ** ((engine.get_elo(away) - engine.get_elo(home)) / 400))
        
        # B. Momentum Delta (Streak Diff)
        # Scale: +10 streak diff ~= +0.05 prob
        streak_diff = engine.team_streak.get(home, 0) - engine.team_streak.get(away, 0)
        mom_delta = np.clip(streak_diff * 0.005, -0.05, 0.05)
        
        # C. Vision Delta Proxy (Form/Margin Diff)
        # Teams winning by big margins typically "look good" (Vision)
        form_home = engine.get_form_score(home)
        form_away = engine.get_form_score(away)
        vis_delta = np.clip((form_home - form_away) * 0.003, -0.05, 0.05)
        
        # D. Chemistry Delta (Stability Proxy)
        # Assume chemistry ~ consistent winning (using Elo)
        chem_delta = np.clip((engine.get_elo(home) - engine.get_elo(away)) * 0.0001, -0.03, 0.03)
        
        # E. Missing Modalities
        aud_delta = 0.0
        flow_delta = 0.0
        pbp_delta = 0.0
        
        # Save if within training window
        if date < cutoff_date:
            dataset.append({
                "base_prob": float(base_prob),
                "vis_delta": float(vis_delta),
                "aud_delta": float(aud_delta),
                "flow_delta": float(flow_delta),
                "chem_delta": float(chem_delta),
                "mom_delta": float(mom_delta),
                "pbp_delta": float(pbp_delta),
                "home_win": int(home_win)
            })
            
        # 2. UPDATE PHASE
        engine.update_elo(home, away, home_win)
        engine.update_streak(home, home_win)
        engine.update_streak(away, not home_win) # Away win = not home win
        
        margin = home_score - away_score
        engine.update_form(home, margin)
        engine.update_form(away, -margin)
    
    # 3. Save
    out_df = pd.DataFrame(dataset)
    save_path = "data/fusion_training_data.csv"
    out_df.to_csv(save_path, index=False)
    logger.info(f"✅ Generated {len(out_df)} training samples (pre-2024)")
    logger.info("Sample Data:")
    print(out_df.tail())

if __name__ == "__main__":
    prepare_fusion_data()
