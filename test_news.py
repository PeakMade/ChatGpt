"""
Test script for News Fetcher integration
Run this to test the news functionality before deploying
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_news_fetcher():
    """Test the news fetcher functionality"""
    print("🧪 Testing News Fetcher...")
    
    try:
        from news_fetcher import NewsFetcher, get_current_news_context
        
        # Test without API key (should handle gracefully)
        fetcher = NewsFetcher()
        print("✅ News fetcher imported successfully")
        
        # Test context generation (will work with cached data or fail gracefully)
        context = get_current_news_context(3)
        print("✅ News context generation works")
        print(f"Context preview: {context[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ News fetcher test failed: {e}")
        return False

def test_app_integration():
    """Test the app integration"""
    print("🧪 Testing App Integration...")
    
    try:
        from app_flask import NEWS_FETCHER_AVAILABLE
        print(f"✅ News fetcher available in app: {NEWS_FETCHER_AVAILABLE}")
        return True
        
    except Exception as e:
        print(f"❌ App integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing News Integration")
    print("=" * 50)
    
    # Run tests
    news_test = test_news_fetcher()
    app_test = test_app_integration()
    
    print("\n" + "=" * 50)
    if news_test and app_test:
        print("✅ All tests passed! Ready to deploy.")
        print("\n📝 Setup Instructions:")
        print("1. Get a free API key from https://newsapi.org/register")
        print("2. Set environment variable: NEWS_API_KEY=your_api_key")
        print("3. Deploy your app - it will now have current news context!")
    else:
        print("❌ Some tests failed. Check the errors above.")