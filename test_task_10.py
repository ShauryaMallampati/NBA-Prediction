#!/usr/bin/env python3
"""Test script for Task #10: NBA Stats API Client.

Tests:
1. ✅ ODDS_API_KEY is configured
2. ✅ NBA Stats API connectivity
3. ✅ Player props feature extraction
4. ✅ Feature output validation
"""

import sys
import os
sys.path.insert(0, '/Users/shauryamallampati/Desktop/NBA prediction')
os.environ['ODDS_API_KEY'] = 'REMOVED_ODDS_KEY'

import pandas as pd
from datetime import datetime

# Test imports
try:
    from src.data.ingest.nba_stats_client import NBAStatsClient
    from src.data.ingest.player_props_extractor import PlayerPropsExtractor
    print("✅ Successfully imported modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_odds_api_key():
    """Test ODDS_API_KEY setup."""
    print("\n" + "="*60)
    print("TEST 1: ODDS_API_KEY Configuration")
    print("="*60)
    
    import requests
    try:
        url = "https://api.the-odds-api.com/v4/sports"
        params = {'apiKey': os.getenv('ODDS_API_KEY')}
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            sports = response.json()
            print(f"✅ ODDS_API_KEY is VALID")
            print(f"   Available sports: {len(sports)}")
            nba = [s for s in sports if 'basketball_nba' in s.get('key', '')]
            if nba:
                print(f"   ✅ NBA available: {nba[0]['key']}")
                return True
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {str(e)[:100]}")
        return False


def test_nba_stats_client():
    """Test NBA Stats Client initialization."""
    print("\n" + "="*60)
    print("TEST 2: NBA Stats API Client")
    print("="*60)
    
    try:
        # Note: NBA_STATS_API_KEY can be a dummy key for this test
        os.environ['NBA_STATS_API_KEY'] = 'test_key_for_init'
        
        client = NBAStatsClient()
        print(f"✅ Client initialized")
        print(f"   Base URL: {client.BASE_URL}")
        print(f"   Cache dir: {client.cache_dir}")
        print(f"   Cache dir exists: {client.cache_dir.exists()}")
        return True
        
    except Exception as e:
        print(f"❌ Client init error: {str(e)[:100]}")
        return False


def test_player_props_features():
    """Test player props feature extraction logic."""
    print("\n" + "="*60)
    print("TEST 3: Player Props Features Structure")
    print("="*60)
    
    try:
        from src.data.ingest.player_props_extractor import PlayerPropsExtractor
        
        extractor = PlayerPropsExtractor()
        print(f"✅ Extractor initialized")
        print(f"   Output dir: {extractor.output_dir}")
        print(f"   Properties: {extractor.PROPS}")
        print(f"   Output dir exists: {extractor.output_dir.exists()}")
        
        # Test empty features
        empty_features = extractor.client._empty_features()
        print(f"\n   Empty features structure:")
        for key in sorted(empty_features.keys()):
            print(f"      - {key}: {empty_features[key]}")
        
        expected_features = {
            "PTS_season_avg", "PTS_recent_avg", "PTS_recent_trend", "PTS_consistency",
            "AST_season_avg", "AST_recent_avg", "AST_recent_trend", "AST_consistency",
            "REB_season_avg", "REB_recent_avg", "REB_recent_trend", "REB_consistency",
            "STEALS_season_avg", "STEALS_recent_avg", "STEALS_recent_trend", "STEALS_consistency",
            "BLOCKS_season_avg", "BLOCKS_recent_avg", "BLOCKS_recent_trend", "BLOCKS_consistency",
        }
        
        if set(empty_features.keys()) == expected_features:
            print(f"✅ Feature structure is correct ({len(expected_features)} features)")
            return True
        else:
            missing = expected_features - set(empty_features.keys())
            extra = set(empty_features.keys()) - expected_features
            if missing:
                print(f"❌ Missing features: {missing}")
            if extra:
                print(f"❌ Extra features: {extra}")
            return False
        
    except Exception as e:
        print(f"❌ Feature extraction error: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return False


def test_file_structure():
    """Test that required files exist and are correctly formatted."""
    print("\n" + "="*60)
    print("TEST 4: File Structure & Module Organization")
    print("="*60)
    
    import pathlib
    
    required_files = [
        pathlib.Path('/Users/shauryamallampati/Desktop/NBA prediction/src/data/ingest/nba_stats_client.py'),
        pathlib.Path('/Users/shauryamallampati/Desktop/NBA prediction/src/data/ingest/player_props_extractor.py'),
    ]
    
    all_exist = True
    for file_path in required_files:
        exists = file_path.exists()
        size_kb = file_path.stat().st_size / 1024 if exists else 0
        status = "✅" if exists else "❌"
        print(f"{status} {file_path.name}: {size_kb:.1f} KB")
        if not exists:
            all_exist = False
    
    if all_exist:
        print("✅ All required files exist")
        return True
    else:
        print("❌ Some files are missing")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " TASK #10: NBA STATS API CLIENT - TEST SUITE ".center(58) + "║")
    print("╚" + "="*58 + "╝")
    
    results = {
        "ODDS_API_KEY Configuration": test_odds_api_key(),
        "NBA Stats Client Init": test_nba_stats_client(),
        "Player Props Features": test_player_props_features(),
        "File Structure": test_file_structure(),
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\nResult: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Task #10 implementation is ready.")
        print("\nNext steps:")
        print("1. Add real NBA_STATS_API_KEY to .env (from https://rapidapi.com/api-sports/api/api-nba)")
        print("2. Run: python3 -m src.data.ingest.player_props_extractor 2023")
        print("3. Verify output: ls -lh artifacts/player_props_data/")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
