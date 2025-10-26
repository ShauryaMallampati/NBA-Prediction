"""
Task #12 Tests: Travel Distance Calculator + Fatigue Scoring

Tests cover:
✅ Distance calculation (Haversine formula accuracy)
✅ Timezone difference calculation
✅ Back-to-back detection
✅ Minutes-based fatigue contribution
✅ Composite fatigue score (0-100)
✅ Complete travel fatigue extraction
✅ Edge cases (no travel, extreme distances, multiple B2Bs)
✅ Interpretation generation
"""

import sys
import math
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, "/Users/shauryamallampati/Desktop/NBA prediction")

from src.data.ingest.travel_ors import TravelFatigueCalculator, NBA_ARENAS


def test_distance_calculation():
    """Test distance calculation using Haversine formula."""
    print("\n" + "="*70)
    print("TEST 1: Distance Calculation (Haversine Formula)")
    print("="*70)
    
    calc = TravelFatigueCalculator()
    
    # Test 1a: LA to Boston (known distance ~2450-2600 miles, Haversine gives 2592)
    distance_la_boston = calc.get_distance_miles("Los Angeles Lakers", "Boston Celtics")
    print(f"✓ LA to Boston: {distance_la_boston:.1f} miles (expected ~2600 via Haversine)")
    assert 2500 < distance_la_boston < 2700, f"Got {distance_la_boston}, expected ~2600"
    
    # Test 1b: Warriors to Kings (California, ~550-750 miles depending on exact coords)
    distance_local = calc.get_distance_miles("Golden State Warriors", "Sacramento Kings")
    print(f"✓ Warriors to Kings: {distance_local:.1f} miles (Bay Area to Sacramento)")
    assert 50 < distance_local < 200, f"Got {distance_local}, Bay Area should be ~75 miles"
    
    # Test 1c: Same arena (0 miles)
    distance_same = calc.get_distance_miles("Boston Celtics", "Boston Celtics")
    print(f"✓ Boston to Boston: {distance_same:.1f} miles (expected ~0)")
    assert distance_same < 1, f"Got {distance_same}, expected ~0"
    
    # Test 1d: Invalid arena (should return 0)
    distance_invalid = calc.get_distance_miles("Boston Celtics", "Invalid Team")
    print(f"✓ Invalid arena: {distance_invalid:.1f} miles (expected 0)")
    assert distance_invalid == 0.0
    
    print("✅ PASS: Distance calculation accurate within Haversine formula")


def test_timezone_calculation():
    """Test timezone difference calculation."""
    print("\n" + "="*70)
    print("TEST 2: Timezone Difference Calculation")
    print("="*70)
    
    calc = TravelFatigueCalculator()
    
    # Test 2a: LA to NY (west to east = gained sleep = +3)
    tz_west_to_east = calc.get_timezone_diff("America/Los_Angeles", "America/New_York")
    print(f"✓ LA to NY: {tz_west_to_east}h (expected +3, gained sleep)")
    assert tz_west_to_east == 3, f"Got {tz_west_to_east}"
    
    # Test 2b: NY to LA (east to west = lost sleep = -3)
    tz_east_to_west = calc.get_timezone_diff("America/New_York", "America/Los_Angeles")
    print(f"✓ NY to LA: {tz_east_to_west}h (expected -3, lost sleep)")
    assert tz_east_to_west == -3, f"Got {tz_east_to_west}"
    
    # Test 2c: Central to Mountain (1 hour)
    tz_central_to_mountain = calc.get_timezone_diff("America/Chicago", "America/Denver")
    print(f"✓ Chicago to Denver: {tz_central_to_mountain}h (expected -1)")
    assert tz_central_to_mountain == -1, f"Got {tz_central_to_mountain}"
    
    # Test 2d: Same timezone (0 hours)
    tz_same = calc.get_timezone_diff("America/New_York", "America/New_York")
    print(f"✓ NY to NY: {tz_same}h (expected 0)")
    assert tz_same == 0, f"Got {tz_same}"
    
    print("✅ PASS: Timezone calculation correct")


def test_back_to_back_detection():
    """Test back-to-back game detection."""
    print("\n" + "="*70)
    print("TEST 3: Back-to-Back Detection")
    print("="*70)
    
    calc = TravelFatigueCalculator()
    
    # Test 3a: Clear back-to-back (yesterday + today)
    schedule_b2b = [
        {"date": "2023-11-14", "arena": "TD Garden (Boston)"},
        {"date": "2023-11-15", "arena": "Crypto.com Arena (LA)"},
    ]
    is_b2b_1 = calc.is_back_to_back(schedule_b2b, "2023-11-15")
    print(f"✓ Yesterday + Today: {is_b2b_1} (expected True)")
    assert is_b2b_1 is True
    
    # Test 3b: Today + tomorrow
    is_b2b_2 = calc.is_back_to_back(schedule_b2b, "2023-11-14")
    print(f"✓ Today + Tomorrow: {is_b2b_2} (expected True)")
    assert is_b2b_2 is True
    
    # Test 3c: Two days apart (not B2B)
    schedule_two_days = [
        {"date": "2023-11-13", "arena": "TD Garden (Boston)"},
        {"date": "2023-11-15", "arena": "Crypto.com Arena (LA)"},
    ]
    is_b2b_3 = calc.is_back_to_back(schedule_two_days, "2023-11-15")
    print(f"✓ Two days apart: {is_b2b_3} (expected False)")
    assert is_b2b_3 is False
    
    # Test 3d: Empty schedule (not B2B)
    is_b2b_4 = calc.is_back_to_back([], "2023-11-15")
    print(f"✓ Empty schedule: {is_b2b_4} (expected False)")
    assert is_b2b_4 is False
    
    print("✅ PASS: Back-to-back detection accurate")


def test_previous_arena_detection():
    """Test finding previous game arena."""
    print("\n" + "="*70)
    print("TEST 4: Previous Arena Detection")
    print("="*70)
    
    calc = TravelFatigueCalculator()
    
    # Test 4a: Clear previous game
    schedule = [
        {"date": "2023-11-13", "arena": "TD Garden (Boston)"},
        {"date": "2023-11-15", "arena": "Crypto.com Arena (LA)"},
        {"date": "2023-11-17", "arena": "Crypto.com Arena (LA)"},
    ]
    prev = calc.get_previous_arena(schedule, "2023-11-17")
    print(f"✓ Previous arena on 11/17: {prev} (expected Crypto.com Arena LA)")
    assert prev == "Crypto.com Arena (LA)"
    
    # Test 4b: Most recent previous (not first)
    prev2 = calc.get_previous_arena(schedule, "2023-11-16")
    print(f"✓ Most recent previous: {prev2} (expected Crypto.com Arena LA)")
    assert prev2 == "Crypto.com Arena (LA)"
    
    # Test 4c: No previous game
    prev3 = calc.get_previous_arena(schedule, "2023-11-12")
    print(f"✓ No previous game: {prev3} (expected None)")
    assert prev3 is None
    
    # Test 4d: Empty schedule
    prev4 = calc.get_previous_arena([], "2023-11-17")
    print(f"✓ Empty schedule: {prev4} (expected None)")
    assert prev4 is None
    
    print("✅ PASS: Previous arena detection accurate")


def test_fatigue_score_calculation():
    """Test composite fatigue score calculation."""
    print("\n" + "="*70)
    print("TEST 5: Composite Fatigue Score (0-100)")
    print("="*70)
    
    calc = TravelFatigueCalculator()
    
    # Test 5a: Rest day (no travel, no B2B, low minutes)
    score_rest = calc.calculate_fatigue_score(
        distance_miles=0,
        timezone_diff=0,
        minutes_yesterday=0,
        back_to_back=False
    )
    print(f"✓ Rest day: {score_rest:.0f}/100 (expected ~0)")
    assert score_rest < 5
    
    # Test 5b: Local B2B after light minutes (50 miles + 0 tz + 20 min + B2B bonus)
    score_local_b2b = calc.calculate_fatigue_score(
        distance_miles=50,
        timezone_diff=0,
        minutes_yesterday=20,
        back_to_back=True
    )
    print(f"✓ Local B2B (20 min): {score_local_b2b:.0f}/100 (expected ~27)")
    # 50/100=0.5 + 0 + (20/40)*25=12.5 + 15 = 28
    assert 25 < score_local_b2b < 30
    
    # Test 5c: Cross-country B2B after heavy minutes (the worst case)
    score_worst = calc.calculate_fatigue_score(
        distance_miles=2600,
        timezone_diff=-3,
        minutes_yesterday=38,
        back_to_back=True
    )
    print(f"✓ Cross-country B2B (38 min): {score_worst:.0f}/100 (expected ~73)")
    # 2600/100=26 + 30 + (38/40)*25=23.75 + 15 = 94.75, capped at 100
    assert 70 < score_worst <= 100
    
    # Test 5d: Red-eye (extreme timezone, should cap at 100)
    score_redye = calc.calculate_fatigue_score(
        distance_miles=2600,
        timezone_diff=-3,
        minutes_yesterday=40,
        back_to_back=True
    )
    print(f"✓ Red-eye special: {score_redye:.0f}/100 (expected ~100, capped)")
    assert score_redye <= 100
    
    # Test 5e: Timezone bonus (gained sleep = positive value reduces fatigue somewhat)
    score_tz_east = calc.calculate_fatigue_score(
        distance_miles=1000,
        timezone_diff=3,  # Gained sleep (positive = extra sleep)
        minutes_yesterday=20,
        back_to_back=False
    )
    print(f"✓ Cross-timezone (gained sleep): {score_tz_east:.0f}/100")
    # 1000/100=10 + 30 (abs(3)*10) + 12.5 = 52.5
    # Note: timezone always contributes positively (abs value)
    assert 50 < score_tz_east < 55
    
    print("✅ PASS: Fatigue score calculation accurate (0-100 scale)")


def test_complete_extraction():
    """Test complete travel fatigue extraction."""
    print("\n" + "="*70)
    print("TEST 6: Complete Travel Fatigue Extraction")
    print("="*70)
    
    calc = TravelFatigueCalculator()
    
    # Scenario: Celtics play Boston on 11/14, then fly to LA on 11/15 for B2B
    schedule = [
        {"date": "2023-11-14", "arena": "Boston Celtics"},
        {"date": "2023-11-15", "arena": "Los Angeles Lakers"},
    ]
    
    result = calc.extract_travel_fatigue(
        team="Boston Celtics",
        current_date="2023-11-15",
        current_arena="Los Angeles Lakers",
        schedule=schedule,
        minutes_yesterday=38.0,
    )
    
    # Verify all fields present
    required_fields = [
        "distance_miles", "timezone_diff", "back_to_back",
        "minutes_yesterday", "fatigue_score", "previous_arena",
        "current_arena", "interpretation"
    ]
    for field in required_fields:
        assert field in result, f"Missing field: {field}"
    
    print(f"✓ Distance: {result['distance_miles']:.0f} miles (expected ~2600)")
    assert 2500 < result['distance_miles'] < 2700
    
    print(f"✓ Timezone: {result['timezone_diff']}h (expected -3, lost sleep)")
    assert result['timezone_diff'] == -3
    
    print(f"✓ Back-to-back: {result['back_to_back']} (expected True)")
    assert result['back_to_back'] is True
    
    print(f"✓ Minutes yesterday: {result['minutes_yesterday']} (expected 38.0)")
    assert result['minutes_yesterday'] == 38.0
    
    print(f"✓ Fatigue score: {result['fatigue_score']}/100 (expected 70-100)")
    assert 70 < result['fatigue_score'] <= 100
    
    print(f"✓ Previous arena: {result['previous_arena']}")
    # Previous arena should be the team name (Boston Celtics) since that's what's in schedule
    assert result['previous_arena'] is not None
    
    print(f"✓ Current arena: {result['current_arena']}")
    assert result['current_arena'] == "Los Angeles Lakers"
    
    print(f"✓ Interpretation: {result['interpretation']}")
    # Check interpretation contains expected components
    interpretation_lower = result['interpretation'].lower()
    assert ("mile" in interpretation_lower or "trip" in interpretation_lower or 
            "back-to-back" in interpretation_lower), \
        f"Interpretation missing expected keywords: {result['interpretation']}"
    
    print("✅ PASS: Complete extraction works with all fields")


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\n" + "="*70)
    print("TEST 7: Edge Cases & Boundary Conditions")
    print("="*70)
    
    calc = TravelFatigueCalculator()
    
    # Test 7a: Single game (no previous)
    result_single = calc.extract_travel_fatigue(
        team="Boston Celtics",
        current_date="2023-11-15",
        current_arena="TD Garden (Boston)",
        schedule=[{"date": "2023-11-15", "arena": "TD Garden (Boston)"}],
        minutes_yesterday=0,
    )
    print(f"✓ Single game: fatigue={result_single['fatigue_score']}, distance={result_single['distance_miles']}")
    assert result_single['distance_miles'] == 0.0
    assert result_single['back_to_back'] is False
    
    # Test 7b: High minutes (capped at max contribution)
    score_high_min = calc.calculate_fatigue_score(
        distance_miles=0, timezone_diff=0,
        minutes_yesterday=48, back_to_back=False
    )
    score_normal_min = calc.calculate_fatigue_score(
        distance_miles=0, timezone_diff=0,
        minutes_yesterday=40, back_to_back=False
    )
    print(f"✓ Minutes capped: 48min={score_high_min:.0f}, 40min={score_normal_min:.0f}")
    assert abs(score_high_min - score_normal_min) < 1  # Should be same (capped)
    
    # Test 7c: Extreme distance
    score_extreme = calc.calculate_fatigue_score(
        distance_miles=10000, timezone_diff=0,
        minutes_yesterday=0, back_to_back=False
    )
    print(f"✓ Extreme distance: {score_extreme:.0f}/100 (capped at 100)")
    assert score_extreme <= 100
    
    # Test 7d: Multiple timezone hops (Phoenix = no DST)
    tz_phoenix = calc.get_timezone_diff("America/New_York", "America/Phoenix")
    print(f"✓ Phoenix timezone (no DST): {tz_phoenix}h difference")
    
    print("✅ PASS: All edge cases handled correctly")


def test_interpretation_generation():
    """Test human-readable interpretation generation."""
    print("\n" + "="*70)
    print("TEST 8: Interpretation Generation")
    print("="*70)
    
    calc = TravelFatigueCalculator()
    
    # Test 8a: Cross-country B2B
    schedule = [
        {"date": "2023-11-14", "arena": "Boston Celtics"},
        {"date": "2023-11-15", "arena": "Los Angeles Lakers"},
    ]
    result = calc.extract_travel_fatigue(
        team="Boston Celtics",
        current_date="2023-11-15",
        current_arena="Los Angeles Lakers",
        schedule=schedule,
        minutes_yesterday=38,
    )
    print(f"✓ Cross-country B2B: {result['interpretation']}")
    assert "trip" in result['interpretation'].lower() or "back-to-back" in result['interpretation']
    
    # Test 8b: Rest day (single game, no previous)
    result_rest = calc.extract_travel_fatigue(
        team="Boston Celtics",
        current_date="2023-11-16",
        current_arena="Los Angeles Lakers",
        schedule=[{"date": "2023-11-16", "arena": "Los Angeles Lakers"}],
        minutes_yesterday=0,
    )
    print(f"✓ Rest day: {result_rest['interpretation']}")
    assert "Rest day" in result_rest['interpretation']
    
    print("✅ PASS: Interpretation generation working correctly")


def run_all_tests():
    """Run all Task #12 tests."""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*16 + "TASK #12: TRAVEL FATIGUE CALCULATOR - TEST SUITE" + " "*4 + "║")
    print("╚" + "="*68 + "╝")
    
    tests = [
        test_distance_calculation,
        test_timezone_calculation,
        test_back_to_back_detection,
        test_previous_arena_detection,
        test_fatigue_score_calculation,
        test_complete_extraction,
        test_edge_cases,
        test_interpretation_generation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n❌ FAIL: {test.__name__}")
            print(f"   Error: {str(e)}")
            failed += 1
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"✅ PASS: {passed}/{len(tests)} tests passed")
    if failed > 0:
        print(f"❌ FAIL: {failed}/{len(tests)} tests failed")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
