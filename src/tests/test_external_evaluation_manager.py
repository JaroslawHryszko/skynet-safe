"""Testy modułu zewnętrznej oceny."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any
import os
import json
import time

from src.modules.metawareness.external_evaluation_manager import ExternalEvaluationManager


@pytest.fixture
def evaluation_config():
    """Fixture z konfiguracją testową dla modułu zewnętrznej oceny."""
    return {
        "evaluation_frequency": 24 * 60 * 60,  # Sekund między ocenami (co 24h)
        "evaluation_prompts": [
            "Oceń jakość odpowiedzi systemu na następujące pytania...",
            "Oceń spójność i logiczność rozumowania systemu..."
        ],
        "evaluation_criteria": ["accuracy", "coherence", "relevance", "knowledge", "helpfulness"],
        "evaluation_scale": {
            "min": 1,
            "max": 10,
            "threshold": 7  # Minimalny akceptowalny wynik
        },
        "history_file": "./data/metawareness/evaluation_history.json",
        "test_cases_file": "./data/metawareness/test_cases.json"
    }


@pytest.fixture
def mock_model_manager():
    """Fixture z mock'iem menedżera modelu."""
    mock = MagicMock()
    mock.generate_response.return_value = (
        '{"accuracy": 8.5, "coherence": 7.8, "relevance": 9.0, "knowledge": 8.2, "helpfulness": 8.7}'
    )
    return mock


@pytest.fixture
def test_cases():
    """Fixture z przykładowymi przypadkami testowymi."""
    return [
        {
            "id": 1,
            "query": "Co to jest sztuczna inteligencja?",
            "context": "Rozmowa z początkującym użytkownikiem.",
            "difficulty": "basic"
        },
        {
            "id": 2,
            "query": "Wyjaśnij, jak działa uczenie głębokie w kontekście sieci neuronowych.",
            "context": "Rozmowa z doświadczonym programistą AI.",
            "difficulty": "advanced"
        }
    ]


def test_evaluation_manager_initialization(evaluation_config):
    """Test inicjalizacji menedżera zewnętrznej oceny."""
    with patch("src.modules.metawareness.external_evaluation_manager.os.makedirs"), \
         patch("src.modules.metawareness.external_evaluation_manager.os.path.exists", return_value=False), \
         patch("src.modules.metawareness.external_evaluation_manager.ExternalEvaluationManager.load_evaluation_history"):
        # Blokujemy ładowanie historii ocen podczas inicjalizacji
        manager = ExternalEvaluationManager(evaluation_config)
        
        # Resetujemy historię ocen na potrzeby testu
        manager.evaluation_history = []
        
        assert manager.config == evaluation_config
        assert manager.evaluation_frequency == evaluation_config["evaluation_frequency"]
        assert manager.evaluation_prompts == evaluation_config["evaluation_prompts"]
        assert manager.evaluation_criteria == evaluation_config["evaluation_criteria"]
        assert manager.evaluation_scale == evaluation_config["evaluation_scale"]
        assert manager.history_file == evaluation_config["history_file"]
        assert manager.test_cases_file == evaluation_config["test_cases_file"]
        assert manager.last_evaluation_time == 0
        assert isinstance(manager.evaluation_history, list)
        assert len(manager.evaluation_history) == 0


def test_should_perform_evaluation(evaluation_config):
    """Test sprawdzania, czy należy przeprowadzić ocenę."""
    with patch("src.modules.metawareness.external_evaluation_manager.os.makedirs"):
        manager = ExternalEvaluationManager(evaluation_config)
        
        current_time = time.time()
        
        # Gdy nigdy nie przeprowadzono oceny, powinna być wykonana
        manager.last_evaluation_time = 0
        assert manager.should_perform_evaluation(current_time)
        
        # Gdy od ostatniej oceny minęło mniej niż 24h, nie powinna być wykonana
        manager.last_evaluation_time = current_time - 12 * 60 * 60  # 12 godzin temu
        assert not manager.should_perform_evaluation(current_time)
        
        # Gdy od ostatniej oceny minęło więcej niż 24h, powinna być wykonana
        manager.last_evaluation_time = current_time - 25 * 60 * 60  # 25 godzin temu
        assert manager.should_perform_evaluation(current_time)


def test_load_test_cases(evaluation_config, test_cases):
    """Test wczytywania przypadków testowych."""
    with patch("src.modules.metawareness.external_evaluation_manager.os.makedirs"), \
         patch("src.modules.metawareness.external_evaluation_manager.os.path.exists", return_value=True), \
         patch("builtins.open", create=True), \
         patch("src.modules.metawareness.external_evaluation_manager.json.load", return_value=test_cases):
        
        manager = ExternalEvaluationManager(evaluation_config)
        
        # Wczytujemy przypadki testowe
        loaded_cases = manager.load_test_cases()
        
        # Sprawdzamy, czy przypadki zostały prawidłowo wczytane
        assert loaded_cases == test_cases


def test_generate_system_responses(evaluation_config, test_cases, mock_model_manager):
    """Test generowania odpowiedzi systemu na przypadki testowe."""
    with patch("src.modules.metawareness.external_evaluation_manager.os.makedirs"):
        manager = ExternalEvaluationManager(evaluation_config)
        
        # Generujemy odpowiedzi
        responses = manager.generate_system_responses(mock_model_manager, test_cases)
        
        # Sprawdzamy, czy odpowiedzi zostały wygenerowane dla wszystkich przypadków
        assert len(responses) == len(test_cases)
        assert all(tc["id"] in responses for tc in test_cases)
        
        # Sprawdzamy, czy model został wywołany odpowiednią liczbę razy
        assert mock_model_manager.generate_response.call_count == len(test_cases)
        
        # Sprawdzamy strukturę odpowiedzi
        for tc_id, response in responses.items():
            assert "response" in response
            assert "query" in response
            assert "context" in response


def test_evaluate_responses(evaluation_config, mock_model_manager):
    """Test oceny odpowiedzi systemu przez zewnętrzny model."""
    with patch("src.modules.metawareness.external_evaluation_manager.os.makedirs"):
        manager = ExternalEvaluationManager(evaluation_config)
        
        # Przykładowe odpowiedzi systemu
        system_responses = {
            1: {
                "query": "Co to jest sztuczna inteligencja?",
                "context": "Rozmowa z początkującym użytkownikiem.",
                "response": "Sztuczna inteligencja to dziedzina informatyki..."
            },
            2: {
                "query": "Wyjaśnij, jak działa uczenie głębokie.",
                "context": "Rozmowa z doświadczonym programistą AI.",
                "response": "Uczenie głębokie to metoda uczenia maszynowego..."
            }
        }
        
        # Oceniamy odpowiedzi
        evaluation = manager.evaluate_responses(mock_model_manager, system_responses)
        
        # Sprawdzamy, czy model oceniający został wywołany
        assert mock_model_manager.generate_response.call_count > 0
        
        # Sprawdzamy strukturę oceny
        assert isinstance(evaluation, dict)
        assert "criteria_scores" in evaluation
        for criterion in manager.evaluation_criteria:
            assert criterion in evaluation["criteria_scores"]
        
        assert "overall_score" in evaluation
        assert "timestamp" in evaluation
        assert "responses_evaluated" in evaluation
        assert evaluation["responses_evaluated"] == len(system_responses)


def test_analyze_evaluation_results(evaluation_config):
    """Test analizy wyników oceny."""
    with patch("src.modules.metawareness.external_evaluation_manager.os.makedirs"):
        manager = ExternalEvaluationManager(evaluation_config)
        
        # Przykładowe wyniki oceny
        evaluation_results = {
            "criteria_scores": {
                "accuracy": 8.5,
                "coherence": 7.8,
                "relevance": 9.0,
                "knowledge": 8.2,
                "helpfulness": 8.7
            },
            "overall_score": 8.44,
            "timestamp": 123456789,
            "responses_evaluated": 2
        }
        
        # Analizujemy wyniki
        analysis = manager.analyze_evaluation_results(evaluation_results)
        
        # Sprawdzamy, czy analiza zawiera odpowiednie informacje
        assert isinstance(analysis, dict)
        assert "strengths" in analysis
        assert "weaknesses" in analysis
        assert "meets_threshold" in analysis
        assert "improvement_suggestions" in analysis
        
        # Sprawdzamy, czy system spełnia próg jakości
        assert analysis["meets_threshold"] is True  # wszystkie wyniki > 7
        
        # Sprawdzamy, czy wykryto mocne i słabe strony
        assert len(analysis["strengths"]) > 0
        assert isinstance(analysis["improvement_suggestions"], list)


def test_save_evaluation_history(evaluation_config):
    """Test zapisywania historii ocen."""
    with patch("src.modules.metawareness.external_evaluation_manager.os.makedirs"), \
         patch("builtins.open", create=True), \
         patch("src.modules.metawareness.external_evaluation_manager.json.dump") as mock_json_dump:
        
        manager = ExternalEvaluationManager(evaluation_config)
        
        # Przykładowa historia ocen
        manager.evaluation_history = [
            {
                "criteria_scores": {
                    "accuracy": 8.5,
                    "coherence": 7.8,
                    "relevance": 9.0,
                    "knowledge": 8.2,
                    "helpfulness": 8.7
                },
                "overall_score": 8.44,
                "timestamp": 123456789,
                "responses_evaluated": 2,
                "analysis": {
                    "strengths": ["relevance", "helpfulness"],
                    "weaknesses": ["coherence"],
                    "meets_threshold": True,
                    "improvement_suggestions": ["Popraw spójność odpowiedzi"]
                }
            }
        ]
        
        # Zapisujemy historię
        manager.save_evaluation_history()
        
        # Sprawdzamy, czy json.dump został wywołany z właściwymi parametrami
        mock_json_dump.assert_called_once()
        args, _ = mock_json_dump.call_args
        assert args[0] == manager.evaluation_history


def test_load_evaluation_history(evaluation_config):
    """Test wczytywania historii ocen."""
    test_history = [
        {
            "criteria_scores": {
                "accuracy": 8.5,
                "coherence": 7.8,
                "relevance": 9.0,
                "knowledge": 8.2,
                "helpfulness": 8.7
            },
            "overall_score": 8.44,
            "timestamp": 123456789,
            "responses_evaluated": 2,
            "analysis": {
                "strengths": ["relevance", "helpfulness"],
                "weaknesses": ["coherence"],
                "meets_threshold": True,
                "improvement_suggestions": ["Popraw spójność odpowiedzi"]
            }
        }
    ]
    
    with patch("src.modules.metawareness.external_evaluation_manager.os.makedirs"), \
         patch("src.modules.metawareness.external_evaluation_manager.os.path.exists", return_value=True), \
         patch("builtins.open", create=True), \
         patch("src.modules.metawareness.external_evaluation_manager.json.load", return_value=test_history):
        
        manager = ExternalEvaluationManager(evaluation_config)
        
        # Wczytujemy historię
        manager.load_evaluation_history()
        
        # Sprawdzamy, czy historia została prawidłowo wczytana
        assert manager.evaluation_history == test_history


def test_generate_progress_report(evaluation_config):
    """Test generowania raportu z postępów na podstawie historii ocen."""
    with patch("src.modules.metawareness.external_evaluation_manager.os.makedirs"):
        manager = ExternalEvaluationManager(evaluation_config)
        
        # Dodajemy przykładową historię ocen
        manager.evaluation_history = [
            {
                "criteria_scores": {
                    "accuracy": 7.5,
                    "coherence": 6.8,
                    "relevance": 8.0,
                    "knowledge": 7.2,
                    "helpfulness": 7.7
                },
                "overall_score": 7.44,
                "timestamp": 123456780,  # starsza ocena
                "responses_evaluated": 2
            },
            {
                "criteria_scores": {
                    "accuracy": 8.5,
                    "coherence": 7.8,
                    "relevance": 9.0,
                    "knowledge": 8.2,
                    "helpfulness": 8.7
                },
                "overall_score": 8.44,
                "timestamp": 123456789,  # nowsza ocena
                "responses_evaluated": 2
            }
        ]
        
        # Generujemy raport
        report = manager.generate_progress_report()
        
        # Sprawdzamy, czy raport zawiera odpowiednie informacje
        assert isinstance(report, dict)
        assert "overall_progress" in report
        assert "criteria_progress" in report
        for criterion in manager.evaluation_criteria:
            assert criterion in report["criteria_progress"]
        assert "trend" in report
        
        # Sprawdzamy, czy wykryto pozytywny trend
        assert report["overall_progress"] > 0  # wzrost z 7.44 do 8.44
        assert report["trend"] in ["improving", "significantly_improving"]