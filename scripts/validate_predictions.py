"""
Validation Agent - Checks predictions against actual results
Runs at 1 AM to validate yesterday's predictions
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
import requests
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PredictionValidator:
    """Validates predictions against actual game results"""
    
    def __init__(self):
        self.predictions_dir = Path("predictions")
        self.results_dir = Path("predictions/results")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def get_game_result(self, game_id):
        """Fetch actual game result"""
        try:
            url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            game = data.get('game', {})
            home_score = int(game.get('homeTeam', {}).get('score', 0))
            away_score = int(game.get('awayTeam', {}).get('score', 0))
            
            return {
                'home_score': home_score,
                'away_score': away_score,
                'home_won': home_score > away_score,
                'game_status': game.get('gameStatus', 0)
            }
            
        except Exception as e:
            logger.warning(f"Failed to fetch result for game {game_id}: {e}")
            return None
    
    def validate_prediction(self, prediction, actual_result):
        """Check if prediction was correct"""
        if not actual_result:
            return None
        
        predicted_home_win = prediction['home_win_prob'] > 0.5
        actual_home_win = actual_result['home_won']
        
        correct = predicted_home_win == actual_home_win
        
        validation = {
            'game_id': prediction['game_id'],
            'home_team': prediction['home_team'],
            'away_team': prediction['away_team'],
            'predicted_winner': prediction['predicted_winner'],
            'actual_winner': prediction['home_team'] if actual_home_win else prediction['away_team'],
            'home_score': actual_result['home_score'],
            'away_score': actual_result['away_score'],
            'predicted_home_prob': prediction['home_win_prob'],
            'predicted_away_prob': prediction['away_win_prob'],
            'correct': correct,
            'confidence': prediction['confidence'],
            'prediction_time': prediction['prediction_time'],
            'validation_time': datetime.now().isoformat()
        }
        
        return validation
    
    def validate_date(self, date_str):
        """Validate all predictions for a specific date"""
        predictions_file = self.predictions_dir / f"predictions_{date_str}.json"
        
        if not predictions_file.exists():
            logger.warning(f"❌ No predictions found for {date_str}")
            return None
        
        logger.info(f"📂 Loading predictions from {predictions_file}")
        with open(predictions_file) as f:
            predictions = json.load(f)
        
        logger.info(f"🔍 Validating {len(predictions)} predictions...")
        
        validations = []
        for pred in predictions:
            logger.info(f"  Checking {pred['away_team']} @ {pred['home_team']}...")
            
            result = self.get_game_result(pred['game_id'])
            if result and result['game_status'] == 3:  # Game finished
                validation = self.validate_prediction(pred, result)
                if validation:
                    validations.append(validation)
                    status = "✅ CORRECT" if validation['correct'] else "❌ WRONG"
                    logger.info(f"    {status} - Predicted: {validation['predicted_winner']}, Actual: {validation['actual_winner']}")
            else:
                logger.info(f"    ⏳ Game not finished yet")
        
        if not validations:
            logger.warning("⚠️  No completed games to validate")
            return None
        
        # Calculate accuracy
        correct_count = sum(1 for v in validations if v['correct'])
        accuracy = correct_count / len(validations) if validations else 0
        
        summary = {
            'date': date_str,
            'total_predictions': len(predictions),
            'validated_games': len(validations),
            'correct_predictions': correct_count,
            'accuracy': accuracy,
            'validations': validations,
            'validation_time': datetime.now().isoformat()
        }
        
        # Save results
        results_file = self.results_dir / f"results_{date_str}.json"
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"\n💾 Saved validation results to: {results_file}")
        
        return summary
    
    def validate_yesterday(self):
        """Validate yesterday's predictions (run at 1 AM)"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        return self.validate_date(yesterday)
    
    def show_accuracy_report(self):
        """Show accuracy report across all validated dates"""
        logger.info(f"\n{'='*80}")
        logger.info("📊 OVERALL ACCURACY REPORT")
        logger.info(f"{'='*80}\n")
        
        results_files = sorted(self.results_dir.glob("results_*.json"))
        
        if not results_files:
            logger.info("No validation results found yet.")
            return
        
        total_validated = 0
        total_correct = 0
        
        for results_file in results_files:
            with open(results_file) as f:
                summary = json.load(f)
            
            total_validated += summary['validated_games']
            total_correct += summary['correct_predictions']
            
            logger.info(f"{summary['date']}: {summary['correct_predictions']}/{summary['validated_games']} ({summary['accuracy']:.1%})")
        
        overall_accuracy = total_correct / total_validated if total_validated > 0 else 0
        
        logger.info(f"\n{'='*80}")
        logger.info(f"OVERALL ACCURACY: {total_correct}/{total_validated} ({overall_accuracy:.1%})")
        logger.info(f"{'='*80}")

def main():
    print("=" * 80)
    print("🔍 PREDICTION VALIDATION AGENT")
    print("=" * 80)
    
    validator = PredictionValidator()
    
    # Validate yesterday's predictions
    summary = validator.validate_yesterday()
    
    if summary:
        print(f"\n{'='*80}")
        print("✅ VALIDATION COMPLETE")
        print(f"{'='*80}")
        print(f"Date: {summary['date']}")
        print(f"Games Validated: {summary['validated_games']}")
        print(f"Correct Predictions: {summary['correct_predictions']}")
        print(f"Accuracy: {summary['accuracy']:.1%}")
        print(f"{'='*80}")
    
    # Show overall accuracy report
    validator.show_accuracy_report()

if __name__ == "__main__":
    main()
