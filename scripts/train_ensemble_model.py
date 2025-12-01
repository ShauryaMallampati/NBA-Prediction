"""
Train the NBA Ensemble Model System
Uses collected data to train 5+ ML algorithms
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict

from src.models.ensemble_model import NBAEnsembleModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_betting_data() -> Dict:
    """Load collected betting odds data"""
    logger.info("📂 Loading betting data...")
    
    data_dir = Path("data/raw/rapid_api_working")
    
    # Find most recent data file
    data_files = sorted(data_dir.glob("nba_comprehensive_*.json"))
    
    if not data_files:
        logger.error("❌ No betting data found!")
        return {}
    
    latest_file = data_files[-1]
    logger.info(f"   Loading: {latest_file.name}")
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    return data


def create_features_from_odds(odds_data: Dict) -> pd.DataFrame:
    """
    Create features from betting odds data
    
    Features include:
    - Opening odds
    - Current odds
    - Line movement
    - Spread
    - Total points
    - Bookmaker consensus
    """
    logger.info("\n🔧 Engineering features from odds data...")
    
    games_data = []
    
    # Get NBA odds - new structure has endpoints dict
    endpoints = odds_data.get('endpoints', {})
    nba_odds = endpoints.get('nba_odds', [])
    
    logger.info(f"   Processing {len(nba_odds)} games...")
    
    for game in nba_odds:
        try:
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            
            # Get bookmaker data
            bookmakers = game.get('bookmakers', [])
            
            if not bookmakers:
                continue
            
            # Extract odds from multiple bookmakers
            h2h_odds = []
            spreads = []
            totals = []
            
            for bookmaker in bookmakers:
                markets = bookmaker.get('markets', [])
                
                for market in markets:
                    market_key = market.get('key', '')
                    outcomes = market.get('outcomes', [])
                    
                    if market_key == 'h2h':
                        # Head to head odds
                        for outcome in outcomes:
                            if outcome.get('name') == home_team:
                                h2h_odds.append(('home', outcome.get('price', 0)))
                            elif outcome.get('name') == away_team:
                                h2h_odds.append(('away', outcome.get('price', 0)))
                    
                    elif market_key == 'spreads':
                        # Point spreads
                        for outcome in outcomes:
                            if outcome.get('name') == home_team:
                                spreads.append(('home', outcome.get('point', 0)))
                            elif outcome.get('name') == away_team:
                                spreads.append(('away', outcome.get('point', 0)))
                    
                    elif market_key == 'totals':
                        # Over/Under totals
                        for outcome in outcomes:
                            totals.append(outcome.get('point', 0))
            
            # Calculate average odds
            home_odds = [price for team, price in h2h_odds if team == 'home']
            away_odds = [price for team, price in h2h_odds if team == 'away']
            
            home_spreads = [point for team, point in spreads if team == 'home']
            away_spreads = [point for team, point in spreads if team == 'away']
            
            # Create feature row
            features = {
                'game_id': game.get('id', ''),
                'home_team': home_team,
                'away_team': away_team,
                'commence_time': game.get('commence_time', ''),
                
                # Home team odds features
                'home_odds_avg': np.mean(home_odds) if home_odds else 0,
                'home_odds_min': np.min(home_odds) if home_odds else 0,
                'home_odds_max': np.max(home_odds) if home_odds else 0,
                'home_odds_std': np.std(home_odds) if len(home_odds) > 1 else 0,
                
                # Away team odds features
                'away_odds_avg': np.mean(away_odds) if away_odds else 0,
                'away_odds_min': np.min(away_odds) if away_odds else 0,
                'away_odds_max': np.max(away_odds) if away_odds else 0,
                'away_odds_std': np.std(away_odds) if len(away_odds) > 1 else 0,
                
                # Spread features
                'home_spread_avg': np.mean(home_spreads) if home_spreads else 0,
                'away_spread_avg': np.mean(away_spreads) if away_spreads else 0,
                'spread_diff': np.mean(home_spreads) - np.mean(away_spreads) if home_spreads and away_spreads else 0,
                
                # Total points features
                'total_avg': np.mean(totals) if totals else 0,
                'total_std': np.std(totals) if len(totals) > 1 else 0,
                
                # Implied probability (from odds)
                'home_implied_prob': 1 / np.mean(home_odds) if home_odds and np.mean(home_odds) > 0 else 0.5,
                'away_implied_prob': 1 / np.mean(away_odds) if away_odds and np.mean(away_odds) > 0 else 0.5,
                
                # Market efficiency
                'bookmaker_count': len(bookmakers),
                'market_variance': np.var(home_odds + away_odds) if (home_odds or away_odds) else 0,
                
                # Odds ratio
                'odds_ratio': np.mean(home_odds) / np.mean(away_odds) if home_odds and away_odds and np.mean(away_odds) > 0 else 1,
            }
            
            games_data.append(features)
            
        except Exception as e:
            logger.warning(f"   ⚠️ Error processing game: {e}")
            continue
    
    df = pd.DataFrame(games_data)
    
    logger.info(f"   ✅ Created {len(df)} game samples with {len(df.columns)} features")
    
    return df


def create_synthetic_labels(df: pd.DataFrame) -> pd.Series:
    """
    Create synthetic labels based on odds
    
    In production, replace with actual game results
    For now, use implied probability from odds as ground truth
    """
    logger.info("\n🎯 Creating labels...")
    
    # Use implied probability to determine winner
    # If home_implied_prob > away_implied_prob, home wins (1), else away wins (0)
    labels = (df['home_implied_prob'] > df['away_implied_prob']).astype(int)
    
    logger.info(f"   Home wins: {labels.sum()} ({labels.sum()/len(labels)*100:.1f}%)")
    logger.info(f"   Away wins: {len(labels) - labels.sum()} ({(len(labels)-labels.sum())/len(labels)*100:.1f}%)")
    
    return labels


def train_model():
    """Main training function"""
    logger.info("="*80)
    logger.info("🏀 NBA ENSEMBLE MODEL TRAINING")
    logger.info("="*80)
    
    # Load data
    odds_data = load_betting_data()
    
    if not odds_data:
        logger.error("❌ No data available for training!")
        return
    
    # Create features
    df = create_features_from_odds(odds_data)
    
    if len(df) == 0:
        logger.error("❌ No features created!")
        return
    
    logger.info(f"\n📊 Dataset shape: {df.shape}")
    
    # Create labels (synthetic for now)
    y = create_synthetic_labels(df)
    
    # Select feature columns
    feature_cols = [
        'home_odds_avg', 'home_odds_std',
        'away_odds_avg', 'away_odds_std',
        'home_spread_avg', 'away_spread_avg', 'spread_diff',
        'total_avg', 'total_std',
        'home_implied_prob', 'away_implied_prob',
        'bookmaker_count', 'market_variance',
        'odds_ratio'
    ]
    
    X = df[feature_cols]
    
    # Initialize and train ensemble
    logger.info("\n" + "="*80)
    logger.info("🤖 INITIALIZING ENSEMBLE MODEL")
    logger.info("="*80)
    
    ensemble = NBAEnsembleModel()
    
    # Train
    results = ensemble.train(X, y, use_stacking=False)  # Skip stacking for small dataset
    
    # Test predictions
    logger.info("\n" + "="*80)
    logger.info("🎯 TESTING PREDICTIONS")
    logger.info("="*80)
    
    predictions_df = ensemble.predict_with_probabilities(X.head(5))
    
    logger.info("\nSample predictions:")
    for i, row in predictions_df.iterrows():
        logger.info(f"\n   Game {i+1}:")
        logger.info(f"      Prediction: {row['prediction']}")
        logger.info(f"      Home Win: {row['home_win_probability']}%")
        logger.info(f"      Away Win: {row['away_win_probability']}%")
        logger.info(f"      Confidence: {row['confidence']}%")
        logger.info(f"      Model Agreement: {row['models_agree']}")
    
    logger.info("\n" + "="*80)
    logger.info("✅ TRAINING COMPLETE!")
    logger.info("="*80)
    logger.info(f"\n📁 Models saved to: models/ensemble/")
    logger.info(f"🎯 Best model accuracy: {max(results.values()):.4f}")


if __name__ == "__main__":
    train_model()
