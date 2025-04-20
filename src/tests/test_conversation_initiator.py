"""Testy modułu inicjowania konwersacji."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any
from datetime import datetime, timedelta

from src.modules.conversation_initiator.conversation_initiator import ConversationInitiator


@pytest.fixture
def initiator_config():
    """Fixture z konfiguracją testową dla modułu inicjowania konwersacji."""
    return {
        "min_time_between_initiations": 3600,  # sekundy
        "init_probability": 0.3,
        "topics_of_interest": ["AI", "metaświadomość", "uczenie maszynowe"],
        "max_daily_initiations": 5
    }


@pytest.fixture
def mock_discoveries():
    """Fixture z przykładowymi odkryciami."""
    return [
        {
            "topic": "AI",
            "content": "Nowy przełom w badaniach nad sztuczną inteligencją.",
            "source": "https://example.com/ai-news",
            "timestamp": datetime.now().timestamp() - 3600,
            "importance": 0.8
        },
        {
            "topic": "metaświadomość",
            "content": "Nowe teorie dotyczące metaświadomości w systemach AI.",
            "source": "https://example.com/metacognition",
            "timestamp": datetime.now().timestamp() - 7200,
            "importance": 0.9
        }
    ]


def test_initiator_initialization(initiator_config):
    """Test inicjalizacji inicjatora konwersacji."""
    initiator = ConversationInitiator(initiator_config)
    
    assert initiator.config == initiator_config
    assert initiator.min_time_between_initiations == initiator_config["min_time_between_initiations"]
    assert initiator.init_probability == initiator_config["init_probability"]
    assert initiator.topics_of_interest == initiator_config["topics_of_interest"]
    assert initiator.max_daily_initiations == initiator_config["max_daily_initiations"]
    assert initiator.initiated_conversations == []


def test_should_initiate_conversation(initiator_config):
    """Test sprawdzania, czy należy zainicjować konwersację."""
    initiator = ConversationInitiator(initiator_config)
    
    # Mockowanie czasu i generatora losowego
    with patch("src.modules.conversation_initiator.conversation_initiator.random.random") as mock_random, \
         patch("src.modules.conversation_initiator.conversation_initiator.datetime") as mock_datetime:
        
        # Przypadek 1: Prawdopodobieństwo poniżej progu, powinno zwrócić False
        mock_random.return_value = 0.4  # większe niż init_probability (0.3)
        result = initiator.should_initiate_conversation()
        assert result is False
        
        # Przypadek 2: Prawdopodobieństwo powyżej progu, ale zbyt wiele inicjalizacji dzisiaj
        mock_random.return_value = 0.2  # mniejsze niż init_probability (0.3)
        mock_datetime.now.return_value = datetime.now()
        
        # Symulacja zbyt wielu inicjalizacji
        today = datetime.now().date()
        initiator.initiated_conversations = [datetime.combine(today, datetime.min.time()) + timedelta(hours=i) for i in range(5)]
        
        result = initiator.should_initiate_conversation()
        assert result is False
        
        # Przypadek 3: Prawdopodobieństwo powyżej progu, dopuszczalna liczba inicjalizacji
        mock_random.return_value = 0.2  # mniejsze niż init_probability (0.3)
        initiator.initiated_conversations = [datetime.combine(today, datetime.min.time()) + timedelta(hours=i) for i in range(2)]
        
        result = initiator.should_initiate_conversation()
        assert result is True


def test_get_topic_for_initiation(initiator_config, mock_discoveries):
    """Test wyboru tematu do inicjacji konwersacji."""
    initiator = ConversationInitiator(initiator_config)
    
    # Przypadek 1: Dostępne odkrycia
    with patch("src.modules.conversation_initiator.conversation_initiator.random.choice") as mock_choice:
        mock_choice.return_value = mock_discoveries[0]
        
        topic = initiator.get_topic_for_initiation(mock_discoveries)
        assert topic is not None
        assert topic == mock_discoveries[0]
        
    # Przypadek 2: Brak odkryć, wybór z domyślnych tematów
    with patch("src.modules.conversation_initiator.conversation_initiator.random.choice") as mock_choice:
        mock_choice.return_value = "metaświadomość"
        
        topic = initiator.get_topic_for_initiation([])
        assert topic is not None
        assert topic == "metaświadomość"


def test_generate_initiation_message(initiator_config, mock_discoveries):
    """Test generowania wiadomości inicjującej."""
    initiator = ConversationInitiator(initiator_config)
    
    # Mockowanie model_manager
    model_manager = MagicMock()
    model_manager.generate_response.return_value = "Czy słyszałeś o nowym przełomie w AI?"
    
    # Przypadek 1: Na podstawie odkrycia
    message = initiator.generate_initiation_message(model_manager, mock_discoveries[0])
    
    assert message is not None
    assert isinstance(message, str)
    assert message == "Czy słyszałeś o nowym przełomie w AI?"
    
    # Sprawdzamy, czy model został wywołany z odpowiednimi parametrami
    model_manager.generate_response.assert_called_once()
    args, _ = model_manager.generate_response.call_args
    assert "AI" in args[0]  # temat powinien być zawarty w zapytaniu


def test_initiate_conversation(initiator_config, mock_discoveries):
    """Test pełnego procesu inicjowania konwersacji."""
    initiator = ConversationInitiator(initiator_config)
    
    # Mockowanie metod
    initiator.should_initiate_conversation = MagicMock(return_value=True)
    initiator.get_topic_for_initiation = MagicMock(return_value=mock_discoveries[0])
    initiator.generate_initiation_message = MagicMock(return_value="Czy słyszałeś o nowym przełomie w AI?")
    
    # Mockowanie zależności
    model_manager = MagicMock()
    communication_interface = MagicMock()
    recipients = ["user1", "user2"]
    
    # Wywołanie metody
    result = initiator.initiate_conversation(model_manager, communication_interface, mock_discoveries, recipients)
    
    # Sprawdzenie rezultatu
    assert result is True
    
    # Sprawdzenie wywołań metod
    initiator.should_initiate_conversation.assert_called_once()
    initiator.get_topic_for_initiation.assert_called_once_with(mock_discoveries)
    initiator.generate_initiation_message.assert_called_once_with(model_manager, mock_discoveries[0])
    
    # Komunikacja powinna zostać wywołana dla każdego odbiorcy
    assert communication_interface.send_message.call_count == len(recipients)
    
    # Sprawdzamy, czy nowa inicjalizacja została dodana do historii
    assert len(initiator.initiated_conversations) == 1
