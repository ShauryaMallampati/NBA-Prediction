"""
Generate predictions for today's NBA games using ensemble model
Integrates scraped schedule with trained prediction models + injury data
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.common.paths import Paths
from src.models.pregame.predictor import EnsemblePredictor

# Import injury feature engineer
sys.path.insert(0, str(project_root / "scripts"))
from enhance_features_with_injuries import InjuryFeatureEngineer


def load_todays_games() -> pd.DataFrame:
    """Load today's games needing predictions"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    predictions_file = Paths.DATA / "schedules" / f"predictions_needed_{today_str}.csv"
    
    if not predictions_file.exists():
        print(f"❌ No predictions file found at {predictions_file}")
        print("   Run scripts/update_schedule_database.py first!")
        return pd.DataFrame()
    
    games_df = pd.read_csv(predictions_file)
    print(f"✅ Loaded {len(games_df)} games needing predictions")
    return games_df


def prepare_features_for_games(games_df: pd.DataFrame, include_injuries: bool = True) -> pd.DataFrame:
    """
    Prepare features for prediction
    
    This is a simplified version - in production, you'd fetch:
    - Team ELO ratings
    - Recent form (last 5/10 games)
    - Head-to-head history
    - Rest days
    - Home/away records
    - INJURY DATA (NOW INCLUDED!)
    - Etc.
    
    For now, we'll use placeholder values as demonstration
    """
    print("\n🔧 Preparing features for prediction...")
    
    # Load historical features to get feature names
    pregame_features_file = Paths.ARTIFACTS / "features" / "pregame.parquet"
    
    if not pregame_features_file.exists():
        print(f"❌ No feature file found at {pregame_features_file}")
        return pd.DataFrame()
    
    historical_df = pd.read_parquet(pregame_features_file)
    feature_columns = [col for col in historical_df.columns if col not in [
        'game_id', 'date', 'home_team', 'away_team', 'season', 'year', 'month', 'day_of_week',
        'home_score', 'away_score', 'home_win', 'away_win', 'score_diff'
    ]]
    
    # Add injury feature columns to expected features
    injury_feature_cols = [
        'home_injured_stars', 'home_total_injured', 'home_injury_impact',
        'away_injured_stars', 'away_total_injured', 'away_injury_impact',
        'injury_advantage'
    ]
    
    print(f"   Using {len(feature_columns)} features from historical data")
    if include_injuries:
        print(f"   + {len(injury_feature_cols)} injury impact features")
    
    # Initialize injury engineer
    injury_engineer = InjuryFeatureEngineer() if include_injuries else None
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # For each game, we need to fetch/compute these features
    # For demonstration, we'll use recent averages from historical data
    prediction_features = []
    
    for idx, game in games_df.iterrows():
        home_team = game['home_team']
        away_team = game['away_team']
        
        # Get recent historical data for these teams
        home_recent = historical_df[historical_df['home_team'] == home_team].tail(10)
        away_recent = historical_df[historical_df['away_team'] == away_team].tail(10)
        
        if home_recent.empty or away_recent.empty:
            print(f"   ⚠️  Skipping {away_team} @ {home_team} - insufficient historical data")
            continue
        
        # Create feature row using recent averages
        feature_row = {
            'game_id': game['game_id'],
            'date': game['date'],
            'home_team': home_team,
            'away_team': away_team
        }
        
        # Use mean of recent games for each feature
        for col in feature_columns:
            if col in home_recent.columns:
                home_val = home_recent[col].mean()
                feature_row[col] = home_val
            else:
                # Default value if feature not found
                feature_row[col] = 0
        
        # Add injury features
        if include_injuries and injury_engineer:
            injuries_df = injury_engineer.load_injury_data(today_str)
            home_impact = injury_engineer.calculate_injury_impact(home_team, injuries_df)
            away_impact = injury_engineer.calculate_injury_impact(away_team, injuries_df)
            
            feature_row['home_injured_stars'] = home_impact['injured_star_count']
            feature_row['home_total_injured'] = home_impact['total_injured']
            feature_row['home_injury_impact'] = home_impact['injury_impact_score']
            feature_row['away_injured_stars'] = away_impact['injured_star_count']
            feature_row['away_total_injured'] = away_impact['total_injured']
            feature_row['away_injury_impact'] = away_impact['injury_impact_score']
            feature_row['injury_advantage'] = home_impact['injury_impact_score'] - away_impact['injury_impact_score']
        
        prediction_features.append(feature_row)
        print(f"   ✓ Prepared features for {away_team} @ {home_team}")
    
    features_df = pd.DataFrame(prediction_features)
    print(f"\n✅ Prepared {len(features_df)} games with features")
    
    return features_df


def generate_predictions():
    """Main prediction generation function"""
    print("=" * 80)
    print("GENERATING PREDICTIONS FOR TODAY'S GAMES")
    print("=" * 80)
    
    # Load today's games
    games_df = load_todays_games()
    
    if games_df.empty:
        return
    
    # Prepare features
    features_df = prepare_features_for_games(games_df)
    
    if features_df.empty:
        print("\n❌ No features prepared - cannot generate predictions")
        return
    
    # Load ensemble model
    print("\n🤖 Loading ensemble prediction model...")
    try:
        model_dir = Paths.MODELS / "pregame"
        predictor = EnsemblePredictor(str(model_dir))
        print("✅ Model loaded successfully")
        
        # Get model info
        model_info = predictor.get_model_info()
        print(f"\nModel Performance:")
        if 'ensemble_accuracy' in model_info:
            print(f"  Ensemble Accuracy: {model_info['ensemble_accuracy']:.1%}")
        if 'ensemble_auc' in model_info:
            print(f"  Ensemble AUC: {model_info['ensemble_auc']:.3f}")
        print(f"  Loaded {model_info.get('n_features', 0)} features")
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Generate predictions
    print("\n🎯 Generating predictions...")
    predictions_list = []
    
    for idx, row in features_df.iterrows():
        game_id = row['game_id']
        home_team = row['home_team']
        away_team = row['away_team']
        
        # Extract feature values (exclude metadata columns)
        feature_cols = [col for col in features_df.columns if col not in [
            'game_id', 'date', 'home_team', 'away_team', 'season', 'year', 'month', 'day_of_week'
        ]]
        
        # Create DataFrame with just features (predictor expects DataFrame)
        features_for_pred = pd.DataFrame([row[feature_cols].values], columns=feature_cols)
        
        # Get prediction with feature importance
        try:
            pred_result = predictor.predict_with_features(
                features_for_pred,
                top_n=5
            )
            
            # Extract result (it's a list with one element)
            result = pred_result[0] if isinstance(pred_result, list) else pred_result
            
            home_win_prob = result['prediction']
            away_win_prob = 1 - home_win_prob
            top_features = {f['feature']: f['importance'] for f in result['top_features']}
            
            predictions_list.append({
                'game_id': game_id,
                'date': row['date'],
                'home_team': home_team,
                'away_team': away_team,
                'home_win_prob': home_win_prob,
                'away_win_prob': away_win_prob,
                'predicted_winner': home_team if home_win_prob > 0.5 else away_team,
                'confidence': max(home_win_prob, away_win_prob),
                'top_feature_1': list(top_features.keys())[0] if len(top_features) > 0 else None,
                'top_feature_2': list(top_features.keys())[1] if len(top_features) > 1 else None,
                'top_feature_3': list(top_features.keys())[2] if len(top_features) > 2 else None,
                'generated_at': datetime.now().isoformat()
            })
            
            print(f"   ✓ {away_team} @ {home_team}: {home_team} {home_win_prob:.1%} - {away_team} {away_win_prob:.1%}")
            
        except Exception as e:
            print(f"   ❌ Error predicting {away_team} @ {home_team}: {e}")
    
    # Save predictions
    if predictions_list:
        predictions_df = pd.DataFrame(predictions_list)
        
        # Save to artifacts
        predictions_dir = Paths.ARTIFACTS / "predictions"
        predictions_dir.mkdir(parents=True, exist_ok=True)
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        output_file = predictions_dir / f"predictions_{today_str}.csv"
        
        predictions_df.to_csv(output_file, index=False)
        
        print(f"\n✅ Saved {len(predictions_df)} predictions to {output_file}")
        
        # Display predictions
        print("\n" + "=" * 80)
        print(f"TODAY'S PREDICTIONS ({today_str})")
        print("=" * 80)
        
        for _, pred in predictions_df.iterrows():
            home_team = pred['home_team']
            away_team = pred['away_team']
            home_prob = pred['home_win_prob']
            away_prob = pred['away_win_prob']
            winner = pred['predicted_winner']
            confidence = pred['confidence']
            
            print(f"\n{away_team} @ {home_team}")
            print(f"  Prediction: {winner} wins ({confidence:.1%} confidence)")
            print(f"  Probabilities: {home_team} {home_prob:.1%} - {away_team} {away_prob:.1%}")
            
            if pred['top_feature_1']:
                print(f"  Key factors: {pred['top_feature_1']}, {pred['top_feature_2']}, {pred['top_feature_3']}")
        
        print("\n" + "=" * 80)
        print("✅ PREDICTIONS GENERATED SUCCESSFULLY!")
        print("=" * 80)
        
    else:
        print("\n❌ No predictions generated")


def main():
    """Run prediction generation"""
    generate_predictions()


if __name__ == "__main__":
    main()
