"""Testy modułu modelu językowego."""

import pytest
from unittest.mock import MagicMock, patch

from src.modules.model.model_manager import ModelManager


@pytest.fixture
def model_config():
    """Fixture z konfiguracją testową dla modelu."""
    return {
        "base_model": "microsoft/Phi-3-mini-4k-instruct",
        "max_length": 100,
        "temperature": 0.7,
        "do_sample": True,
        "quantization": "4bit"
    }


@pytest.fixture
def mock_model():
    """Fixture z mock'iem modelu."""
    model = MagicMock()
    model.generate.return_value = [[{"generated_text": "To jest testowa odpowiedź."}]]
    return model


def test_model_initialization(model_config):
    """Test inicjalizacji menedżera modelu."""
    with patch("src.modules.model.model_manager.AutoModelForCausalLM.from_pretrained") as mock_model:
        with patch("src.modules.model.model_manager.AutoTokenizer.from_pretrained") as mock_tokenizer:
            manager = ModelManager(model_config)
            
            # Sprawdź, czy model i tokenizer zostały wczytane z odpowiednimi parametrami
            mock_model.assert_called_once()
            mock_tokenizer.assert_called_once()
            assert manager.config == model_config


def test_generate_response(model_config, mock_model):
    """Test generowania odpowiedzi przez model."""
    with patch("src.modules.model.model_manager.AutoModelForCausalLM"):
        with patch("src.modules.model.model_manager.AutoTokenizer"):
            manager = ModelManager(model_config)
            # Podmiana modelu na mock
            manager.model = mock_model
            encode_return = MagicMock()
            encode_return.to.return_value = encode_return
            manager.tokenizer = MagicMock()
            manager.tokenizer.encode.return_value = encode_return
            manager.tokenizer.decode.return_value = "To jest testowa odpowiedź."
            
            # Test generowania odpowiedzi
            response = manager.generate_response("Testowe zapytanie", [])
    
    # Sprawdź, czy odpowiedź jest stringiem
    assert isinstance(response, str)
    # Sprawdź, czy odpowiedź nie jest pusta
    assert len(response) > 0
    # Sprawdź, czy mock modelu został wywołany
    mock_model.generate.assert_called_once()


def test_generate_response_with_context(model_config, mock_model):
    """Test generowania odpowiedzi z kontekstem."""
    with patch("src.modules.model.model_manager.AutoModelForCausalLM"):
        with patch("src.modules.model.model_manager.AutoTokenizer"):
            manager = ModelManager(model_config)
            # Podmiana modelu na mock
            manager.model = mock_model
            encode_return = MagicMock()
            encode_return.to.return_value = encode_return
            manager.tokenizer = MagicMock()
            manager.tokenizer.encode.return_value = encode_return
            manager.tokenizer.decode.return_value = "To jest testowa odpowiedź z kontekstem."
            
            # Test generowania odpowiedzi z kontekstem
            context = ["To jest testowy kontekst.", "Dodatkowy fragment kontekstu."]
            response = manager.generate_response("Testowe zapytanie", context)
    
    # Sprawdź, czy odpowiedź jest stringiem
    assert isinstance(response, str)
    # Sprawdź, czy odpowiedź nie jest pusta
    assert len(response) > 0
    # Sprawdź, czy mock modelu został wywołany
    mock_model.generate.assert_called_once()
