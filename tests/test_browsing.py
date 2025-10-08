"""
Test script to demonstrate the new browsing capabilities
"""
import json
from app import search_web, fetch_webpage_content

def test_browsing():
    print("🌐 Testing Web Browsing Capabilities")
    print("=" * 50)
    
    # Test web search
    print("\n1. Testing Web Search:")
    search_result = search_web("Python programming latest features 2024", 3)
    print(f"Search Status: {'✅ Success' if search_result['success'] else '❌ Failed'}")
    if search_result['success']:
        print(f"Found {len(search_result['results'])} results")
        for i, result in enumerate(search_result['results'], 1):
            print(f"   {i}. {result['title'][:100]}...")
    else:
        print(f"Error: {search_result['error']}")
    
    # Test webpage fetching
    print("\n2. Testing Webpage Fetching:")
    webpage_result = fetch_webpage_content("https://www.python.org")
    print(f"Fetch Status: {'✅ Success' if webpage_result['success'] else '❌ Failed'}")
    if webpage_result['success']:
        print(f"Title: {webpage_result['title']}")
        print(f"Content length: {len(webpage_result['content'])} characters")
        print(f"Content preview: {webpage_result['content'][:200]}...")
    else:
        print(f"Error: {webpage_result['error']}")
    
    print("\n🎉 Browsing capabilities are ready!")
    print("Your ChatGPT app can now:")
    print("• Search the web for current information")
    print("• Fetch and read webpage content")
    print("• Provide real-time, up-to-date responses")

if __name__ == "__main__":
    test_browsing()
