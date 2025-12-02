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
        """Prepare prediction features for a game using team-specific stats"""
        from src.agents.advanced_stats_agent import advanced_stats_agent
        
        try:
            # Get team stats
            stats_df = advanced_stats_agent.get_team_advanced_stats('2024-25')
            
            # Find home and away team stats
            home_stats = stats_df[stats_df['TEAM_ID'] == game['home_team_id']]
            away_stats = stats_df[stats_df['TEAM_ID'] == game['away_team_id']]
            
            # League averages
            league_avg_off = stats_df['OFF_RATING'].mean()
            league_avg_def = stats_df['DEF_RATING'].mean()
            league_avg_net = stats_df['NET_RATING'].mean()
            league_avg_pace = stats_df['PACE'].mean()
            league_avg_ts = stats_df['TS_PCT'].mean()
            
            # Calculate matchup features
            if not home_stats.empty and not away_stats.empty:
                # Get actual team ratings
                home_off = home_stats['OFF_RATING'].iloc[0]
                home_def = home_stats['DEF_RATING'].iloc[0]
                home_net = home_stats['NET_RATING'].iloc[0]
                home_pace = home_stats['PACE'].iloc[0]
                home_ts = home_stats['TS_PCT'].iloc[0]
                
                away_off = away_stats['OFF_RATING'].iloc[0]
                away_def = away_stats['DEF_RATING'].iloc[0]
                away_net = away_stats['NET_RATING'].iloc[0]
                away_pace = away_stats['PACE'].iloc[0]
                away_ts = away_stats['TS_PCT'].iloc[0]
                
                # Create features that match training distribution
                # Training expects ratings near league average with small variance
                # So we adjust slightly based on team strength
                off_adjustment = (home_off - away_def) * 0.15  # Small adjustment
                def_adjustment = (away_off - home_def) * 0.15
                net_adjustment = (home_net - away_net) * 0.08  # Net rating differential scaled down
                pace_adjustment = ((home_pace + away_pace) / 2 - league_avg_pace) * 0.3
                ts_adjustment = ((home_ts + away_ts) / 2 - league_avg_ts) * 0.3
                
                # Features close to league averages with small team-specific adjustments
                matchup_off = league_avg_off + off_adjustment
                matchup_def = league_avg_def + def_adjustment
                matchup_net = net_adjustment  # This becomes the key differentiator
                matchup_pace = league_avg_pace + pace_adjustment
                matchup_ts = league_avg_ts + ts_adjustment
                
                # Expected home win rate based on net rating differential
                expected_win_rate = 0.58 + (home_net - away_net) * 0.015
                expected_win_rate = max(0.3, min(0.75, expected_win_rate))
                
            else:
                # Fallback if team not found
                matchup_off = league_avg_off
                matchup_def = league_avg_def
                matchup_net = 0.0
                matchup_pace = league_avg_pace
                matchup_ts = league_avg_ts
                expected_win_rate = 0.58
            
            features = pd.DataFrame({
                'league_avg_off_rating': [matchup_off],
                'league_avg_def_rating': [matchup_def],
                'league_avg_net_rating': [matchup_net],
                'league_avg_pace': [matchup_pace],
                'league_avg_ts_pct': [matchup_ts],
                'home_court_advantage': [1.0],
                'expected_home_win_rate': [expected_win_rate],
                'game_sequence': [250],
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
