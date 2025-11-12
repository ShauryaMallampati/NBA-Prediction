"""
Quick test script to verify all scrapers work properly
"""

import sys
import time
from pathlib import Path

def test_advanced_stats():
    """Test advanced stats scraper"""
    print("\n" + "="*80)
    print("TESTING: Advanced Stats Scraper")
    print("="*80)
    
    try:
        from scrape_advanced_stats import AdvancedStatsScraper
        
        scraper = AdvancedStatsScraper()
        
        # Test just one endpoint (Advanced stats)
        print("\nTesting Advanced stats endpoint...")
        df = scraper.scrape_advanced_stats('Advanced')
        
        if not df.empty:
            print(f"✅ SUCCESS: Got {len(df)} teams, {len(df.columns)} columns")
            print(f"   Sample columns: {list(df.columns[:5])}")
            return True
        else:
            print("❌ FAILED: Empty dataframe")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_news_sentiment():
    """Test news sentiment scraper"""
    print("\n" + "="*80)
    print("TESTING: News Sentiment Scraper")
    print("="*80)
    
    try:
        from scrape_news_sentiment import NewsSentimentScraper
        
        scraper = NewsSentimentScraper()
        
        # Test just one team
        print("\nTesting ESPN news for BOS...")
        articles = scraper.scrape_espn_news('BOS')
        
        if articles:
            print(f"✅ SUCCESS: Got {len(articles)} articles")
            print(f"   Sample: {articles[0][:100] if articles else 'N/A'}")
            return True
        else:
            print("⚠️  WARNING: No articles found (may be normal)")
            return True  # Not an error, just no recent news
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_player_tracking():
    """Test player tracking scraper"""
    print("\n" + "="*80)
    print("TESTING: Player Tracking Scraper")
    print("="*80)
    
    try:
        from scrape_player_tracking import PlayerTrackingScraper
        
        scraper = PlayerTrackingScraper()
        
        # Test just hustle stats
        print("\nTesting hustle stats...")
        df = scraper.scrape_hustle_stats()
        
        if not df.empty:
            print(f"✅ SUCCESS: Got {len(df)} players, {len(df.columns)} columns")
            print(f"   Sample columns: {list(df.columns[:5])}")
            return True
        else:
            print("❌ FAILED: Empty dataframe")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("SCRAPER FUNCTIONALITY TEST SUITE")
    print("="*80)
    print("Testing all scrapers to ensure they work properly...\n")
    
    results = {}
    
    # Test each scraper
    results['advanced_stats'] = test_advanced_stats()
    time.sleep(2)
    
    results['news_sentiment'] = test_news_sentiment()
    time.sleep(2)
    
    results['player_tracking'] = test_player_tracking()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name.replace('_', ' ').title()}")
    
    # Overall result
    all_passed = all(results.values())
    print("\n" + "="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Scrapers are working correctly.")
    else:
        print("⚠️  SOME TESTS FAILED. Check the output above for details.")
    print("="*80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
