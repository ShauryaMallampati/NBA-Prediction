"""
Test Suite for Player Props Features Pipeline (Task #13)

Tests:
  1. Feature Count Validation - Verify 40+ features present
  2. Feature Types Check - Ensure correct dtypes
  3. Feature Ranges - Values within expected bounds (0-1 normalized)
  4. Missing Value Handling - Graceful fallback to 0.0
  5. Data Integration - Stats + BR + Travel combine correctly
  6. Parquet Export - File creation and schema
  7. Feature Statistics - Min, max, mean for each feature
  8. Real-World Scenario - LeBron game with all data sources
  9. Partial Data - Handle missing BR or travel data
  10. Batch Processing - Multiple player-games

Run: python3 test_task_13.py
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.preprocess.player_props_pipeline import PlayerPropsFeaturesPipeline, create_sample_feature_matrix


class TestPlayerPropsFeaturesPipeline:
    """Test suite for Player Props Features Pipeline."""
    
    def __init__(self):
        self.pipeline = PlayerPropsFeaturesPipeline()
        self.test_results = []
    
    def run_all_tests(self):
        """Run all tests and display results."""
        print("╔" + "="*68 + "╗")
        print("║" + " "*15 + "TASK #13: PLAYER PROPS FEATURES PIPELINE" + " "*13 + "║")
        print("╚" + "="*68 + "╝\n")
        
        test_methods = [
            self.test_feature_count,
            self.test_feature_types,
            self.test_feature_ranges,
            self.test_missing_value_handling,
            self.test_data_integration,
            self.test_parquet_export,
            self.test_feature_statistics,
            self.test_real_world_scenario,
            self.test_partial_data,
            self.test_batch_processing,
        ]
        
        for i, test_method in enumerate(test_methods, 1):
            test_name = test_method.__name__.replace("test_", "").replace("_", " ").title()
            result = test_method()
            status = "✅" if result else "❌"
            self.test_results.append((test_name, result))
            print(f"TEST {i}: {test_name} {status}\n")
        
        # Summary
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        print("="*70)
        print("TEST SUMMARY")
        print("="*70)
        for name, result in self.test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {name}")
        
        print(f"\n✅ PASS: {passed}/{total} tests passed")
        return passed == total
    
    def test_feature_count(self) -> bool:
        """TEST 1: Feature Count Validation."""
        print("  • Checking feature count...")
        
        # Create sample data
        stats_data = [{
            "date": "2023-11-15",
            "player_name": "LeBron James",
            "team": "Los Angeles Lakers",
            "opponent": "Boston Celtics",
            "pts_season_avg": 25.5, "pts_recent_avg": 26.2, "pts_recent_trend": 0.3, "pts_consistency": 2.1,
            "ast_season_avg": 9.2, "ast_recent_avg": 9.5, "ast_recent_trend": 0.1, "ast_consistency": 1.8,
            "reb_season_avg": 7.3, "reb_recent_avg": 7.5, "reb_recent_trend": 0.0, "reb_consistency": 1.5,
            "stl_season_avg": 1.2, "stl_recent_avg": 1.3, "stl_recent_trend": 0.05, "stl_consistency": 0.4,
            "blk_season_avg": 0.8, "blk_recent_avg": 0.9, "blk_recent_trend": 0.02, "blk_consistency": 0.3,
            "actual_pts": 24, "actual_ast": 9, "actual_reb": 8, "actual_stl": 1, "actual_blk": 1,
        }]
        
        br_data = [{"player_name": "LeBron James", "date": "2023-11-15",
                   "on_games": 8.0, "off_games": 1.0, "consistency": 1.0, "rest_risk": 0.11,
                   "recent_ppg": 23.3, "recent_trend": 3.0, "recent_consistency": 2.95, "is_resting": False}]
        
        travel_data = [{"team": "Los Angeles Lakers", "date": "2023-11-15",
                       "distance_miles": 0.0, "timezone_diff": 0, "fatigue_score": 5,
                       "back_to_back": False, "minutes_yesterday": 38.0, "rest_risk": 0.05}]
        
        df = self.pipeline.build_feature_matrix(stats_data, br_data, travel_data)
        
        # Verify feature count
        feature_count = len(df.columns)
        print(f"    - Feature count: {feature_count}")
        
        # Breakdown
        player_features = ["pts_season_avg", "ast_season_avg", "reb_season_avg", "stl_season_avg", "blk_season_avg"]
        load_features = ["load_on_games", "form_recent_ppg"]
        travel_features = ["travel_distance_miles", "travel_fatigue_score"]
        context_features = ["game_date", "player_name"]
        
        player_count = sum(1 for c in df.columns if any(pf in c for pf in ["pts_", "ast_", "reb_", "stl_", "blk_"]))
        load_count = sum(1 for c in df.columns if any(lf in c for lf in ["load_", "form_"]))
        travel_count = sum(1 for c in df.columns if any(tf in c for tf in ["travel_"]))
        context_count = sum(1 for c in df.columns if any(cf in c for cf in ["game_", "player_", "team", "opponent"]))
        
        print(f"      • Player Performance: {player_count} features")
        print(f"      • Load Management: {load_count} features")
        print(f"      • Travel & Fatigue: {travel_count} features")
        print(f"      • Context: {context_count} features")
        print(f"      • Targets: 5 features (actual_*)")
        
        success = feature_count >= 40
        print(f"    - Result: {'✅ PASS' if success else '❌ FAIL'} ({feature_count} >= 40)")
        return success
    
    def test_feature_types(self) -> bool:
        """TEST 2: Feature Types Check."""
        print("  • Checking feature data types...")
        
        df = create_sample_feature_matrix()
        
        type_issues = []
        for col in df.columns:
            if col in ["game_date", "player_name", "team", "opponent"]:
                if df[col].dtype != "object":
                    type_issues.append(f"    - {col} should be object, got {df[col].dtype}")
            else:
                if df[col].dtype not in ["float32", "float64", "int8", "int16", "int32", "int64"]:
                    type_issues.append(f"    - {col} should be numeric, got {df[col].dtype}")
        
        if type_issues:
            for issue in type_issues:
                print(issue)
            return False
        else:
            print(f"    - All {len(df.columns)} columns have correct types")
            return True
    
    def test_feature_ranges(self) -> bool:
        """TEST 3: Feature Ranges Check."""
        print("  • Checking feature value ranges...")
        
        df = create_sample_feature_matrix()
        
        # Check binary features (0 or 1)
        binary_features = ["travel_back_to_back", "travel_arena_change", "form_rest_pattern"]
        binary_ok = True
        for col in binary_features:
            if col in df.columns:
                unique_vals = df[col].unique()
                if not all(v in [0.0, 1.0] for v in unique_vals):
                    print(f"    - {col} has non-binary values: {unique_vals}")
                    binary_ok = False
        
        # Check normalized ratio features (0 to 1) - consistency values are normalized
        normalized_ratio_features = ["pts_consistency", "ast_consistency", "reb_consistency", 
                                     "stl_consistency", "blk_consistency", "form_recent_consistency",
                                     "load_consistency", "load_rest_risk", "travel_risk"]
        ratio_ok = True
        for col in normalized_ratio_features:
            if col in df.columns:
                min_val = df[col].min()
                max_val = df[col].max()
                if min_val < 0 or max_val > 1:
                    print(f"    - {col} out of range [0,1]: min={min_val}, max={max_val}")
                    ratio_ok = False
        
        # Check positive features (can be any positive number)
        positive_features = ["pts_season_avg", "travel_distance_miles", "travel_minutes_yesterday",
                            "load_on_games", "load_off_games", "form_recent_ppg"]
        positive_ok = True
        for col in positive_features:
            if col in df.columns:
                min_val = df[col].min()
                if min_val < 0:
                    print(f"    - {col} has negative values: min={min_val}")
                    positive_ok = False
        
        result = binary_ok and ratio_ok and positive_ok
        print(f"    - Binary features: {'✅' if binary_ok else '❌'}")
        print(f"    - Normalized ratio features: {'✅' if ratio_ok else '❌'}")
        print(f"    - Positive features: {'✅' if positive_ok else '❌'}")
        return result
    
    def test_missing_value_handling(self) -> bool:
        """TEST 4: Missing Value Handling."""
        print("  • Testing missing value fallback...")
        
        # Test with None BR data
        stats_data = [{
            "date": "2023-11-15",
            "player_name": "Test Player",
            "team": "Test Team",
            "opponent": "Opponent",
            "pts_season_avg": 20.0,
            "pts_recent_avg": 21.0,
            "pts_recent_trend": 0.5,
            "pts_consistency": 2.0,
            "ast_season_avg": 5.0,
            "ast_recent_avg": 5.5,
            "ast_recent_trend": 0.2,
            "ast_consistency": 1.0,
            "reb_season_avg": 5.0,
            "reb_recent_avg": 5.0,
            "reb_recent_trend": 0.0,
            "reb_consistency": 1.0,
            "stl_season_avg": 1.0,
            "stl_recent_avg": 1.0,
            "stl_recent_trend": 0.0,
            "stl_consistency": 0.5,
            "blk_season_avg": 1.0,
            "blk_recent_avg": 1.0,
            "blk_recent_trend": 0.0,
            "blk_consistency": 0.5,
        }]
        
        # No BR data
        df = self.pipeline.build_feature_matrix(stats_data, [], [])
        
        # Check that load management features default to 0.0
        load_cols = [c for c in df.columns if c.startswith("load_") or c.startswith("form_")]
        all_zero = all(df[col].iloc[0] == 0.0 for col in load_cols)
        
        print(f"    - Load management features defaulted to 0.0: {all_zero}")
        
        # Check that travel features default to 0.0
        travel_cols = [c for c in df.columns if c.startswith("travel_")]
        all_zero_travel = all(df[col].iloc[0] == 0.0 or df[col].iloc[0] == "" 
                             for col in travel_cols)
        
        print(f"    - Travel features defaulted to 0.0: {all_zero_travel}")
        
        return all_zero and all_zero_travel
    
    def test_data_integration(self) -> bool:
        """TEST 5: Data Integration Check."""
        print("  • Verifying integration of all three sources...")
        
        stats_data = [{
            "date": "2023-11-15",
            "player_name": "LeBron James",
            "team": "Lakers",
            "opponent": "Celtics",
            "pts_season_avg": 25.5, "pts_recent_avg": 26.0, "pts_recent_trend": 0.3, "pts_consistency": 2.1,
            "ast_season_avg": 9.0, "ast_recent_avg": 9.5, "ast_recent_trend": 0.1, "ast_consistency": 1.8,
            "reb_season_avg": 7.0, "reb_recent_avg": 7.5, "reb_recent_trend": 0.0, "reb_consistency": 1.5,
            "stl_season_avg": 1.2, "stl_recent_avg": 1.3, "stl_recent_trend": 0.05, "stl_consistency": 0.4,
            "blk_season_avg": 0.8, "blk_recent_avg": 0.9, "blk_recent_trend": 0.02, "blk_consistency": 0.3,
        }]
        
        br_data = [{
            "player_name": "LeBron James",
            "date": "2023-11-15",
            "on_games": 8.0, "off_games": 1.0, "consistency": 0.95, "rest_risk": 0.15,
            "recent_ppg": 25.3, "recent_trend": 3.0, "recent_consistency": 2.95, "is_resting": False,
        }]
        
        travel_data = [{
            "team": "Lakers",
            "date": "2023-11-15",
            "distance_miles": 2592.0, "timezone_diff": 3, "fatigue_score": 94,
            "back_to_back": True, "minutes_yesterday": 38.0,
        }]
        
        df = self.pipeline.build_feature_matrix(stats_data, br_data, travel_data)
        
        checks = []
        
        # Check that stats data is present
        checks.append(("Stats data (PTS)", df["pts_season_avg"].iloc[0] == 25.5))
        
        # Check that BR data is present
        checks.append(("BR data (load)", df["load_on_games"].iloc[0] == 8.0))
        checks.append(("BR data (form)", df["form_recent_ppg"].iloc[0] == 25.3))
        
        # Check that travel data is present
        checks.append(("Travel data (distance)", df["travel_distance_miles"].iloc[0] == 2592.0))
        checks.append(("Travel data (timezone)", df["travel_timezone_diff"].iloc[0] == 3))
        checks.append(("Travel data (B2B)", df["travel_back_to_back"].iloc[0] == 1.0))
        
        for check_name, result in checks:
            print(f"    - {check_name}: {'✅' if result else '❌'}")
        
        return all(result for _, result in checks)
    
    def test_parquet_export(self) -> bool:
        """TEST 6: Parquet Export Check."""
        print("  • Testing Parquet export...")
        
        df = create_sample_feature_matrix()
        output_path = self.pipeline.export_to_parquet(df, "test_features.parquet")
        
        # Verify file exists
        exists = output_path.exists()
        print(f"    - File created: {exists}")
        
        if exists:
            # Read back and verify
            df_read = pd.read_parquet(output_path)
            shapes_match = df_read.shape == df.shape
            print(f"    - Shape preserved: {shapes_match} {df_read.shape} == {df.shape}")
            
            # Cleanup
            if output_path.exists():
                output_path.unlink()
            
            return shapes_match
        
        return False
    
    def test_feature_statistics(self) -> bool:
        """TEST 7: Feature Statistics Check."""
        print("  • Computing feature statistics...")
        
        df = create_sample_feature_matrix()
        stats = self.pipeline.get_feature_stats(df)
        
        print(f"    - Total records: {stats['total_records']}")
        print(f"    - Total features: {stats['total_features']}")
        print(f"    - Unique players: {stats['unique_players']}")
        print(f"    - Unique teams: {stats['unique_teams']}")
        print(f"    - Date range: {stats['date_range']}")
        
        checks = [
            stats['total_records'] > 0,
            stats['total_features'] >= 40,
            stats['unique_players'] > 0,
            stats['unique_teams'] > 0,
        ]
        
        return all(checks)
    
    def test_real_world_scenario(self) -> bool:
        """TEST 8: Real-World Scenario."""
        print("  • Testing real-world scenario (LeBron Nov 15, 2023)...")
        
        # LeBron James, Lakers vs Celtics, 2023-11-15
        # Home game (no travel), off load management, 38 min yesterday
        
        stats_data = [{
            "date": "2023-11-15",
            "player_name": "LeBron James",
            "team": "Los Angeles Lakers",
            "opponent": "Boston Celtics",
            "pts_season_avg": 25.5, "pts_recent_avg": 26.2, "pts_recent_trend": 0.3, "pts_consistency": 2.1,
            "ast_season_avg": 9.2, "ast_recent_avg": 9.5, "ast_recent_trend": 0.1, "ast_consistency": 1.8,
            "reb_season_avg": 7.3, "reb_recent_avg": 7.5, "reb_recent_trend": 0.0, "reb_consistency": 1.5,
            "stl_season_avg": 1.2, "stl_recent_avg": 1.3, "stl_recent_trend": 0.05, "stl_consistency": 0.4,
            "blk_season_avg": 0.8, "blk_recent_avg": 0.9, "blk_recent_trend": 0.02, "blk_consistency": 0.3,
            "actual_pts": 24, "actual_ast": 9, "actual_reb": 8, "actual_stl": 1, "actual_blk": 1,
        }]
        
        br_data = [{
            "player_name": "LeBron James",
            "date": "2023-11-15",
            "on_games": 8.0, "off_games": 1.0, "consistency": 1.0, "rest_risk": 0.11,
            "recent_ppg": 23.3, "recent_trend": 3.0, "recent_consistency": 2.95, "is_resting": False,
        }]
        
        travel_data = [{
            "team": "Los Angeles Lakers",
            "date": "2023-11-15",
            "distance_miles": 0.0,  # Home game
            "timezone_diff": 0,
            "fatigue_score": 5,  # Low due to home game
            "back_to_back": False,
            "minutes_yesterday": 38.0,
            "rest_risk": 0.05,
        }]
        
        df = self.pipeline.build_feature_matrix(stats_data, br_data, travel_data)
        
        row = df.iloc[0]
        
        checks = [
            ("Player name", row["player_name"] == "LeBron James"),
            ("Date", row["game_date"] == "2023-11-15"),
            ("Team", row["team"] == "Los Angeles Lakers"),
            ("PTS features present", row["pts_season_avg"] == 25.5),
            ("Load management present", row["load_on_games"] == 8.0),
            ("Travel distance (home)", row["travel_distance_miles"] == 0.0),
            ("Fatigue score (home)", row["travel_fatigue_score"] == 5),
            ("Actual target stats", row["actual_pts"] == 24),
        ]
        
        for check_name, result in checks:
            print(f"    - {check_name}: {'✅' if result else '❌'}")
        
        return all(result for _, result in checks)
    
    def test_partial_data(self) -> bool:
        """TEST 9: Partial Data Handling."""
        print("  • Testing partial data handling...")
        
        stats_data = [{
            "date": "2023-11-15",
            "player_name": "Test Player",
            "team": "Test Team",
            "opponent": "Opponent",
            "pts_season_avg": 20.0, "pts_recent_avg": 21.0, "pts_recent_trend": 0.5, "pts_consistency": 2.0,
            "ast_season_avg": 5.0, "ast_recent_avg": 5.5, "ast_recent_trend": 0.2, "ast_consistency": 1.0,
            "reb_season_avg": 5.0, "reb_recent_avg": 5.0, "reb_recent_trend": 0.0, "reb_consistency": 1.0,
            "stl_season_avg": 1.0, "stl_recent_avg": 1.0, "stl_recent_trend": 0.0, "stl_consistency": 0.5,
            "blk_season_avg": 1.0, "blk_recent_avg": 1.0, "blk_recent_trend": 0.0, "blk_consistency": 0.5,
        }]
        
        # Test 1: No BR data
        df1 = self.pipeline.build_feature_matrix(stats_data, [], [])
        has_load_fallback = df1["load_on_games"].iloc[0] == 0.0
        print(f"    - No BR data fallback: {'✅' if has_load_fallback else '❌'}")
        
        # Test 2: No travel data
        df2 = self.pipeline.build_feature_matrix(stats_data, [], [])
        has_travel_fallback = df2["travel_distance_miles"].iloc[0] == 0.0
        print(f"    - No travel data fallback: {'✅' if has_travel_fallback else '❌'}")
        
        # Test 3: Partial BR data (mismatch date)
        br_data = [{
            "player_name": "Test Player",
            "date": "2023-11-16",  # Different date
            "on_games": 5.0,
        }]
        df3 = self.pipeline.build_feature_matrix(stats_data, br_data, [])
        partial_match = df3["load_on_games"].iloc[0] == 0.0  # Should still fall back
        print(f"    - Partial match fallback: {'✅' if partial_match else '❌'}")
        
        return has_load_fallback and has_travel_fallback and partial_match
    
    def test_batch_processing(self) -> bool:
        """TEST 10: Batch Processing."""
        print("  • Testing batch processing of multiple games...")
        
        # Create multi-player dataset
        stats_data = []
        players = ["LeBron James", "Kyrie Irving", "Jayson Tatum"]
        dates = ["2023-11-15", "2023-11-16", "2023-11-17"]
        
        for i, (player, date) in enumerate(zip(players, dates)):
            stats_data.append({
                "date": date,
                "player_name": player,
                "team": ["Lakers", "Celtics", "Celtics"][i],
                "opponent": ["Celtics", "Warriors", "Lakers"][i],
                "pts_season_avg": 20.0 + i,
                "pts_recent_avg": 21.0 + i,
                "pts_recent_trend": 0.5,
                "pts_consistency": 2.0,
                "ast_season_avg": 5.0 + i*0.5,
                "ast_recent_avg": 5.5 + i*0.5,
                "ast_recent_trend": 0.2,
                "ast_consistency": 1.0,
                "reb_season_avg": 5.0,
                "reb_recent_avg": 5.0,
                "reb_recent_trend": 0.0,
                "reb_consistency": 1.0,
                "stl_season_avg": 1.0,
                "stl_recent_avg": 1.0,
                "stl_recent_trend": 0.0,
                "stl_consistency": 0.5,
                "blk_season_avg": 1.0,
                "blk_recent_avg": 1.0,
                "blk_recent_trend": 0.0,
                "blk_consistency": 0.5,
            })
        
        df = self.pipeline.build_feature_matrix(stats_data, [], [])
        
        correct_rows = len(df) == 3
        correct_players = set(df["player_name"].unique()) == set(players)
        correct_dates = set(df["game_date"].unique()) == set(dates)
        
        print(f"    - Rows: {len(df)} (expected 3): {'✅' if correct_rows else '❌'}")
        print(f"    - Players: {sorted(df['player_name'].unique())}: {'✅' if correct_players else '❌'}")
        print(f"    - Dates: {sorted(df['game_date'].unique())}: {'✅' if correct_dates else '❌'}")
        
        return correct_rows and correct_players and correct_dates


if __name__ == "__main__":
    tester = TestPlayerPropsFeaturesPipeline()
    success = tester.run_all_tests()
    
    exit_code = 0 if success else 1
    sys.exit(exit_code)
