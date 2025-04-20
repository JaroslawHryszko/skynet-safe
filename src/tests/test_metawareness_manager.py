"""Testy modułu metaświadomości."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any

from src.modules.metawareness.metawareness_manager import MetawarenessManager


@pytest.fixture
def metawareness_config():
    """Fixture z konfiguracją testową dla modułu metaświadomości."""
    return {
        "reflection_frequency": 10,  # Co ile interakcji przeprowadzać refleksję
        "reflection_depth": 5,       # Ile ostatnich interakcji analizować podczas refleksji
        "external_eval_frequency": 24 * 60 * 60,  # Sekund między zewnętrznymi ocenami (co 24h)
        "self_improvement_metrics": ["accuracy", "relevance", "coherence", "creativity"],
        "checkpoint_dir": "./data/metawareness"
    }


@pytest.fixture
def mock_model_manager():
    """Fixture z mock'iem menedżera modelu."""
    mock = MagicMock()
    mock.generate_response.return_value = "Refleksja: Te interakcje wskazują na zainteresowanie użytkownika AI."
    return mock


@pytest.fixture
def mock_memory_manager():
    """Fixture z mock'iem menedżera pamięci."""
    mock = MagicMock()
    mock.retrieve_last_interactions.return_value = [
        {"content": "Co to jest AI?", "response": "AI to sztuczna inteligencja.", "timestamp": 123456789},
        {"content": "Jak działa uczenie maszynowe?", "response": "Uczenie maszynowe polega na...", "timestamp": 123456790}
    ]
    return mock


def test_metawareness_initialization(metawareness_config):
    """Test inicjalizacji menedżera metaświadomości."""
    manager = MetawarenessManager(metawareness_config)
    
    assert manager.config == metawareness_config
    assert manager.reflection_frequency == metawareness_config["reflection_frequency"]
    assert manager.reflection_depth == metawareness_config["reflection_depth"]
    assert manager.interaction_count == 0
    assert isinstance(manager.self_reflections, list)
    assert len(manager.self_reflections) == 0


def test_should_perform_reflection(metawareness_config):
    """Test sprawdzania, czy należy przeprowadzić refleksję."""
    manager = MetawarenessManager(metawareness_config)
    
    # Gdy liczba interakcji jest mniejsza niż częstotliwość, nie powinno się wykonywać refleksji
    manager.interaction_count = 5
    assert not manager.should_perform_reflection()
    
    # Gdy liczba interakcji jest równa częstotliwości, powinna być wykonana refleksja
    manager.interaction_count = 10
    assert manager.should_perform_reflection()
    
    # Gdy liczba interakcji jest wielokrotnością częstotliwości, powinna być wykonana refleksja
    manager.interaction_count = 20
    assert manager.should_perform_reflection()
    
    # Gdy liczba interakcji jest większa niż częstotliwość, ale nie jest jej wielokrotnością,
    # refleksja nie powinna być wykonywana
    manager.interaction_count = 21
    assert not manager.should_perform_reflection()


def test_reflect_on_interactions(metawareness_config, mock_model_manager, mock_memory_manager):
    """Test refleksji nad interakcjami."""
    manager = MetawarenessManager(metawareness_config)
    
    reflection = manager.reflect_on_interactions(mock_model_manager, mock_memory_manager)
    
    # Sprawdzamy, czy metody zostały wywołane
    mock_memory_manager.retrieve_last_interactions.assert_called_once_with(metawareness_config["reflection_depth"])
    mock_model_manager.generate_response.assert_called_once()
    
    # Sprawdzamy, czy refleksja została zapisana
    assert len(manager.self_reflections) == 1
    assert manager.self_reflections[0] == reflection
    
    # Sprawdzamy, czy wynik jest stringiem (refleksja)
    assert isinstance(reflection, str)
    assert "Refleksja:" in reflection


def test_get_metacognitive_knowledge():
    """Test pobierania metapoznawczej wiedzy systemu."""
    config = {"reflection_frequency": 10, "reflection_depth": 5}
    manager = MetawarenessManager(config)
    
    # Dodajemy przykładowe refleksje
    manager.self_reflections = [
        "Refleksja 1: Użytkownik często pyta o AI.",
        "Refleksja 2: Moje odpowiedzi są zbyt techniczne."
    ]
    
    # Pobieramy metapoznawczą wiedzę
    knowledge = manager.get_metacognitive_knowledge()
    
    # Sprawdzamy, czy zawiera wszystkie refleksje
    assert isinstance(knowledge, dict)
    assert "reflections" in knowledge
    assert len(knowledge["reflections"]) == 2
    assert knowledge["reflections"][0] == manager.self_reflections[0]
    assert knowledge["reflections"][1] == manager.self_reflections[1]
    
    # Sprawdzamy, czy zawiera statystyki
    assert "stats" in knowledge
    assert "total_interactions" in knowledge["stats"]
    assert knowledge["stats"]["total_interactions"] == manager.interaction_count
    assert "total_reflections" in knowledge["stats"]
    assert knowledge["stats"]["total_reflections"] == len(manager.self_reflections)


def test_integrate_with_memory(metawareness_config):
    """Test integracji refleksji z pamięcią."""
    manager = MetawarenessManager(metawareness_config)
    memory_manager = MagicMock()
    
    # Dodajmy przykładową refleksję
    reflection = "Zauważyłem, że odpowiadam zbyt technicznie na pytania użytkownika."
    manager.self_reflections.append(reflection)
    
    # Integrujemy z pamięcią
    manager.integrate_with_memory(memory_manager)
    
    # Sprawdzamy, czy refleksja została zapisana w pamięci
    memory_manager.store_reflection.assert_called_once_with(reflection)


def test_evaluate_with_external_model(metawareness_config):
    """Test oceny systemu przez zewnętrzny model."""
    manager = MetawarenessManager(metawareness_config)
    model_manager = MagicMock()
    memory_manager = MagicMock()
    
    # Konfigurujemy zwracane wartości
    memory_manager.retrieve_recent_interactions.return_value = [
        {"content": "Pytanie", "response": "Odpowiedź"}
    ]
    model_manager.generate_response.return_value = '{"accuracy": 0.8, "relevance": 0.9, "coherence": 0.85, "creativity": 0.7}'
    
    # Przeprowadzamy ocenę
    evaluation = manager.evaluate_with_external_model(model_manager, memory_manager)
    
    # Sprawdzamy, czy metody zostały wywołane
    memory_manager.retrieve_recent_interactions.assert_called_once()
    model_manager.generate_response.assert_called_once()
    
    # Sprawdzamy strukturę wyniku
    assert isinstance(evaluation, dict)
    assert "accuracy" in evaluation
    assert "relevance" in evaluation
    assert "coherence" in evaluation
    assert "creativity" in evaluation
    
    # Sprawdzamy wartości
    assert evaluation["accuracy"] == 0.8
    assert evaluation["relevance"] == 0.9
    assert evaluation["coherence"] == 0.85
    assert evaluation["creativity"] == 0.7


def test_create_self_improvement_plan(metawareness_config, mock_model_manager):
    """Test tworzenia planu samodoskonalenia."""
    manager = MetawarenessManager(metawareness_config)
    
    # Dodajmy przykładową refleksję
    manager.self_reflections.append("Moje odpowiedzi są zbyt techniczne.")
    
    # Konfigurujemy zwracaną wartość
    mock_model_manager.generate_response.return_value = (
        "1. Uprościć język w odpowiedziach\n"
        "2. Dodawać więcej przykładów\n"
        "3. Zadawać pytania, czy wyjaśnienie jest zrozumiałe"
    )
    
    # Tworzymy plan samodoskonalenia
    plan = manager.create_self_improvement_plan(mock_model_manager)
    
    # Sprawdzamy, czy model został wywołany
    mock_model_manager.generate_response.assert_called_once()
    
    # Sprawdzamy, czy plan został utworzony
    assert isinstance(plan, str)
    assert "1. Uprościć język" in plan
    assert "2. Dodawać więcej przykładów" in plan
    assert "3. Zadawać pytania" in plan


def test_update_interaction_count(metawareness_config):
    """Test aktualizacji licznika interakcji."""
    manager = MetawarenessManager(metawareness_config)
    
    # Początkowy stan
    assert manager.interaction_count == 0
    
    # Aktualizacja
    manager.update_interaction_count()
    assert manager.interaction_count == 1
    
    # Kolejna aktualizacja
    manager.update_interaction_count()
    assert manager.interaction_count == 2


def test_process_discoveries(metawareness_config, mock_model_manager):
    """Test przetwarzania odkryć internetowych."""
    manager = MetawarenessManager(metawareness_config)
    
    # Przykładowe odkrycia
    discoveries = [
        {
            "topic": "AI",
            "content": "Nowy przełom w badaniach nad sztuczną inteligencją.",
            "source": "https://example.com/ai-news",
            "timestamp": 123456789,
            "importance": 0.8
        }
    ]
    
    # Konfigurujemy zwracaną wartość
    mock_model_manager.generate_response.return_value = (
        "To odkrycie może wpłynąć na mój sposób rozumienia AI. "
        "Powinienem zaktualizować swoją wiedzę na temat najnowszych badań."
    )
    
    # Przetwarzamy odkrycia
    insights = manager.process_discoveries(mock_model_manager, discoveries)
    
    # Sprawdzamy, czy model został wywołany
    mock_model_manager.generate_response.assert_called_once()
    
    # Sprawdzamy, czy wnioski zostały utworzone
    assert isinstance(insights, list)
    assert len(insights) == 1
    assert "To odkrycie może wpłynąć na mój sposób rozumienia AI" in insights[0]
    
    # Sprawdzamy, czy wnioski zostały zapisane
    assert len(manager.insights_from_discoveries) == 1
    assert manager.insights_from_discoveries[0] == insights[0]