"""
Live NBA Predictions - Make predictions for today's games
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import joblib
import pandas as pd
import requests
from datetime import datetime, timedelta
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TodaysPredictions:
    """Get today's games and make predictions"""
    
    def __init__(self):
        self.models = joblib.load('models/ensemble/pregame_models.pkl')
        self.scaler = joblib.load('models/ensemble/pregame_scaler.pkl')
        self.predictions_dir = Path("predictions")
        self.predictions_dir.mkdir(exist_ok=True)
        
    def get_todays_games(self):
        """Fetch today's NBA games"""
        logger.info("🏀 Fetching today's NBA games...")
        
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            games = data.get('scoreboard', {}).get('games', [])
            
            todays_games = []
            for game in games:
                game_info = {
                    'game_id': game['gameId'],
                    'home_team': game['homeTeam']['teamName'],
                    'home_team_id': game['homeTeam']['teamId'],
                    'away_team': game['awayTeam']['teamName'],
                    'away_team_id': game['awayTeam']['teamId'],
                    'game_time': game.get('gameTimeUTC', ''),
                    'status': game.get('gameStatus', 1)
                }
                todays_games.append(game_info)
            
            logger.info(f"✅ Found {len(todays_games)} games today")
            return todays_games
            
        except Exception as e:
            logger.error(f"Failed to fetch today's games: {e}")
            return []
    
    def prepare_features(self, game):
        """Prepare prediction features for a game"""
        # Use latest advanced stats (would be fetched from agents in production)
        from src.agents.advanced_stats_agent import advanced_stats_agent
        
        try:
            stats_df = advanced_stats_agent.get_team_advanced_stats('2024-25')
            
            features = pd.DataFrame({
                'league_avg_off_rating': [stats_df['OFF_RATING'].mean()],
                'league_avg_def_rating': [stats_df['DEF_RATING'].mean()],
                'league_avg_net_rating': [stats_df['NET_RATING'].mean()],
                'league_avg_pace': [stats_df['PACE'].mean()],
                'league_avg_ts_pct': [stats_df['TS_PCT'].mean()],
                'home_court_advantage': [1.0],
                'expected_home_win_rate': [0.58],
                'game_sequence': [250],  # Approximate
                'game_pct_through_season': [0.5]
            })
            
            return features
            
        except Exception as e:
            logger.warning(f"Using default features: {e}")
            # Default features if stats fetch fails
            return pd.DataFrame({
                'league_avg_off_rating': [113.5],
                'league_avg_def_rating': [113.5],
                'league_avg_net_rating': [0.0],
                'league_avg_pace': [99.5],
                'league_avg_ts_pct': [0.578],
                'home_court_advantage': [1.0],
                'expected_home_win_rate': [0.58],
                'game_sequence': [250],
                'game_pct_through_season': [0.5]
            })
    
    def predict_game(self, game):
        """Make prediction for a single game"""
        features = self.prepare_features(game)
        X = self.scaler.transform(features)
        
        # Get predictions from all models
        rf_prob = self.models['rf'].predict_proba(X)[0][1]
        gb_prob = self.models['gb'].predict_proba(X)[0][1]
        lr_prob = self.models['lr'].predict_proba(X)[0][1]
        ensemble_prob = self.models['ensemble'].predict_proba(X)[0][1]
        
        prediction = {
            'game_id': game['game_id'],
            'home_team': game['home_team'],
            'away_team': game['away_team'],
            'home_team_id': game['home_team_id'],
            'away_team_id': game['away_team_id'],
            'home_win_prob': float(ensemble_prob),
            'away_win_prob': float(1 - ensemble_prob),
            'predicted_winner': game['home_team'] if ensemble_prob > 0.5 else game['away_team'],
            'confidence': float(max(ensemble_prob, 1 - ensemble_prob)),
            'model_predictions': {
                'random_forest': float(rf_prob),
                'gradient_boosting': float(gb_prob),
                'logistic_regression': float(lr_prob),
                'ensemble': float(ensemble_prob)
            },
            'prediction_time': datetime.now().isoformat(),
            'game_time': game['game_time']
        }
        
        return prediction
    
    def predict_all_games(self):
        """Make predictions for all today's games"""
        games = self.get_todays_games()
        
        if not games:
            logger.warning("⚠️  No games today")
            return []
        
        logger.info(f"\n{'='*80}")
        logger.info("🎯 MAKING PREDICTIONS FOR TODAY'S GAMES")
        logger.info(f"{'='*80}\n")
        
        predictions = []
        for i, game in enumerate(games, 1):
            logger.info(f"Game {i}/{len(games)}: {game['away_team']} @ {game['home_team']}")
            
            pred = self.predict_game(game)
            predictions.append(pred)
            
            logger.info(f"  ✅ Prediction: {pred['predicted_winner']} wins ({pred['confidence']:.1%} confidence)")
            logger.info(f"     Home: {pred['home_win_prob']:.1%} | Away: {pred['away_win_prob']:.1%}\n")
        
        # Save predictions
        today = datetime.now().strftime('%Y-%m-%d')
        output_file = self.predictions_dir / f"predictions_{today}.json"
        
        with open(output_file, 'w') as f:
            json.dump(predictions, f, indent=2)
        
        logger.info(f"💾 Saved predictions to: {output_file}")
        
        return predictions

def main():
    print("=" * 80)
    print("🏀 NBA PREDICTIONS FOR TODAY")
    print("=" * 80)
    
    predictor = TodaysPredictions()
    predictions = predictor.predict_all_games()
    
    if predictions:
        print("\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print(f"Total Games: {len(predictions)}")
        print(f"Predictions saved: predictions/predictions_{datetime.now().strftime('%Y-%m-%d')}.json")
        print("\nTo validate predictions tomorrow, run:")
        print("  python scripts/validate_predictions.py")
    else:
        print("\n⚠️  No games to predict today")

if __name__ == "__main__":
    main()
