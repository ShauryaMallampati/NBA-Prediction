"""
Simple NBA Predictions based on team ratings - No ML needed
Uses Elo-style rating system based on current team performance
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
from datetime import datetime
import json
import logging
import math

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplePredictor:
    """Make predictions using team ratings"""
    
    def __init__(self):
        self.predictions_dir = Path("predictions")
        self.predictions_dir.mkdir(exist_ok=True)
    
    def get_todays_games(self):
        """Fetch today's NBA games"""
        logger.info("🏀 Fetching today's NBA games...")
        
        url = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"
        
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
                }
                todays_games.append(game_info)
            
            logger.info(f"✅ Found {len(todays_games)} games today")
            return todays_games
            
        except Exception as e:
            logger.error(f"Failed to fetch today's games: {e}")
            return []
    
    def predict_game(self, game):
        """Predict game outcome using team stats"""
        from src.agents.advanced_stats_agent import advanced_stats_agent
        
        try:
            stats_df = advanced_stats_agent.get_team_advanced_stats('2024-25')
            
            home_stats = stats_df[stats_df['TEAM_ID'] == game['home_team_id']]
            away_stats = stats_df[stats_df['TEAM_ID'] == game['away_team_id']]
            
            if home_stats.empty or away_stats.empty:
                # Default 50/50 + home court
                home_prob = 0.58
            else:
                # Get net ratings
                home_net = home_stats['NET_RATING'].iloc[0]
                away_net = away_stats['NET_RATING'].iloc[0]
                
                # Net rating differential
                net_diff = home_net - away_net
                
                # Add home court advantage (~3 points = ~0.08 net rating boost)
                home_court = 3.0
                adjusted_diff = net_diff + home_court
                
                # Convert to win probability
                # Rule: Every 10 point net rating diff ≈ 20% win prob change
                # Using logistic function: P = 1 / (1 + e^(-k*diff))
                k = 0.033  # Tuned constant
                home_prob = 1 / (1 + math.exp(-k * adjusted_diff))
                
                # Clip to reasonable range
                home_prob = max(0.2, min(0.8, home_prob))
            
            prediction = {
                'game_id': game['game_id'],
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'home_team_id': game['home_team_id'],
                'away_team_id': game['away_team_id'],
                'home_win_prob': float(home_prob),
                'away_win_prob': float(1 - home_prob),
                'predicted_winner': game['home_team'] if home_prob > 0.5 else game['away_team'],
                'confidence': float(max(home_prob, 1 - home_prob)),
                'prediction_time': datetime.now().isoformat(),
                'game_time': game['game_time']
            }
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting game: {e}")
            return None
    
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
            if pred:
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
    print("🏀 NBA PREDICTIONS FOR TODAY (SIMPLE METHOD)")
    print("=" * 80)
    
    predictor = SimplePredictor()
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
