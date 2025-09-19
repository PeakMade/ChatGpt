"""
News Fetcher Module
Fetches latest news headlines to provide current information to the AI assistant
"""

import requests
import time
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class NewsFetcher:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('NEWS_API_KEY')
        self.base_url = "https://newsapi.org/v2"
        self.cache_file = "news_cache.json"
        self.cache_duration = 3600  # 1 hour cache
        
    def fetch_latest_news(self, country: str = "us", category: str = None, sources: str = None) -> List[Dict]:
        """Fetch latest news headlines from NewsAPI"""
        if not self.api_key:
            print("⚠️ No NewsAPI key found. Set NEWS_API_KEY environment variable.")
            return []
            
        try:
            # Check cache first
            cached_news = self._get_cached_news()
            if cached_news:
                print("📰 Using cached news data")
                return cached_news
            
            # Build URL parameters
            params = {
                "apiKey": self.api_key,
                "pageSize": 20,  # Get more articles for variety
                "sortBy": "publishedAt"
            }
            
            # Choose endpoint and parameters
            if sources:
                url = f"{self.base_url}/top-headlines"
                params["sources"] = sources
            else:
                url = f"{self.base_url}/top-headlines"
                params["country"] = country
                if category:
                    params["category"] = category
            
            print(f"🔍 Fetching news from: {country}" + (f" ({category})" if category else ""))
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get('articles', [])
                
                # Process and clean articles
                processed_articles = self._process_articles(articles)
                
                # Cache the results
                self._cache_news(processed_articles)
                
                print(f"✅ Fetched {len(processed_articles)} news articles")
                return processed_articles
            else:
                print(f"❌ Failed to fetch news: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching news: {e}")
            return []
    
    def _process_articles(self, articles: List[Dict]) -> List[Dict]:
        """Process and clean news articles"""
        processed = []
        
        for article in articles:
            # Skip articles with missing data
            if not article.get('title') or article.get('title') == '[Removed]':
                continue
                
            processed_article = {
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', ''),
                'publishedAt': article.get('publishedAt', ''),
                'urlToImage': article.get('urlToImage', ''),
                'content': article.get('content', '')[:200] + '...' if article.get('content') else ''
            }
            processed.append(processed_article)
            
        return processed
    
    def _get_cached_news(self) -> Optional[List[Dict]]:
        """Get news from cache if still fresh"""
        try:
            if not os.path.exists(self.cache_file):
                return None
                
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache is still fresh
            cache_time = datetime.fromisoformat(cache_data.get('timestamp', ''))
            if datetime.now() - cache_time < timedelta(seconds=self.cache_duration):
                return cache_data.get('articles', [])
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error reading news cache: {e}")
            return None
    
    def _cache_news(self, articles: List[Dict]):
        """Cache news articles to file"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'articles': articles
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Error caching news: {e}")
    
    def get_news_summary(self, max_articles: int = 10) -> str:
        """Get a formatted summary of latest news for AI context"""
        articles = self.fetch_latest_news()
        
        if not articles:
            return "No current news available."
        
        # Limit articles for context
        articles = articles[:max_articles]
        
        summary = f"📰 **Current News Headlines** (as of {datetime.now().strftime('%B %d, %Y')}):\n\n"
        
        for i, article in enumerate(articles, 1):
            summary += f"{i}. **{article['title']}**\n"
            if article['description']:
                summary += f"   {article['description'][:150]}...\n"
            summary += f"   Source: {article['source']}\n\n"
        
        return summary
    
    def search_news(self, query: str, language: str = "en") -> List[Dict]:
        """Search for specific news topics"""
        if not self.api_key:
            return []
            
        try:
            url = f"{self.base_url}/everything"
            params = {
                "q": query,
                "apiKey": self.api_key,
                "language": language,
                "sortBy": "publishedAt",
                "pageSize": 10
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._process_articles(data.get('articles', []))
            else:
                print(f"❌ Failed to search news: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error searching news: {e}")
            return []

# Global news fetcher instance
news_fetcher = NewsFetcher()

def get_current_news_context(max_articles: int = 5) -> str:
    """Quick function to get news context for AI responses"""
    return news_fetcher.get_news_summary(max_articles)

if __name__ == "__main__":
    # Test the news fetcher
    fetcher = NewsFetcher()
    news = fetcher.fetch_latest_news()
    
    if news:
        print("Latest News Headlines:")
        for article in news[:5]:
            print("-", article['title'])
    else:
        print("No news data available.")