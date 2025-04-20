"""Testy modułu uczenia."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any

from src.modules.learning.learning_manager import LearningManager


@pytest.fixture
def learning_config():
    """Fixture z konfiguracją testową dla modułu uczenia."""
    return {
        "learning_rate": 0.001,
        "batch_size": 4,
        "epochs": 1,
        "checkpoint_dir": "./data/checkpoints",
        "evaluation_interval": 10
    }


@pytest.fixture
def mock_model_manager():
    """Fixture z mock'iem menedżera modelu."""
    mock = MagicMock()
    
    # Mockowanie metod potrzebnych do uczenia
    mock.model = MagicMock()
    mock.tokenizer = MagicMock()
    mock.config = {
        "base_model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "max_length": 512,
        "temperature": 0.7,
    }
    
    return mock


def test_learning_manager_initialization(learning_config):
    """Test inicjalizacji menedżera uczenia."""
    with patch("src.modules.learning.learning_manager.os.makedirs"):
        manager = LearningManager(learning_config)
        
        assert manager.config == learning_config
        assert manager.learning_rate == learning_config["learning_rate"]
        assert manager.batch_size == learning_config["batch_size"]
        assert manager.epochs == learning_config["epochs"]


def test_prepare_training_data():
    """Test przygotowania danych treningowych."""
    config = {"batch_size": 4}
    with patch("src.modules.learning.learning_manager.os.makedirs"):
        manager = LearningManager(config)
        
        # Testowe dane
        interactions = [
            {"content": "Pytanie 1", "response": "Odpowiedź 1"},
            {"content": "Pytanie 2", "response": "Odpowiedź 2"},
            {"content": "Pytanie 3", "response": "Odpowiedź 3"},
            {"content": "Pytanie 4", "response": "Odpowiedź 4"},
            {"content": "Pytanie 5", "response": "Odpowiedź 5"}
        ]
        
        # Podmieniamy metodę przetwarzania
        manager._process_interaction = MagicMock(side_effect=lambda x: (f"przetworzono: {x['content']}", f"przetworzono: {x['response']}"))
        
        training_data = manager.prepare_training_data(interactions)
        
        # Sprawdzamy, czy dane są w odpowiednim formacie
        assert isinstance(training_data, list)
        assert len(training_data) == 5
        assert all(isinstance(item, tuple) and len(item) == 2 for item in training_data)
        assert all(isinstance(item[0], str) and isinstance(item[1], str) for item in training_data)
        
        # Sprawdzamy, czy przetwarzanie zostało wywołane dla każdej interakcji
        assert manager._process_interaction.call_count == 5


def test_train_model(learning_config, mock_model_manager):
    """Test trenowania modelu."""
    with patch("src.modules.learning.learning_manager.os.makedirs"):
        manager = LearningManager(learning_config)
        
        # Mockujemy metodę treningową
        manager._run_training_steps = MagicMock()
        manager._save_checkpoint = MagicMock()
        manager._evaluate_model = MagicMock(return_value={"loss": 0.1, "accuracy": 0.9})
        
        # Przykładowe dane treningowe
        training_data = [
            ("przetworzono: Pytanie 1", "przetworzono: Odpowiedź 1"),
            ("przetworzono: Pytanie 2", "przetworzono: Odpowiedź 2"),
        ]
        
        # Trenowanie modelu
        result = manager.train_model(mock_model_manager, training_data)
        
        # Sprawdzamy, czy metody zostały wywołane
        manager._run_training_steps.assert_called_once()
        manager._save_checkpoint.assert_called_once()
        manager._evaluate_model.assert_called_once()
        
        # Sprawdzamy wynik
        assert isinstance(result, dict)
        assert "loss" in result
        assert "accuracy" in result


def test_adapt_model_from_interaction(learning_config, mock_model_manager):
    """Test dostosowywania modelu na podstawie pojedynczej interakcji."""
    with patch("src.modules.learning.learning_manager.os.makedirs"):
        manager = LearningManager(learning_config)
        
        # Mockujemy metody
        manager.prepare_training_data = MagicMock(return_value=[("", "")])
        manager.train_model = MagicMock(return_value={"loss": 0.1, "accuracy": 0.9})
        
        # Testowa interakcja
        interaction = {"content": "Pytanie", "response": "Odpowiedź"}
        
        # Adaptacja modelu
        result = manager.adapt_model_from_interaction(mock_model_manager, interaction)
        
        # Sprawdzamy wywołania metod
        manager.prepare_training_data.assert_called_once_with([interaction])
        manager.train_model.assert_called_once()
        
        # Sprawdzamy wynik
        assert isinstance(result, dict)
        assert "loss" in result
        assert "accuracy" in result
