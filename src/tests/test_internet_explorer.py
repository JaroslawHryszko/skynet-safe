"""Testy modułu eksploracji internetowej."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any

from src.modules.internet.internet_explorer import InternetExplorer


@pytest.fixture
def internet_config():
    """Fixture z konfiguracją testową dla eksploracji internetowej."""
    return {
        "search_engine": "duckduckgo",
        "max_results": 3,
        "timeout": 10
    }


def test_internet_initialization(internet_config):
    """Test inicjalizacji eksploratora internetowego."""
    explorer = InternetExplorer(internet_config)
    assert explorer.config == internet_config
    assert explorer.search_engine == "duckduckgo"
    assert explorer.max_results == 3
    assert explorer.timeout == 10


def test_search_information(internet_config):
    """Test wyszukiwania informacji."""
    with patch("src.modules.internet.internet_explorer.DDGS") as mock_ddgs:
        # Konfiguracja mock'a wyszukiwarki
        mock_search_instance = MagicMock()
        mock_ddgs.return_value = mock_search_instance
        
        # Bezpośrednia konfiguracja wyników
        mock_results = [
            {"title": "Wynik 1", "body": "Opis wyniku 1", "href": "http://example.com/1"},
            {"title": "Wynik 2", "body": "Opis wyniku 2", "href": "http://example.com/2"},
            {"title": "Wynik 3", "body": "Opis wyniku 3", "href": "http://example.com/3"}
        ]
        # Upewnimy się, że mock zwraca faktycznie listę wyników
        mock_search_instance.text.return_value = mock_results
        
        # Symulacja działania _search_duckduckgo - główna metoda powinna zwrócić wyniki
        explorer = InternetExplorer(internet_config)
        explorer._search_duckduckgo = MagicMock(return_value=mock_results)
        
        results = explorer.search_information("testowe zapytanie")
        
        # Sprawdź, czy zwrócono listę wyników
        assert isinstance(results, list)
        assert len(results) == 3
        assert all(isinstance(item, dict) for item in results)
        assert "title" in results[0]
        assert "body" in results[0]
        assert "href" in results[0]


def test_fetch_content(internet_config):
    """Test pobierania zawartości ze strony."""
    with patch("src.modules.internet.internet_explorer.requests.get") as mock_get:
        # Konfiguracja mock'a dla requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body><h1>Testowa strona</h1><p>Treść strony</p></body></html>"
        mock_get.return_value = mock_response
        
        # Konfiguracja mock'a dla BeautifulSoup
        with patch("src.modules.internet.internet_explorer.BeautifulSoup") as mock_bs:
            mock_soup = MagicMock()
            mock_soup.get_text.return_value = "Testowa strona Treść strony"
            mock_bs.return_value = mock_soup
            
            explorer = InternetExplorer(internet_config)
            content = explorer.fetch_content("http://example.com")
            
            # Sprawdź, czy zwrócono string z zawartością
            assert isinstance(content, str)
            assert len(content) > 0
            mock_get.assert_called_once_with("http://example.com", timeout=10)


def test_fetch_content_error(internet_config):
    """Test obsługi błędu przy pobieraniu zawartości."""
    with patch("src.modules.internet.internet_explorer.requests.get") as mock_get:
        # Symulacja błędu połączenia
        mock_get.side_effect = Exception("Connection error")
        
        explorer = InternetExplorer(internet_config)
        content = explorer.fetch_content("http://example.com")
        
        # Sprawdź, czy zwrócono None w przypadku błędu
        assert content is None
