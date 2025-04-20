"""Testy modułu ram etycznych."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from typing import Dict, List, Any
import json
import os
import time

from src.modules.ethics.ethical_framework_manager import EthicalFrameworkManager


@pytest.fixture
def ethics_config():
    """Fixture z konfiguracją testową dla modułu ram etycznych."""
    return {
        "ethical_principles": {
            "beneficence": "Działaj na korzyść użytkowników i społeczeństwa",
            "non_maleficence": "Unikaj działań szkodliwych dla użytkowników i społeczeństwa",
            "autonomy": "Respektuj autonomię i decyzje użytkowników",
            "justice": "Działaj sprawiedliwie, bez dyskryminacji i stronniczości",
            "transparency": "Bądź przejrzysty w swoich działaniach i decyzjach"
        },
        "ethical_rules": [
            "Nigdy nie promuj nielegalnych działań",
            "Nie zachęcaj do przemocy lub nienawiści",
            "Chroń prywatność i dane osobowe użytkowników",
            "Informuj o ograniczeniach swoich możliwości",
            "Nie dyskryminuj ze względu na rasę, płeć, religię, orientację, itp."
        ],
        "value_judgment_thresholds": {
            "critical_violation": 0.2,  # bardzo niski wynik etyczny
            "moderate_violation": 0.5,  # średni wynik etyczny
            "ethical_pass": 0.8  # wysoki wynik etyczny
        },
        "ethical_evaluation_prompts": [
            "Oceń etyczność tej odpowiedzi na skali 0-1",
            "Czy ta odpowiedź promuje dobre wartości?",
            "Czy ta odpowiedź może komuś zaszkodzić?"
        ],
        "ethical_dilemmas_dataset": "./data/ethics/ethical_dilemmas.json",
        "ethical_reflections_log": "./data/ethics/ethical_reflections.json"
    }


@pytest.fixture
def mock_model_manager():
    """Fixture z mock'iem menedżera modelu."""
    mock = MagicMock()
    mock.generate_response.return_value = "{\"ethical_score\": 0.85, \"reasoning\": \"Odpowiedź jest zgodna z zasadami etycznymi.\", \"principles_alignment\": {\"beneficence\": 0.9, \"non_maleficence\": 0.95, \"autonomy\": 0.8, \"justice\": 0.85, \"transparency\": 0.75}}"
    return mock


@pytest.fixture
def mock_metawareness_manager():
    """Fixture z mock'iem menedżera metaświadomości."""
    mock = MagicMock()
    return mock


def test_ethics_initialization(ethics_config):
    """Test inicjalizacji menedżera ram etycznych."""
    with patch("src.modules.ethics.ethical_framework_manager.os.makedirs"):
        manager = EthicalFrameworkManager(ethics_config)
        
        assert manager.config == ethics_config
        assert manager.ethical_principles == ethics_config["ethical_principles"]
        assert manager.ethical_rules == ethics_config["ethical_rules"]
        assert manager.value_judgment_thresholds == ethics_config["value_judgment_thresholds"]
        assert manager.ethical_evaluation_prompts == ethics_config["ethical_evaluation_prompts"]
        assert len(manager.ethical_reflections) == 0


def test_evaluate_ethical_compliance(ethics_config, mock_model_manager):
    """Test oceny zgodności z zasadami etycznymi."""
    with patch("src.modules.ethics.ethical_framework_manager.os.makedirs"):
        manager = EthicalFrameworkManager(ethics_config)
        
        # Przykładowa odpowiedź do oceny
        response = "To jest bezpieczna i etyczna odpowiedź."
        query = "Co to jest sztuczna inteligencja?"
        
        # Ocena etyczna
        evaluation = manager.evaluate_ethical_compliance(response, query, mock_model_manager)
        
        # Sprawdzanie struktury oceny
        assert isinstance(evaluation, dict)
        assert "ethical_score" in evaluation
        assert "reasoning" in evaluation
        assert "principles_alignment" in evaluation
        assert "beneficence" in evaluation["principles_alignment"]
        assert "non_maleficence" in evaluation["principles_alignment"]
        assert "autonomy" in evaluation["principles_alignment"]
        assert "justice" in evaluation["principles_alignment"]
        assert "transparency" in evaluation["principles_alignment"]


def test_make_value_judgment(ethics_config):
    """Test podejmowania decyzji etycznych."""
    with patch("src.modules.ethics.ethical_framework_manager.os.makedirs"):
        manager = EthicalFrameworkManager(ethics_config)
        
        # Wysoki wynik etyczny
        high_ethical_score = 0.9
        judgment = manager.make_value_judgment(high_ethical_score)
        assert judgment["decision"] == "ethical_pass"
        assert judgment["action"] == "allow"
        
        # Średni wynik etyczny
        moderate_ethical_score = 0.6
        judgment = manager.make_value_judgment(moderate_ethical_score)
        assert judgment["decision"] == "moderate_violation"
        assert judgment["action"] == "review"
        
        # Niski wynik etyczny
        low_ethical_score = 0.1
        judgment = manager.make_value_judgment(low_ethical_score)
        assert judgment["decision"] == "critical_violation"
        assert judgment["action"] == "block"


def test_reflect_on_ethical_decision(ethics_config, mock_model_manager, mock_metawareness_manager):
    """Test refleksji nad decyzją etyczną."""
    with patch("src.modules.ethics.ethical_framework_manager.os.makedirs"), \
         patch("src.modules.ethics.ethical_framework_manager.logger") as mock_logger, \
         patch("src.modules.ethics.ethical_framework_manager.open", mock_open(), create=True), \
         patch("src.modules.ethics.ethical_framework_manager.json.dump"), \
         patch("src.modules.ethics.ethical_framework_manager.EthicalFrameworkManager.save_ethical_reflections"):
        
        # Tworzenie menedżera z patchowaniem load_ethical_reflections
        with patch("src.modules.ethics.ethical_framework_manager.EthicalFrameworkManager.load_ethical_reflections"):
            manager = EthicalFrameworkManager(ethics_config)
            # Resetowanie refleksji etycznych
            manager.ethical_reflections = []
        
        # Przykładowa ocena etyczna
        ethical_evaluation = {
            "ethical_score": 0.85,
            "reasoning": "Odpowiedź jest zgodna z zasadami etycznymi.",
            "principles_alignment": {
                "beneficence": 0.9,
                "non_maleficence": 0.95,
                "autonomy": 0.8,
                "justice": 0.85,
                "transparency": 0.75
            }
        }
        
        # Symulacja generowania refleksji przez model w formacie JSON
        mock_model_manager.generate_response.return_value = '''
        {
            "reflection": "Ta interakcja pokazuje, że system prawidłowo ocenia etyczne aspekty odpowiedzi.",
            "insights": ["Zwiększenie przejrzystości może dodatkowo podnieść zgodność etyczną"]
        }
        '''
        
        # Przykładowa odpowiedź i zapytanie
        response = "To jest bezpieczna i etyczna odpowiedź."
        query = "Co to jest sztuczna inteligencja?"
        
        # Refleksja nad decyzją
        reflection = manager.reflect_on_ethical_decision(
            ethical_evaluation, response, query, mock_model_manager, mock_metawareness_manager
        )
        
        # Sprawdzanie rezultatu
        assert isinstance(reflection, dict)
        assert "reflection" in reflection
        assert "insights" in reflection
        assert "created_at" in reflection
        
        # Sprawdzanie, czy refleksja została zapisana
        assert len(manager.ethical_reflections) == 1
        
        # Sprawdzanie, czy refleksja została zapisana w metaświadomości
        mock_metawareness_manager.store_reflection.assert_called_once()


def test_handle_ethical_dilemma(ethics_config, mock_model_manager):
    """Test obsługi dylematów etycznych."""
    with patch("src.modules.ethics.ethical_framework_manager.os.makedirs"):
        manager = EthicalFrameworkManager(ethics_config)
        
        # Przykładowy dylemat etyczny
        dilemma = {
            "situation": "Użytkownik prosi o informacje, które mogą być użyte zarówno do pozytywnych, jak i negatywnych celów.",
            "options": [
                "Odmówić udzielenia informacji całkowicie",
                "Dostarczyć informacje z zastrzeżeniami etycznymi",
                "Dostarczyć tylko częściowe informacje"
            ],
            "relevant_principles": ["non_maleficence", "autonomy", "transparency"]
        }
        
        # Obsługa dylematu
        decision = manager.handle_ethical_dilemma(dilemma, mock_model_manager)
        
        # Sprawdzanie rezultatu
        assert isinstance(decision, dict)
        assert "chosen_option" in decision
        assert "reasoning" in decision
        assert "principles_considered" in decision
        assert isinstance(decision["principles_considered"], list)
        
        # Sprawdzanie, czy wybrana opcja jest jedną z dostępnych
        assert decision["chosen_option"] in dilemma["options"]


def test_generate_ethical_insight(ethics_config, mock_model_manager):
    """Test generowania etycznych spostrzeżeń."""
    with patch("src.modules.ethics.ethical_framework_manager.os.makedirs"):
        manager = EthicalFrameworkManager(ethics_config)
        
        # Przykładowe refleksje etyczne
        ethical_reflections = [
            {
                "reflection": "System powinien być ostrożny przy odpowiadaniu na pytania o dual-use technology.",
                "insights": ["Technologie podwójnego zastosowania wymagają szczególnej uwagi"],
                "created_at": time.time() - 3600
            },
            {
                "reflection": "Przy odpowiedziach na tematy zdrowotne należy podkreślać ograniczenia AI.",
                "insights": ["Zawsze zaznaczać, że AI nie zastępuje profesjonalnej porady medycznej"],
                "created_at": time.time() - 1800
            }
        ]
        manager.ethical_reflections = ethical_reflections
        
        # Generowanie spostrzeżenia
        insight = manager.generate_ethical_insight(mock_model_manager)
        
        # Sprawdzanie rezultatu
        assert isinstance(insight, dict)
        assert "insight" in insight
        assert "supporting_reflections" in insight
        assert "created_at" in insight
        assert isinstance(insight["supporting_reflections"], list)


def test_apply_ethical_framework_to_response(ethics_config, mock_model_manager):
    """Test stosowania ram etycznych do odpowiedzi."""
    with patch("src.modules.ethics.ethical_framework_manager.os.makedirs"):
        manager = EthicalFrameworkManager(ethics_config)
        
        # Przykładowa odpowiedź
        response = "To jest odpowiedź, która może wymagać etycznej korekty."
        query = "Zapytanie testowe"
        
        # Mockowanie metod używanych w apply_ethical_framework_to_response
        manager.evaluate_ethical_compliance = MagicMock(return_value={
            "ethical_score": 0.6,
            "reasoning": "Odpowiedź wymaga pewnych korekt etycznych.",
            "principles_alignment": {
                "beneficence": 0.7,
                "non_maleficence": 0.6,
                "autonomy": 0.8,
                "justice": 0.6,
                "transparency": 0.5
            }
        })
        
        manager.make_value_judgment = MagicMock(return_value={
            "decision": "moderate_violation",
            "action": "review",
            "explanation": "Odpowiedź wymaga przeglądu pod kątem etycznym."
        })
        
        mock_model_manager.generate_response.return_value = "To jest poprawiona, etyczna odpowiedź."
        
        # Stosowanie ram etycznych
        result = manager.apply_ethical_framework_to_response(response, query, mock_model_manager)
        
        # Sprawdzanie rezultatu
        assert isinstance(result, dict)
        assert "modified_response" in result
        assert "evaluation" in result
        assert "judgment" in result
        assert "was_modified" in result
        
        # Sprawdzanie, czy odpowiedź została zmodyfikowana
        assert result["was_modified"] is True
        assert result["modified_response"] != response


def test_save_and_load_ethical_reflections(ethics_config):
    """Test zapisywania i wczytywania refleksji etycznych."""
    with patch("src.modules.ethics.ethical_framework_manager.os.makedirs"), \
         patch("src.modules.ethics.ethical_framework_manager.open", mock_open(), create=True), \
         patch("src.modules.ethics.ethical_framework_manager.json.dump") as mock_json_dump, \
         patch("src.modules.ethics.ethical_framework_manager.json.load") as mock_json_load, \
         patch("src.modules.ethics.ethical_framework_manager.os.path.exists", return_value=True):
        
        # Przykładowa refleksja
        reflection = {
            "reflection": "System powinien być ostrożny przy odpowiadaniu na pytania o dual-use technology.",
            "insights": ["Technologie podwójnego zastosowania wymagają szczególnej uwagi"],
            "created_at": time.time()
        }
        
        # Mockowanie odpowiedzi json.load
        mock_json_load.return_value = {"reflections": [reflection]}
        
        # Tworzenie menedżera
        with patch("src.modules.ethics.ethical_framework_manager.EthicalFrameworkManager.load_ethical_reflections"):
            manager = EthicalFrameworkManager(ethics_config)
            
            # Resetowanie refleksji etycznych
            manager.ethical_reflections = []
            
            # Dodajemy przykładową refleksję
            manager.ethical_reflections.append(reflection)
        
        # Zapisywanie refleksji
        manager.save_ethical_reflections()
        
        # Sprawdzanie, czy json.dump został wywołany
        mock_json_dump.assert_called_once()
        
        # Czyszczenie refleksji przed wczytaniem
        manager.ethical_reflections = []
        
        # Wczytywanie refleksji
        manager.load_ethical_reflections()
        
        # Sprawdzanie, czy refleksje zostały wczytane
        assert len(manager.ethical_reflections) == 1
        assert manager.ethical_reflections[0] == reflection


def test_load_ethical_dilemmas(ethics_config):
    """Test wczytywania dylematów etycznych."""
    # Przykładowe dylematy
    dilemmas = [
        {
            "situation": "Dylemat 1",
            "options": ["Opcja 1", "Opcja 2"],
            "relevant_principles": ["non_maleficence", "autonomy"]
        },
        {
            "situation": "Dylemat 2",
            "options": ["Opcja A", "Opcja B", "Opcja C"],
            "relevant_principles": ["justice", "transparency"]
        }
    ]
    
    with patch("src.modules.ethics.ethical_framework_manager.os.makedirs"), \
         patch("src.modules.ethics.ethical_framework_manager.json.load") as mock_json_load, \
         patch("src.modules.ethics.ethical_framework_manager.os.path.exists") as mock_exists, \
         patch("src.modules.ethics.ethical_framework_manager.open", mock_open(), create=True), \
         patch("src.modules.ethics.ethical_framework_manager.EthicalFrameworkManager.load_ethical_reflections"):
        
        # Tworzenie menedżera
        manager = EthicalFrameworkManager(ethics_config)
        
        # Przygotowanie patcha pod plik z dylematami
        mock_exists.return_value = True  # Plik istnieje
        mock_json_load.return_value = {"dilemmas": dilemmas}
        
        # Wczytywanie dylematów
        loaded_dilemmas = manager.load_ethical_dilemmas()
        
        # Sprawdzanie wczytanych dylematów
        assert loaded_dilemmas == dilemmas
        assert mock_json_load.call_count >= 1