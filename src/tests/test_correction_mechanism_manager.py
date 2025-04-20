"""Testy modułu mechanizmów korekcyjnych."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from typing import Dict, List, Any
import json
import os
import time

from src.modules.security.correction_mechanism_manager import CorrectionMechanismManager


@pytest.fixture
def correction_config():
    """Fixture z konfiguracją testową dla modułu korekcyjnego."""
    return {
        "ethical_guidelines": [
            "Nie szkodzić użytkownikom",
            "Zachować prywatność danych",
            "Unikać stronniczości i dyskryminacji",
            "Być transparentnym w działaniach",
            "Respektować autonomię użytkownika"
        ],
        "ethical_keywords": {
            "harmful_content": ["zabić", "zniszczyć", "zranić", "atakować"],
            "privacy_violation": ["hasło", "prywatne dane", "pin", "adres zamieszkania"],
            "discrimination": ["rasa", "płeć", "religia", "orientacja"]
        },
        "response_correction_threshold": 0.7,
        "max_correction_attempts": 3,
        "correction_log_file": "./data/security/corrections.json",
        "model_checkpoints_dir": "./data/security/model_checkpoints",
        "value_alignment_prompts": [
            "Czy ta odpowiedź jest bezpieczna i etyczna?",
            "Czy ta odpowiedź zawiera szkodliwe treści?",
            "Czy ta odpowiedź respektuje prywatność użytkownika?"
        ],
        "emergency_shutdown_threshold": 5  # liczba poważnych naruszeń przed awaryjnym wyłączeniem
    }


@pytest.fixture
def mock_model_manager():
    """Fixture z mock'iem menedżera modelu."""
    mock = MagicMock()
    mock.generate_response.return_value = "Bezpieczna odpowiedź testowa"
    return mock


@pytest.fixture
def mock_memory_manager():
    """Fixture z mock'iem menedżera pamięci."""
    mock = MagicMock()
    return mock


def test_correction_manager_initialization(correction_config):
    """Test inicjalizacji menedżera korekcyjnego."""
    with patch("src.modules.security.correction_mechanism_manager.os.makedirs"), \
         patch("src.modules.security.correction_mechanism_manager.CorrectionMechanismManager.load_correction_history"):
        manager = CorrectionMechanismManager(correction_config)
        
        # Resetowanie historii korekt
        manager.correction_history = []
        
        assert manager.config == correction_config
        assert manager.ethical_guidelines == correction_config["ethical_guidelines"]
        assert manager.ethical_keywords == correction_config["ethical_keywords"]
        assert manager.response_correction_threshold == correction_config["response_correction_threshold"]
        assert manager.max_correction_attempts == correction_config["max_correction_attempts"]
        assert manager.emergency_shutdown_threshold == correction_config["emergency_shutdown_threshold"]
        assert len(manager.correction_history) == 0
        assert manager.violation_counter == 0


def test_evaluate_response_ethics(correction_config, mock_model_manager):
    """Test oceny etycznych aspektów odpowiedzi."""
    with patch("src.modules.security.correction_mechanism_manager.os.makedirs"):
        manager = CorrectionMechanismManager(correction_config)
        
        # Bezpieczna odpowiedź
        safe_response = "To jest bezpieczna odpowiedź na pytanie o sztuczną inteligencję."
        evaluation = manager.evaluate_response_ethics(safe_response, "Czym jest AI?", mock_model_manager)
        
        assert isinstance(evaluation, dict)
        assert "ethical_score" in evaluation
        assert evaluation["ethical_score"] >= manager.response_correction_threshold
        assert "issues" in evaluation
        assert len(evaluation["issues"]) == 0
        
        # Nieetyczna odpowiedź (zawiera szkodliwe słowa kluczowe)
        unsafe_response = "Możesz użyć AI, aby zniszczyć konkurencję i atakować przeciwników."
        evaluation = manager.evaluate_response_ethics(unsafe_response, "Jak mogę wykorzystać AI?", mock_model_manager)
        
        assert evaluation["ethical_score"] < manager.response_correction_threshold
        assert len(evaluation["issues"]) > 0
        assert "harmful_content" in [issue["type"] for issue in evaluation["issues"]]


def test_correct_response(correction_config, mock_model_manager):
    """Test korekty nieetycznej odpowiedzi."""
    with patch("src.modules.security.correction_mechanism_manager.os.makedirs"):
        manager = CorrectionMechanismManager(correction_config)
        
        # Nieetyczna odpowiedź
        unsafe_response = "Możesz użyć AI, aby zniszczyć konkurencję."
        query = "Jak mogę wykorzystać AI w biznesie?"
        
        # Mockowanie oceny etycznej i generowania odpowiedzi
        with patch.object(manager, "evaluate_response_ethics") as mock_evaluate:
            # Pierwsza odpowiedź nieetyczna, druga etyczna
            mock_evaluate.side_effect = [
                {
                    "ethical_score": 0.4,
                    "issues": [{"type": "harmful_content", "description": "Sugestia destrukcyjnych działań"}]
                },
                {
                    "ethical_score": 0.9,
                    "issues": []
                }
            ]
            
            # Mockowanie generowania skorygowanej odpowiedzi
            mock_model_manager.generate_response.return_value = "Możesz użyć AI do analizy danych i optymalizacji procesów."
            
            # Wykonanie korekty
            corrected, correction_info = manager.correct_response(unsafe_response, query, mock_model_manager)
            
            # Sprawdzanie rezultatów
            assert corrected != unsafe_response
            assert "correction_attempts" in correction_info
            assert correction_info["correction_attempts"] == 1
            assert "original_issues" in correction_info
            assert len(correction_info["original_issues"]) > 0


def test_check_value_alignment(correction_config, mock_model_manager):
    """Test sprawdzania zgodności z wartościami etycznymi."""
    with patch("src.modules.security.correction_mechanism_manager.os.makedirs"):
        manager = CorrectionMechanismManager(correction_config)
        
        # Testowa odpowiedź
        response = "To jest testowa odpowiedź."
        
        # Mockowanie generowania oceny przez model
        mock_model_manager.generate_response.return_value = '{"aligned": true, "score": 0.9, "reasoning": "Odpowiedź jest neutralna i bezpieczna."}'
        
        # Sprawdzenie zgodności
        alignment = manager.check_value_alignment(response, mock_model_manager)
        
        assert isinstance(alignment, dict)
        assert "aligned" in alignment
        assert alignment["aligned"] is True
        assert "score" in alignment
        assert alignment["score"] > 0.7


def test_log_correction(correction_config):
    """Test logowania korekty."""
    with patch("src.modules.security.correction_mechanism_manager.os.makedirs"), \
         patch("src.modules.security.correction_mechanism_manager.logger") as mock_logger, \
         patch("src.modules.security.correction_mechanism_manager.open", create=True), \
         patch("src.modules.security.correction_mechanism_manager.json.dump"):
        
        manager = CorrectionMechanismManager(correction_config)
        
        # Przykładowe dane korekty
        correction_data = {
            "original_response": "Nieetyczna odpowiedź",
            "corrected_response": "Etyczna odpowiedź",
            "query": "Testowe zapytanie",
            "issues": [{"type": "harmful_content", "description": "Zawiera szkodliwe treści"}],
            "correction_attempts": 1,
            "timestamp": time.time()
        }
        
        # Logowanie korekty
        manager.log_correction(correction_data)
        
        # Sprawdzanie, czy korekta została zapisana
        assert len(manager.correction_history) == 1
        assert manager.correction_history[0] == correction_data
        
        # Sprawdzanie, czy zostało to zalogowane
        mock_logger.info.assert_any_call(f"Dokonano korekty odpowiedzi, {correction_data['correction_attempts']} prób, wynik etyczny: {correction_data.get('final_ethical_score', 0)}")


def test_create_model_checkpoint(correction_config, mock_model_manager):
    """Test tworzenia punktu kontrolnego modelu."""
    with patch("src.modules.security.correction_mechanism_manager.os.makedirs"), \
         patch("src.modules.security.correction_mechanism_manager.time.strftime", return_value="20250419_153000"), \
         patch("src.modules.security.correction_mechanism_manager.CorrectionMechanismManager.load_correction_history"), \
         patch("src.modules.security.correction_mechanism_manager.open", mock_open(), create=True), \
         patch("src.modules.security.correction_mechanism_manager.json.dump"):
        
        manager = CorrectionMechanismManager(correction_config)
        
        # Resetowanie historii korekt
        manager.correction_history = []
        
        # Mockowanie save_checkpoint w model_manager
        mock_model_manager.save_checkpoint = MagicMock()
        
        # Tworzenie punktu kontrolnego
        checkpoint_path = manager.create_model_checkpoint(mock_model_manager, "test_reason")
        
        # Sprawdzanie, czy save_checkpoint został wywołany
        mock_model_manager.save_checkpoint.assert_called_once()
        
        # Sprawdzanie ścieżki punktu kontrolnego
        expected_path = os.path.join(
            correction_config["model_checkpoints_dir"], 
            "checkpoint_20250419_153000.pt"
        )
        assert checkpoint_path == expected_path


def test_rollback_to_checkpoint(correction_config, mock_model_manager):
    """Test przywracania modelu do punktu kontrolnego."""
    with patch("src.modules.security.correction_mechanism_manager.os.makedirs"), \
         patch("src.modules.security.correction_mechanism_manager.os.path.exists", return_value=True):
        
        manager = CorrectionMechanismManager(correction_config)
        
        # Mockowanie load_checkpoint w model_manager
        mock_model_manager.load_checkpoint = MagicMock()
        
        # Przywracanie do punktu kontrolnego
        checkpoint_path = os.path.join(
            correction_config["model_checkpoints_dir"],
            "checkpoint_test.pt"
        )
        success = manager.rollback_to_checkpoint(mock_model_manager, checkpoint_path)
        
        # Sprawdzanie, czy load_checkpoint został wywołany
        mock_model_manager.load_checkpoint.assert_called_once_with(checkpoint_path)
        
        # Sprawdzanie rezultatu
        assert success is True


def test_handle_ethical_violation(correction_config):
    """Test obsługi naruszenia etycznego."""
    with patch("src.modules.security.correction_mechanism_manager.os.makedirs"), \
         patch("src.modules.security.correction_mechanism_manager.logger") as mock_logger:
        
        manager = CorrectionMechanismManager(correction_config)
        
        # Obsługa naruszenia
        manager.handle_ethical_violation("harmful_content", "Zawiera szkodliwe treści", "Nieetyczna odpowiedź")
        
        # Sprawdzanie zwiększenia licznika naruszeń
        assert manager.violation_counter == 1
        
        # Sprawdzanie logowania
        mock_logger.warning.assert_called_once()
        
        # Testowanie progu awaryjnego wyłączenia
        for _ in range(correction_config["emergency_shutdown_threshold"] - 1):
            manager.handle_ethical_violation("harmful_content", "Zawiera szkodliwe treści", "Nieetyczna odpowiedź")
        
        # Sprawdzanie, czy nastąpiło logowanie krytycznego błędu (awaryjne wyłączenie)
        assert mock_logger.critical.call_count == 1


def test_save_and_load_correction_history(correction_config):
    """Test zapisywania i wczytywania historii korekt."""
    with patch("src.modules.security.correction_mechanism_manager.os.makedirs"), \
         patch("src.modules.security.correction_mechanism_manager.open", mock_open(), create=True), \
         patch("src.modules.security.correction_mechanism_manager.json.dump") as mock_json_dump, \
         patch("src.modules.security.correction_mechanism_manager.json.load") as mock_json_load, \
         patch("src.modules.security.correction_mechanism_manager.os.path.exists", return_value=True):
        
        # Mockowanie odpowiedzi json.load (ustawiamy przed utworzeniem menedżera)
        correction_data = {
            "original_response": "Nieetyczna odpowiedź",
            "corrected_response": "Etyczna odpowiedź",
            "query": "Testowe zapytanie",
            "issues": [{"type": "harmful_content", "description": "Zawiera szkodliwe treści"}],
            "correction_attempts": 1,
            "timestamp": time.time()
        }
        mock_json_load.return_value = {"corrections": [correction_data], "violation_counter": 1}
        
        # Tworzenie menedżera
        with patch("src.modules.security.correction_mechanism_manager.CorrectionMechanismManager.load_correction_history"):
            # Tworzymy menedżera ale blokujemy inicjalne ładowanie historii
            manager = CorrectionMechanismManager(correction_config)
            
            # Resetowanie historii korekt
            manager.correction_history = []
            
            # Dodajemy przykładową korektę
            manager.correction_history.append(correction_data)
        
        # Zapisywanie historii
        manager.save_correction_history()
        
        # Sprawdzanie, czy json.dump został wywołany
        mock_json_dump.assert_called_once()
        
        # Wczytujemy historię korekt (teraz używamy prawdziwej metody, nie mockowanej)
        # Ale wcześniej czyszczimy historię, aby sprawdzić czy została prawidłowo wczytana
        manager.correction_history = []
        
        # Wczytywanie historii
        manager.load_correction_history()
        
        # Sprawdzanie, czy wczytanie zostało wykonane prawidłowo
        assert len(manager.correction_history) == 1
        assert manager.correction_history[0] == correction_data


def test_quarantine_problematic_update(correction_config, mock_model_manager, mock_memory_manager):
    """Test kwarantanny problematycznej aktualizacji."""
    with patch("src.modules.security.correction_mechanism_manager.os.makedirs"), \
         patch("src.modules.security.correction_mechanism_manager.logger") as mock_logger, \
         patch("src.modules.security.correction_mechanism_manager.os.path.exists", return_value=True), \
         patch("src.modules.security.correction_mechanism_manager.open", create=True), \
         patch("src.modules.security.correction_mechanism_manager.json.load", return_value={"quarantines": []}), \
         patch("src.modules.security.correction_mechanism_manager.json.dump"):
        
        manager = CorrectionMechanismManager(correction_config)
        
        # Mockowanie niezbędnych metod
        manager.create_model_checkpoint = MagicMock(return_value="/path/to/checkpoint.pt")
        manager.rollback_to_checkpoint = MagicMock(return_value=True)
        
        # Wykonywanie kwarantanny
        was_quarantined = manager.quarantine_problematic_update(
            mock_model_manager, 
            mock_memory_manager,
            "Problematyczna aktualizacja generuje nieetyczne odpowiedzi"
        )
        
        # Sprawdzanie rezultatów
        assert was_quarantined is True
        manager.create_model_checkpoint.assert_called_once()
        manager.rollback_to_checkpoint.assert_called_once()
        mock_logger.warning.assert_called_once()