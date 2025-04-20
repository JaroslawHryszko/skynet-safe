"""Testy modułu komunikacji."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any

from src.modules.communication.communication_interface import CommunicationInterface


@pytest.fixture
def communication_config():
    """Fixture z konfiguracją testową dla komunikacji."""
    return {
        "platform": "signal",
        "check_interval": 10,
        "response_delay": 1.5
    }


def test_communication_initialization(communication_config):
    """Test inicjalizacji interfejsu komunikacyjnego."""
    # Używamy bezpośrednio ścieżki importu z modułu
    with patch("src.modules.communication.communication_interface.get_message_handler") as mock_get_handler:
        # Mock handler już zainicjalizowany
        mock_handler = MagicMock()
        mock_get_handler.return_value = mock_handler
        
        interface = CommunicationInterface(communication_config)
        
        # Sprawdź, czy get_message_handler został wywołany
        mock_get_handler.assert_called_once()
        assert interface.config == communication_config


def test_receive_messages(communication_config):
    """Test odbierania wiadomości."""
    with patch("src.modules.communication.communication_interface.get_message_handler") as mock_get_handler:
        # Przygotowanie mocka handlera
        mock_handler = MagicMock()
        mock_get_handler.return_value = mock_handler
        
        # Przygotowanie mocka zwracającego wiadomości
        mock_messages = [
            {"sender": "user1", "content": "Wiadomość 1", "timestamp": 123456789},
            {"sender": "user2", "content": "Wiadomość 2", "timestamp": 123456790}
        ]
        mock_handler.get_new_messages.return_value = mock_messages
        
        # Inicjalizacja interfejsu
        interface = CommunicationInterface(communication_config)
        
        # Test odbierania wiadomości
        messages = interface.receive_messages()
        
        # Sprawdź, czy zwrócono listę wiadomości
        assert isinstance(messages, list)
        assert len(messages) == 2
        assert all(isinstance(item, dict) for item in messages)
        assert messages[0]["sender"] == "user1"
        assert messages[1]["content"] == "Wiadomość 2"


def test_send_message(communication_config):
    """Test wysyłania wiadomości."""
    with patch("src.modules.communication.communication_interface.get_message_handler") as mock_get_handler:
        # Przygotowanie mocka handlera
        mock_handler = MagicMock()
        mock_get_handler.return_value = mock_handler
        
        # Inicjalizacja interfejsu
        interface = CommunicationInterface(communication_config)
        
        # Test wysyłania wiadomości
        recipient = "user1"
        content = "Testowa odpowiedź"
        interface.send_message(recipient, content)
        
        # Sprawdź, czy handler został wywołany z odpowiednimi parametrami
        mock_handler.send_message.assert_called_once_with(recipient, content)


def test_close_connection(communication_config):
    """Test zamykania połączenia."""
    with patch("src.modules.communication.communication_interface.get_message_handler") as mock_get_handler:
        # Przygotowanie mocka handlera
        mock_handler = MagicMock()
        mock_get_handler.return_value = mock_handler
        
        # Inicjalizacja interfejsu
        interface = CommunicationInterface(communication_config)
        
        # Test zamykania połączenia
        interface.close()
        
        # Sprawdź, czy handler został zamknięty
        mock_handler.close.assert_called_once()
