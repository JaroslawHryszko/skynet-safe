"""Moduł do eksploracji internetowej."""

import logging
from typing import Dict, List, Any, Optional
import time

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class InternetExplorer:
    """Klasa do eksploracji i pozyskiwania informacji z internetu."""

    def __init__(self, config: Dict[str, Any]):
        """Inicjalizacja eksploratora internetowego.
        
        Args:
            config: Konfiguracja zawierająca parametry wyszukiwania, itp.
        """
        self.config = config
        self.search_engine = config.get("search_engine", "duckduckgo")
        self.max_results = config.get("max_results", 5)
        self.timeout = config.get("timeout", 30)
        
        logger.info(f"Inicjalizacja eksploratora internetowego (wyszukiwarka: {self.search_engine})...")
        
        # Sesja HTTP dla wielokrotnych żądań
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        
        logger.info("Eksplorator internetowy zainicjalizowany pomyślnie")
    
    def search_information(self, query: str) -> List[Dict[str, Any]]:
        """Wyszukiwanie informacji na podstawie zapytania.
        
        Args:
            query: Zapytanie wyszukiwania
            
        Returns:
            Lista wyników wyszukiwania w formacie [{"title": str, "body": str, "href": str}]
        """
        try:
            logger.info(f"Wyszukiwanie informacji na temat: {query}")
            
            if self.search_engine == "duckduckgo":
                return self._search_duckduckgo(query)
            else:
                logger.warning(f"Nieobsługiwana wyszukiwarka: {self.search_engine}, używanie DuckDuckGo")
                return self._search_duckduckgo(query)
                
        except Exception as e:
            logger.error(f"Błąd przy wyszukiwaniu informacji: {e}")
            return []
    
    def fetch_content(self, url: str) -> Optional[str]:
        """Pobieranie zawartości ze strony internetowej.
        
        Args:
            url: Adres URL strony do pobrania
            
        Returns:
            Zawartość strony jako tekst lub None w przypadku błędu
        """
        try:
            logger.info(f"Pobieranie zawartości z: {url}")
            
            # Pobieranie strony
            response = requests.get(url, timeout=self.timeout)
            
            # Sprawdzenie statusu odpowiedzi
            if response.status_code == 200:
                # Parsowanie HTML
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Ekstrakcja tekstu
                content = soup.get_text(separator=" ", strip=True)
                
                # Skrócenie zawartości, jeśli jest zbyt długa (opcjonalnie)
                if len(content) > 10000:
                    content = content[:10000] + "..."
                
                return content
            else:
                logger.warning(f"Błąd HTTP {response.status_code} przy pobieraniu zawartości z {url}")
                return None
                
        except Exception as e:
            logger.error(f"Błąd przy pobieraniu zawartości z {url}: {e}")
            return None
    
    def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """Wyszukiwanie informacji za pomocą DuckDuckGo.
        
        Args:
            query: Zapytanie wyszukiwania
            
        Returns:
            Lista wyników wyszukiwania
        """
        try:
            # Inicjalizacja klienta DuckDuckGo
            with DDGS() as ddgs:
                # Wyszukiwanie tekstu
                results = list(ddgs.text(query, max_results=self.max_results))
                
                logger.info(f"Znaleziono {len(results)} wyników dla zapytania: {query}")
                return results
                
        except Exception as e:
            logger.error(f"Błąd przy wyszukiwaniu w DuckDuckGo: {e}")
            return []
