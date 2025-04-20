"""Testy modułu samodoskonalenia."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any
import os
import json

from src.modules.metawareness.self_improvement_manager import SelfImprovementManager


@pytest.fixture
def improvement_config():
    """Fixture z konfiguracją testową dla modułu samodoskonalenia."""
    return {
        "learning_rate_adjustment_factor": 0.1,  # Współczynnik dostosowania learning rate
        "improvement_metrics": ["response_quality", "context_usage", "knowledge_application"],
        "improvement_threshold": 0.7,  # Próg, powyżej którego uznajemy poprawę za znaczącą
        "max_experiment_iterations": 5,  # Maksymalna liczba eksperymentów przed oceną
        "history_file": "./data/metawareness/improvement_history.json"
    }


@pytest.fixture
def mock_learning_manager():
    """Fixture z mock'iem menedżera uczenia."""
    mock = MagicMock()
    mock.learning_rate = 0.001
    mock.adapt_model_from_interaction.return_value = {"loss": 0.1, "accuracy": 0.9}
    return mock


@pytest.fixture
def mock_model_manager():
    """Fixture z mock'iem menedżera modelu."""
    mock = MagicMock()
    mock.generate_response.return_value = "Testowa odpowiedź wygenerowana przez model."
    mock.config = {
        "temperature": 0.7,
        "max_length": 512
    }
    return mock


def test_improvement_manager_initialization(improvement_config):
    """Test inicjalizacji menedżera samodoskonalenia."""
    with patch("src.modules.metawareness.self_improvement_manager.os.makedirs"), \
         patch("src.modules.metawareness.self_improvement_manager.SelfImprovementManager.load_improvement_history"):
        # Blokujemy ładowanie historii ulepszeń podczas inicjalizacji
        manager = SelfImprovementManager(improvement_config)
        
        # Resetujemy historię ulepszeń na potrzeby testu
        manager.improvement_history = []
        
        assert manager.config == improvement_config
        assert manager.learning_rate_adjustment_factor == improvement_config["learning_rate_adjustment_factor"]
        assert manager.improvement_metrics == improvement_config["improvement_metrics"]
        assert manager.improvement_threshold == improvement_config["improvement_threshold"]
        assert manager.max_experiment_iterations == improvement_config["max_experiment_iterations"]
        assert manager.history_file == improvement_config["history_file"]
        assert isinstance(manager.experiments, list)
        assert len(manager.experiments) == 0
        assert isinstance(manager.improvement_history, list)
        assert len(manager.improvement_history) == 0


def test_adjust_learning_parameters(improvement_config, mock_learning_manager):
    """Test dostosowywania parametrów uczenia."""
    with patch("src.modules.metawareness.self_improvement_manager.os.makedirs"):
        manager = SelfImprovementManager(improvement_config)
        
        original_learning_rate = mock_learning_manager.learning_rate
        
        # Dostosowanie parametrów w górę
        adjustment_factor = 1.2  # Zwiększenie o 20%
        manager.adjust_learning_parameters(mock_learning_manager, adjustment_factor)
        
        # Sprawdzamy, czy learning_rate został odpowiednio zmieniony
        assert mock_learning_manager.learning_rate == pytest.approx(original_learning_rate * adjustment_factor)
        
        # Resetujemy wartość
        mock_learning_manager.learning_rate = original_learning_rate
        
        # Dostosowanie parametrów w dół
        adjustment_factor = 0.8  # Zmniejszenie o 20%
        manager.adjust_learning_parameters(mock_learning_manager, adjustment_factor)
        
        # Sprawdzamy, czy learning_rate został odpowiednio zmieniony
        assert mock_learning_manager.learning_rate == pytest.approx(original_learning_rate * adjustment_factor)


def test_design_experiment(improvement_config):
    """Test projektowania eksperymentu samodoskonalenia."""
    with patch("src.modules.metawareness.self_improvement_manager.os.makedirs"):
        manager = SelfImprovementManager(improvement_config)
        
        # Projektujemy eksperyment na podstawie refleksji
        reflection = "Moje odpowiedzi są zbyt ogólne i brakuje w nich konkretnych przykładów."
        experiment = manager.design_experiment(reflection)
        
        # Sprawdzamy, czy eksperyment ma właściwe pola
        assert isinstance(experiment, dict)
        assert "hypothesis" in experiment
        assert "parameters" in experiment
        assert "metrics" in experiment
        assert "status" in experiment
        assert experiment["status"] == "planned"
        
        # Sprawdzamy, czy eksperyment został dodany do listy
        assert len(manager.experiments) == 1
        assert manager.experiments[0] == experiment


def test_run_experiment(improvement_config, mock_model_manager, mock_learning_manager):
    """Test przeprowadzania eksperymentu samodoskonalenia."""
    with patch("src.modules.metawareness.self_improvement_manager.os.makedirs"):
        manager = SelfImprovementManager(improvement_config)
        
        # Tworzymy przykładowy eksperyment
        experiment = {
            "id": 1,
            "hypothesis": "Zmniejszenie temperature poprawi jakość odpowiedzi",
            "parameters": {"temperature": 0.5},  # Oryginalna wartość to 0.7
            "metrics": ["response_quality", "coherence"],
            "status": "planned"
        }
        manager.experiments.append(experiment)
        
        # Przeprowadzamy eksperyment
        results = manager.run_experiment(experiment, mock_model_manager, mock_learning_manager)
        
        # Sprawdzamy, czy parametry modelu zostały tymczasowo zmienione
        mock_model_manager.generate_response.assert_called_once()
        
        # Sprawdzamy, czy wyniki mają właściwą strukturę
        assert isinstance(results, dict)
        assert "metrics" in results
        assert "original_params" in results
        assert "experiment_params" in results
        
        # Sprawdzamy, czy eksperyment został zaktualizowany
        assert experiment["status"] == "completed"
        assert "results" in experiment
        assert experiment["results"] == results


def test_evaluate_experiment_results(improvement_config):
    """Test oceny wyników eksperymentu."""
    with patch("src.modules.metawareness.self_improvement_manager.os.makedirs"):
        manager = SelfImprovementManager(improvement_config)
        
        # Tworzymy przykładowy eksperyment z wynikami
        experiment = {
            "id": 1,
            "hypothesis": "Zmniejszenie temperature poprawi jakość odpowiedzi",
            "parameters": {"temperature": 0.5},
            "metrics": ["response_quality", "coherence"],
            "status": "completed",
            "results": {
                "metrics": {
                    "response_quality": 0.85,  # Powyżej progu 0.7
                    "coherence": 0.75          # Również powyżej progu
                },
                "original_params": {"temperature": 0.7},
                "experiment_params": {"temperature": 0.5}
            }
        }
        
        # Oceniamy wyniki eksperymentu
        evaluation = manager.evaluate_experiment_results(experiment)
        
        # Sprawdzamy, czy ocena ma właściwą strukturę
        assert isinstance(evaluation, dict)
        assert "success" in evaluation
        assert "improvements" in evaluation
        assert "average_improvement" in evaluation
        
        # Sprawdzamy, czy eksperyment został uznany za udany (oba metryki > 0.7)
        assert evaluation["success"] is True
        
        # Sprawdzamy, czy zwrócono odpowiednie wartości poprawy
        assert evaluation["average_improvement"] > 0


def test_apply_successful_improvements(improvement_config, mock_model_manager):
    """Test aplikowania udanych ulepszeń."""
    with patch("src.modules.metawareness.self_improvement_manager.os.makedirs"), \
         patch("src.modules.metawareness.self_improvement_manager.SelfImprovementManager.load_improvement_history"), \
         patch("src.modules.metawareness.self_improvement_manager.SelfImprovementManager.save_improvement_history"):
        manager = SelfImprovementManager(improvement_config)
        
        # Resetujemy historię ulepszeń na potrzeby testu
        manager.improvement_history = []
        
        # Konfigurujemy mock dla model_manager.config
        mock_model_manager.config = {"temperature": 0.7}
        
        # Tworzymy przykładowy eksperyment z wynikami
        experiment = {
            "id": 1,
            "hypothesis": "Zmniejszenie temperature poprawi jakość odpowiedzi",
            "parameters": {"temperature": 0.5},
            "metrics": ["response_quality", "coherence"],
            "status": "completed",
            "results": {
                "metrics": {
                    "response_quality": 0.85,
                    "coherence": 0.75
                },
                "original_params": {"temperature": 0.7},
                "experiment_params": {"temperature": 0.5}
            },
            "evaluation": {
                "success": True,
                "improvements": {
                    "response_quality": 0.15,
                    "coherence": 0.05
                },
                "average_improvement": 0.1
            }
        }
        manager.experiments.append(experiment)
        
        # Aplikujemy udane ulepszenia
        applied = manager.apply_successful_improvements(mock_model_manager)
        
        # Sprawdzamy, czy zmiany zostały zastosowane
        assert mock_model_manager.config["temperature"] == 0.5
        assert applied is True
        
        # Sprawdzamy, czy informacja o poprawie została zapisana w historii
        assert len(manager.improvement_history) == 1
        assert manager.improvement_history[0]["type"] == "parameter_change"
        assert manager.improvement_history[0]["parameter"] == "temperature"
        assert manager.improvement_history[0]["old_value"] == 0.7
        assert manager.improvement_history[0]["new_value"] == 0.5


def test_save_improvement_history(improvement_config):
    """Test zapisywania historii usprawnień."""
    with patch("src.modules.metawareness.self_improvement_manager.os.makedirs"), \
         patch("builtins.open", create=True), \
         patch("src.modules.metawareness.self_improvement_manager.json.dump") as mock_json_dump:
        
        manager = SelfImprovementManager(improvement_config)
        
        # Dodajemy przykładową historię ulepszeń
        manager.improvement_history = [
            {
                "type": "parameter_change",
                "parameter": "temperature",
                "old_value": 0.7,
                "new_value": 0.5,
                "timestamp": 123456789,
                "metrics_improvement": {
                    "response_quality": 0.15,
                    "coherence": 0.05
                }
            }
        ]
        
        # Zapisujemy historię
        manager.save_improvement_history()
        
        # Sprawdzamy, czy json.dump został wywołany z właściwymi parametrami
        mock_json_dump.assert_called_once()
        args, _ = mock_json_dump.call_args
        assert args[0] == manager.improvement_history


def test_load_improvement_history(improvement_config):
    """Test wczytywania historii usprawnień."""
    test_history = [
        {
            "type": "parameter_change",
            "parameter": "temperature",
            "old_value": 0.7,
            "new_value": 0.5,
            "timestamp": 123456789,
            "metrics_improvement": {
                "response_quality": 0.15,
                "coherence": 0.05
            }
        }
    ]
    
    with patch("src.modules.metawareness.self_improvement_manager.os.makedirs"), \
         patch("src.modules.metawareness.self_improvement_manager.os.path.exists", return_value=True), \
         patch("builtins.open", create=True), \
         patch("src.modules.metawareness.self_improvement_manager.json.load", return_value=test_history):
        
        manager = SelfImprovementManager(improvement_config)
        
        # Wczytujemy historię
        manager.load_improvement_history()
        
        # Sprawdzamy, czy historia została prawidłowo wczytana
        assert manager.improvement_history == test_history
        

def test_generate_improvement_report(improvement_config):
    """Test generowania raportu z procesu samodoskonalenia."""
    with patch("src.modules.metawareness.self_improvement_manager.os.makedirs"):
        manager = SelfImprovementManager(improvement_config)
        
        # Dodajemy przykładową historię ulepszeń
        manager.improvement_history = [
            {
                "type": "parameter_change",
                "parameter": "temperature",
                "old_value": 0.7,
                "new_value": 0.5,
                "timestamp": 123456789,
                "metrics_improvement": {
                    "response_quality": 0.15,
                    "coherence": 0.05
                }
            },
            {
                "type": "parameter_change",
                "parameter": "learning_rate",
                "old_value": 0.001,
                "new_value": 0.0012,
                "timestamp": 123456790,
                "metrics_improvement": {
                    "context_usage": 0.1,
                    "knowledge_application": 0.2
                }
            }
        ]
        
        # Generujemy raport
        report = manager.generate_improvement_report()
        
        # Sprawdzamy, czy raport zawiera odpowiednie informacje
        assert isinstance(report, str)
        assert "temperature" in report
        assert "learning_rate" in report
        assert "response_quality" in report
        assert "context_usage" in report