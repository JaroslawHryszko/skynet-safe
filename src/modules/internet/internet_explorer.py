"""Module for internet exploration."""

import logging
from typing import Dict, List, Any, Optional
import time

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
            
            if self.search_engine == "duckduckgo":
                return self._search_duckduckgo(query)
            else:
                logger.warning(f"Unsupported search engine: {self.search_engine}, using DuckDuckGo")
                return self._search_duckduckgo(query)
                
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
            logger.error(f"Error searching with DuckDuckGo: {e}")
            return []
