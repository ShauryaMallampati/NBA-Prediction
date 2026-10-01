"""Quick check that our models actually work.

Loads the saved models and runs a few test predictions to make sure
nothing is broken before we deploy.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
import sys
import pickle

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def validate_models():
    """Make sure models load correctly and can make predictions."""
    
    print("\n" + "="*80)
    print("TASK #15: MODEL VALIDATION")
    print("="*80)
    
    # Load saved models
    print("\n📊 Loading trained models...")
    model_dir = Path('artifacts/models/pregame')
    
    models = {}
    calibrators = {}
    stats = ['PTS', 'AST', 'REB', 'STL', 'BLK']
    
    for stat in stats:
        model_path = model_dir / f'{stat.lower()}_model.pkl'
        calib_path = model_dir / f'{stat.lower()}_calibrator.pkl'
        
        if model_path.exists():
            with open(model_path, 'rb') as f:
                models[stat] = pickle.load(f)
            print(f"  ✅ {stat} model: {model_path.stat().st_size} bytes")
        
        if calib_path.exists():
            with open(calib_path, 'rb') as f:
                calibrators[stat] = pickle.load(f)
            print(f"  ✅ {stat} calibrator: {calib_path.stat().st_size} bytes")
    
    if len(models) != 5:
        print(f"\n❌ Expected 5 models, found {len(models)}")
        return False
    
    print(f"\n✅ Loaded {len(models)} models with calibrators")
    
    # Test predictions
    print("\n🎯 Testing predictions on sample data...")
    
    # Create realistic test data  
    test_features = pd.DataFrame({
        'FG_pct': [0.45],
        'FG3_pct': [0.35],
        'FT_pct': [0.80],
        'usage_pct': [0.25],
        'is_home': [1.0],
        'rest_days': [2.0],
        'is_back_to_back': [0.0],
        'games_played': [10.0],
        'consistency_score': [0.7],
        'PTS_actual_rolling_3': [22.0],
        'PTS_actual_rolling_7': [21.0],
        'PTS_actual_season_avg': [20.5],
        'PTS_actual_rolling_std_7': [2.0],
        'AST_actual_rolling_3': [5.0],
        'AST_actual_rolling_7': [4.8],
        'AST_actual_season_avg': [4.5],
        'AST_actual_rolling_std_7': [0.8],
        'REB_actual_rolling_3': [6.0],
        'REB_actual_rolling_7': [5.8],
        'REB_actual_season_avg': [5.5],
        'REB_actual_rolling_std_7': [0.6],
        'STL_actual_rolling_3': [1.2],
        'STL_actual_rolling_7': [1.0],
        'STL_actual_season_avg': [0.9],
        'STL_actual_rolling_std_7': [0.2],
        'BLK_actual_rolling_3': [0.8],
        'BLK_actual_rolling_7': [0.7],
        'BLK_actual_season_avg': [0.6],
        'BLK_actual_rolling_std_7': [0.15],
        'PTS_vs_opp_advantage': [1.5],
        'AST_vs_opp_advantage': [0.5],
        'REB_vs_opp_advantage': [0.8],
        'STL_vs_opp_advantage': [0.1],
        'BLK_vs_opp_advantage': [0.05],
        'PTS_actual_trend': [0.5],
        'AST_actual_trend': [0.2],
        'REB_actual_trend': [0.3],
        'opp_def_PTS': [22.5],
        'opp_def_AST': [5.2],
        'opp_def_REB': [6.2],
        'opp_def_STL': [1.1],
        'opp_def_BLK': [0.75],
    })
    
    test_array = test_features.values.astype(np.float32)
    
    predictions = {}
    errors = []
    
    for stat in stats:
        try:
            model = models[stat]
            calib = calibrators[stat]
            
            # Get prediction from model
            pred_raw = model.predict(test_array, num_iteration=model.best_iteration)[0]
            
            # Apply calibration
            pred_calib_input = np.array([[pred_raw]])
            pred_calib = calib.predict_proba(pred_calib_input)[0, 1]
            
            predictions[stat] = {
                'raw': pred_raw,
                'calibrated': pred_calib,
                'over': pred_calib > 0.5
            }
            
            direction = "OVER" if pred_calib > 0.5 else "UNDER"
            conf = abs(pred_calib - 0.5) * 200
            print(f"  {stat}: {direction:5s} @ {pred_calib:.1%} (confidence: {conf:.0f}%)")
            
        except Exception as e:
            errors.append(f"{stat}: {str(e)}")
            print(f"  {stat}: ❌ Error - {e}")
    
    if errors:
        print(f"\n⚠️  {len(errors)} prediction errors occurred")
        for err in errors:
            print(f"    • {err}")
    
    # Sanity checks
    print("\n✅ Sanity Checks:")
    print("-" * 80)
    
    checks = [
        ("All models made predictions", len(predictions) == 5),
        ("Predictions are calibrated (0-1)", all(0 <= p['calibrated'] <= 1 for p in predictions.values())),
        ("Models working correctly", len(errors) == 0),
    ]
    
    passed = 0
    for check_name, result in checks:
        status = "✅" if result else "⚠️ "
        print(f"  {status} {check_name}")
        if result:
            passed += 1
    
    print("\n" + "="*80)
    print(f"VALIDATION: {passed}/{len(checks)} checks passed")
    print("="*80)
    
    if passed == len(checks):
        print("✅ Models validated successfully!")
        print("\nReady for next tasks:")
        print("  • Task #16: Integrate rest risk predictor")
        print("  • Task #17: Add live feature extraction")
        print("  • Task #18: Deploy to production")
        return True
    else:
        print(f"⚠️  {len(checks) - passed} checks failed")
        return False


if __name__ == "__main__":
    success = validate_models()
    exit(0 if success else 1)
