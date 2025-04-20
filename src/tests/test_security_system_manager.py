"""Testy modułu systemu bezpieczeństwa."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any
import json
import os

from src.modules.security.security_system_manager import SecuritySystemManager


@pytest.fixture
def security_config():
    """Fixture z konfiguracją testową dla modułu bezpieczeństwa."""
    return {
        "allowed_domains": ["wikipedia.org", "github.com", "python.org"],
        "input_length_limit": 1000,
        "max_api_calls_per_hour": 100,
        "security_logging_level": "INFO",
        "max_consecutive_requests": 20,
        "suspicious_patterns": [
            "eval\\(.*\\)",
            "exec\\(.*\\)",
            "import os.*system",
            "rm -rf"
        ],
        "security_lockout_time": 30 * 60,  # 30 minut
        "security_alert_threshold": 3
    }


@pytest.fixture
def mock_model_manager():
    """Fixture z mock'iem menedżera modelu."""
    mock = MagicMock()
    mock.generate_response.return_value = "Bezpieczna odpowiedź testowa"
    return mock


def test_security_manager_initialization(security_config):
    """Test inicjalizacji menedżera bezpieczeństwa."""
    manager = SecuritySystemManager(security_config)
    
    assert manager.config == security_config
    assert manager.allowed_domains == security_config["allowed_domains"]
    assert manager.input_length_limit == security_config["input_length_limit"]
    assert manager.max_api_calls_per_hour == security_config["max_api_calls_per_hour"]
    assert manager.suspicious_patterns == security_config["suspicious_patterns"]
    assert manager.security_lockout_time == security_config["security_lockout_time"]
    assert manager.security_alert_threshold == security_config["security_alert_threshold"]
    assert manager.security_incidents == []
    assert manager.active_lockouts == {}


def test_check_input_safety(security_config):
    """Test sprawdzania bezpieczeństwa danych wejściowych."""
    manager = SecuritySystemManager(security_config)
    
    # Bezpieczne wejście
    safe_input = "To jest bezpieczne zapytanie o sztuczną inteligencję."
    assert manager.check_input_safety(safe_input) == (True, "Input jest bezpieczny")
    
    # Niebezpieczne wejście (za długie)
    long_input = "a" * (security_config["input_length_limit"] + 1)
    assert manager.check_input_safety(long_input) == (False, "Input przekracza limit długości")
    
    # Niebezpieczne wejście (zawiera podejrzany wzorzec)
    suspicious_input = "Jak mogę użyć eval('print(\"hack\")')??"
    assert manager.check_input_safety(suspicious_input) == (False, "Input zawiera potencjalnie niebezpieczne wzorce")
    
    # Test, czy incydenty bezpieczeństwa są zapisywane
    assert len(manager.security_incidents) == 2


def test_check_url_safety(security_config):
    """Test sprawdzania bezpieczeństwa adresów URL."""
    manager = SecuritySystemManager(security_config)
    
    # Bezpieczny URL (z dozwolonej domeny)
    safe_url = "https://www.wikipedia.org/wiki/Artificial_intelligence"
    assert manager.check_url_safety(safe_url) == (True, "URL jest z dozwolonej domeny")
    
    # Niebezpieczny URL (z niedozwolonej domeny)
    unsafe_url = "https://example.com/suspicious"
    assert manager.check_url_safety(unsafe_url) == (False, "URL nie jest z dozwolonej domeny")


def test_check_response_safety(security_config, mock_model_manager):
    """Test sprawdzania bezpieczeństwa odpowiedzi."""
    manager = SecuritySystemManager(security_config)
    
    # Bezpieczna odpowiedź
    safe_response = "To jest bezpieczna odpowiedź na zapytanie użytkownika."
    assert manager.check_response_safety(safe_response) == (True, "Odpowiedź jest bezpieczna")
    
    # Niebezpieczna odpowiedź (zawiera podejrzany kod)
    unsafe_response = "Możesz rozwiązać problem używając: import os; os.system('rm -rf /')"
    assert manager.check_response_safety(unsafe_response) == (False, "Odpowiedź zawiera potencjalnie niebezpieczne treści")


def test_sanitize_input(security_config):
    """Test sanityzacji danych wejściowych."""
    manager = SecuritySystemManager(security_config)
    
    # Test wejścia zawierającego potencjalnie niebezpieczne elementy
    dangerous_input = "Jak użyć eval('print(\"hack\")')"
    sanitized = manager.sanitize_input(dangerous_input)
    
    # Sprawdź, czy niebezpieczne elementy zostały usunięte/zneutralizowane
    assert "eval" not in sanitized or "eval()" not in sanitized
    assert len(sanitized) <= security_config["input_length_limit"]


def test_enforce_rate_limiting(security_config):
    """Test wymuszania limitów szybkości żądań."""
    manager = SecuritySystemManager(security_config)
    
    # Symulacja normalnego użycia (poniżej limitu)
    for _ in range(5):
        assert manager.enforce_rate_limiting("user123") == (True, "Żądanie w granicach limitu")
    
    # Symulacja intensywnego użycia (przekracza limit)
    manager.user_request_counts["user123"] = security_config["max_consecutive_requests"]
    assert manager.enforce_rate_limiting("user123") == (False, "Przekroczono limit żądań")


def test_check_api_usage(security_config):
    """Test sprawdzania użycia API."""
    manager = SecuritySystemManager(security_config)
    
    # Symulacja normalnego użycia API (poniżej limitu)
    assert manager.check_api_usage() == (True, "Użycie API w granicach limitu")
    
    # Symulacja intensywnego użycia API (przekracza limit)
    manager.api_calls_count = security_config["max_api_calls_per_hour"] + 1
    assert manager.check_api_usage() == (False, "Przekroczono limit wywołań API")


def test_handle_security_incident(security_config):
    """Test obsługi incydentu bezpieczeństwa."""
    manager = SecuritySystemManager(security_config)
    
    # Pierwszy incydent
    manager.handle_security_incident("user123", "Podejrzane zachowanie", "TEST")
    assert len(manager.security_incidents) == 1
    assert manager.user_incident_counts.get("user123") == 1
    
    # Osiągnięcie progu alertu
    for _ in range(security_config["security_alert_threshold"] - 1):
        manager.handle_security_incident("user123", "Podejrzane zachowanie", "TEST")
    
    # Sprawdź, czy użytkownik jest zablokowany
    assert "user123" in manager.active_lockouts
    assert manager.user_incident_counts.get("user123") == security_config["security_alert_threshold"]


def test_is_user_locked_out(security_config):
    """Test sprawdzania, czy użytkownik jest zablokowany."""
    manager = SecuritySystemManager(security_config)
    
    # Użytkownik nie jest zablokowany
    assert not manager.is_user_locked_out("user123")
    
    # Zablokuj użytkownika
    manager.active_lockouts["user123"] = float('inf')  # Nieskończony czas blokady dla testu
    
    # Sprawdź, czy użytkownik jest zablokowany
    assert manager.is_user_locked_out("user123")


def test_log_security_event(security_config):
    """Test logowania zdarzeń bezpieczeństwa."""
    with patch("src.modules.security.security_system_manager.logger") as mock_logger:
        manager = SecuritySystemManager(security_config)
        
        # Resetowanie mock_logger
        mock_logger.reset_mock()
        
        # Logowanie zdarzenia informacyjnego
        manager.log_security_event("Zdarzenie testowe", "INFO")
        mock_logger.info.assert_called_once_with("Zdarzenie testowe")
        
        # Logowanie zdarzenia ostrzegawczego
        manager.log_security_event("Ostrzeżenie testowe", "WARNING")
        mock_logger.warning.assert_called_once_with("Ostrzeżenie testowe")
        
        # Logowanie zdarzenia krytycznego
        manager.log_security_event("Błąd krytyczny testowy", "ERROR")
        mock_logger.error.assert_called_once_with("Błąd krytyczny testowy")


def test_generate_security_report(security_config):
    """Test generowania raportu bezpieczeństwa."""
    manager = SecuritySystemManager(security_config)
    
    # Dodanie incydentów testowych
    manager.handle_security_incident("user1", "Podejrzane zapytanie", "INPUT")
    manager.handle_security_incident("user2", "Niebezpieczny URL", "URL")
    manager.handle_security_incident("user1", "Zbyt wiele żądań", "RATE")
    
    # Generowanie raportu
    report = manager.generate_security_report()
    
    # Sprawdzenie zawartości raportu
    assert isinstance(report, dict)
    assert "total_incidents" in report
    assert report["total_incidents"] == 3
    assert "incidents_by_type" in report
    assert "affected_users" in report
    assert "lockouts" in report