"""Module for internet exploration."""

import logging
from typing import Dict, List, Any, Optional
import time
import re
import json
from urllib.parse import urljoin, quote

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class InternetExplorer:
    """Class for exploring and retrieving information from the internet."""

    def __init__(self, config: Dict[str, Any]):
        """Initialization of internet explorer.
        
        Args:
            config: Configuration containing search parameters, etc.
        """
        self.config = config
        self.search_engine = config.get("search_engine", "duckduckgo")
        self.max_results = config.get("max_results", 5)
        self.timeout = config.get("timeout", 30)
        self.fallback_engines = config.get("fallback_engines", ["reddit", "direct_search"])
        self.rate_limit_cooldown = config.get("rate_limit_cooldown", 300)  # 5 minutes
        self.last_rate_limit = {}
        
        logger.info(f"Initializing internet explorer (search engine: {self.search_engine})...")
        
        # HTTP session for multiple requests
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        logger.info("Internet explorer initialized successfully")
    
    def search_information(self, query: str) -> List[Dict[str, Any]]:
        """Search for information based on a query.
        
        Args:
            query: Search query
            
        Returns:
            List of search results in the format [{"title": str, "body": str, "href": str}]
        """
        try:
            logger.info(f"Searching for information about: {query}")
            
            # Try primary search engine
            results = self._search_with_fallback(query)
            return results
                
        except Exception as e:
            logger.error(f"Error while searching for information: {e}")
            return []
    
    def fetch_content(self, url: str) -> Optional[str]:
        """Retrieve content from a web page.
        
        Args:
            url: URL of the page to retrieve
            
        Returns:
            Page content as text or None in case of error
        """
        try:
            logger.info(f"Retrieving content from: {url}")
            
            # Get the page
            response = requests.get(url, timeout=self.timeout)
            
            # Check response status
            if response.status_code == 200:
                # Parse HTML
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract text
                content = soup.get_text(separator=" ", strip=True)
                
                # Truncate content if it's too long (optional)
                if len(content) > 10000:
                    content = content[:10000] + "..."
                
                return content
            else:
                logger.warning(f"HTTP error {response.status_code} when retrieving content from {url}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving content from {url}: {e}")
            return None
    
    def _search_with_fallback(self, query: str) -> List[Dict[str, Any]]:
        """Search with fallback mechanism in case of rate limiting.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        # Check if DuckDuckGo is rate limited
        if self._is_rate_limited("duckduckgo"):
            logger.warning("DuckDuckGo is rate limited, using fallback engines")
            return self._search_fallback(query)
        
        # Try DuckDuckGo first
        results = self._search_duckduckgo(query)
        
        # If no results or rate limited, try fallback
        if not results:
            logger.warning("No results from DuckDuckGo, trying fallback engines")
            return self._search_fallback(query)
        
        return results
    
    def _is_rate_limited(self, engine: str) -> bool:
        """Check if a search engine is currently rate limited.
        
        Args:
            engine: Name of the search engine
            
        Returns:
            True if rate limited, False otherwise
        """
        if engine in self.last_rate_limit:
            time_since_limit = time.time() - self.last_rate_limit[engine]
            return time_since_limit < self.rate_limit_cooldown
        return False
    
    def _mark_rate_limited(self, engine: str):
        """Mark a search engine as rate limited.
        
        Args:
            engine: Name of the search engine
        """
        self.last_rate_limit[engine] = time.time()
        logger.warning(f"Marking {engine} as rate limited for {self.rate_limit_cooldown} seconds")
    
    def _search_fallback(self, query: str) -> List[Dict[str, Any]]:
        """Search using fallback engines.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        for engine in self.fallback_engines:
            try:
                if engine == "reddit":
                    results = self._search_reddit(query)
                elif engine == "direct_search":
                    results = self._search_direct(query)
                else:
                    continue
                
                if results:
                    logger.info(f"Found {len(results)} results using fallback engine: {engine}")
                    return results
                    
            except Exception as e:
                logger.error(f"Error with fallback engine {engine}: {e}")
                continue
        
        logger.warning("All search engines failed")
        return []
    
    def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """Search for information using DuckDuckGo.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        try:
            # Initialize DuckDuckGo client
            with DDGS() as ddgs:
                # Search for text
                results = list(ddgs.text(query, max_results=self.max_results))
                
                logger.info(f"Found {len(results)} results for query: {query}")
                return results
                
        except Exception as e:
            error_str = str(e).lower()
            if "ratelimit" in error_str or "rate limit" in error_str or "202" in error_str:
                logger.warning(f"DuckDuckGo rate limit detected: {e}")
                self._mark_rate_limited("duckduckgo")
            else:
                logger.error(f"Error searching with DuckDuckGo: {e}")
            return []
    
    def _search_reddit(self, query: str) -> List[Dict[str, Any]]:
        """Search Reddit for relevant discussions.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        try:
            # Use Reddit's JSON API
            search_url = f"https://www.reddit.com/search.json?q={quote(query)}&limit={min(self.max_results, 10)}&sort=relevance"
            
            response = self.session.get(search_url, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for post in data.get('data', {}).get('children', []):
                    post_data = post.get('data', {})
                    
                    # Skip if no title or content
                    if not post_data.get('title'):
                        continue
                    
                    # Combine title and selftext for body
                    body = post_data.get('selftext', '')[:500]  # Limit length
                    if not body:
                        body = post_data.get('title', '')[:200]
                    
                    result = {
                        'title': f"Reddit: {post_data.get('title', 'No title')}",
                        'body': body,
                        'href': f"https://reddit.com{post_data.get('permalink', '')}"
                    }
                    results.append(result)
                
                logger.info(f"Found {len(results)} Reddit results for query: {query}")
                return results[:self.max_results]
            else:
                logger.warning(f"Reddit search returned status: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error searching Reddit: {e}")
            return []
    
    def _search_direct(self, query: str) -> List[Dict[str, Any]]:
        """Direct search by trying to access relevant websites.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        try:
            # List of websites to try based on query content
            sites_to_try = []
            
            # Technology-related queries
            if any(word in query.lower() for word in ['python', 'programming', 'code', 'software', 'ai', 'ml']):
                sites_to_try.extend([
                    f"https://stackoverflow.com/search?q={quote(query)}",
                    f"https://github.com/search?q={quote(query)}"
                ])
            
            # News-related queries
            if any(word in query.lower() for word in ['news', 'current', 'today', 'recent']):
                sites_to_try.extend([
                    f"https://news.ycombinator.com/",
                    f"https://www.bbc.com/search?q={quote(query)}"
                ])
            
            # General fallback - try Wikipedia
            sites_to_try.append(f"https://en.wikipedia.org/wiki/Special:Search?search={quote(query)}")
            
            results = []
            for url in sites_to_try[:3]:  # Limit to first 3 sites
                try:
                    content = self.fetch_content(url)
                    if content:
                        # Extract meaningful snippet
                        snippet = content[:300] if len(content) > 300 else content
                        
                        result = {
                            'title': f"Direct search: {url.split('/')[2]}",
                            'body': snippet,
                            'href': url
                        }
                        results.append(result)
                        
                        if len(results) >= self.max_results:
                            break
                            
                except Exception as e:
                    logger.debug(f"Failed to fetch {url}: {e}")
                    continue
            
            logger.info(f"Found {len(results)} direct search results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error in direct search: {e}")
            return []
