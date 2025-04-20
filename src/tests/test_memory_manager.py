"""Testy modułu pamięci."""

import pytest
from unittest.mock import MagicMock, patch
import os
import shutil
from typing import Dict, List, Any
import numpy as np

from src.modules.memory.memory_manager import MemoryManager


@pytest.fixture
def memory_config():
    """Fixture z konfiguracją testową dla pamięci."""
    return {
        "vector_db_type": "chroma",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "memory_path": "./test_data/memory"
    }


@pytest.fixture
def setup_teardown_memory(memory_config):
    """Fixture do przygotowania i czyszczenia katalogów testowych."""
    # Przygotowanie - stwórz katalog jeśli nie istnieje
    os.makedirs(memory_config["memory_path"], exist_ok=True)
    
    yield
    
    # Czyszczenie po testach
    if os.path.exists(memory_config["memory_path"]):
        shutil.rmtree(memory_config["memory_path"])


def test_memory_initialization(memory_config, setup_teardown_memory):
    """Test inicjalizacji menedżera pamięci."""
    with patch("src.modules.memory.memory_manager.SentenceTransformer") as mock_transformer:
        with patch("src.modules.memory.memory_manager.chromadb.Client") as mock_chroma:
            manager = MemoryManager(memory_config)
            
            # Sprawdź, czy model embeddingu i baza wektorowa zostały wczytane
            mock_transformer.assert_called_once()
            mock_chroma.assert_called_once()
            assert manager.config == memory_config


def test_store_interaction(memory_config):
    """Test zapisywania interakcji w pamięci."""
    with patch("src.modules.memory.memory_manager.SentenceTransformer"):
        with patch("src.modules.memory.memory_manager.chromadb.Client") as mock_chroma:
            # Przygotowanie mocków dla kolekcji
            mock_interactions_collection = MagicMock()
            mock_reflections_collection = MagicMock()
            
            # Konfiguracja zwracanej wartości dla get_or_create_collection
            def get_or_create_collection_side_effect(name, **kwargs):
                if name == "interactions":
                    return mock_interactions_collection
                elif name == "reflections":
                    return mock_reflections_collection
                return MagicMock()
            
            mock_chroma.return_value.get_or_create_collection.side_effect = get_or_create_collection_side_effect
            
            manager = MemoryManager(memory_config)
            # Podmieniamy _embed_text na mock
            manager._embed_text = MagicMock(return_value=np.array([0.1, 0.2, 0.3]))
            
            # Test zapisywania interakcji
            message = {"sender": "user1", "content": "Testowa wiadomość", "timestamp": 123456789}
            manager.store_interaction(message)
            
            # Sprawdź, czy kolekcja interakcji została wywołana z odpowiednimi parametrami
            mock_interactions_collection.add.assert_called_once()
            
            # Sprawdź, czy przekazane metadane zawierają typ "user_message"
            call_args = mock_interactions_collection.add.call_args
            assert call_args[1]["metadatas"][0]["type"] == "user_message"


def test_store_response(memory_config):
    """Test zapisywania odpowiedzi systemu w pamięci."""
    with patch("src.modules.memory.memory_manager.SentenceTransformer"):
        with patch("src.modules.memory.memory_manager.chromadb.Client") as mock_chroma:
            # Przygotowanie mocków dla kolekcji
            mock_interactions_collection = MagicMock()
            mock_reflections_collection = MagicMock()
            
            # Konfiguracja zwracanej wartości dla get_or_create_collection
            def get_or_create_collection_side_effect(name, **kwargs):
                if name == "interactions":
                    return mock_interactions_collection
                elif name == "reflections":
                    return mock_reflections_collection
                return MagicMock()
            
            mock_chroma.return_value.get_or_create_collection.side_effect = get_or_create_collection_side_effect
            
            manager = MemoryManager(memory_config)
            # Podmieniamy _embed_text na mock
            manager._embed_text = MagicMock(return_value=np.array([0.1, 0.2, 0.3]))
            
            # Testowe dane
            original_message = {
                "sender": "user1", 
                "content": "Jak działa sztuczna inteligencja?", 
                "timestamp": 123456789
            }
            response = "Sztuczna inteligencja to dziedzina informatyki zajmująca się tworzeniem systemów zdolnych do wykonywania zadań wymagających ludzkiej inteligencji."
            
            # Testujemy nową metodę store_response
            manager.store_response(response, original_message)
            
            # Sprawdź, czy kolekcja interakcji została wywołana z odpowiednimi parametrami
            mock_interactions_collection.add.assert_called_once()
            
            # Pobierz argumenty wywołania metody add
            call_args = mock_interactions_collection.add.call_args
            
            # Sprawdź zawartość dokumentu i metadanych
            assert call_args[1]["documents"][0] == response
            assert call_args[1]["metadatas"][0]["type"] == "system_response"
            assert call_args[1]["metadatas"][0]["source"] == "system"
            assert call_args[1]["metadatas"][0]["in_response_to"] == original_message["content"]
            assert call_args[1]["metadatas"][0]["original_sender"] == original_message["sender"]
            assert call_args[1]["metadatas"][0]["original_timestamp"] == original_message["timestamp"]


def test_retrieve_relevant_context(memory_config):
    """Test pobierania kontekstu z pamięci."""
    with patch("src.modules.memory.memory_manager.SentenceTransformer"):
        with patch("src.modules.memory.memory_manager.chromadb.Client") as mock_chroma:
            # Przygotowanie mocków dla kolekcji
            mock_interactions_collection = MagicMock()
            mock_reflections_collection = MagicMock()
            
            # Konfiguracja zwracanej wartości dla get_or_create_collection
            def get_or_create_collection_side_effect(name, **kwargs):
                if name == "interactions":
                    return mock_interactions_collection
                elif name == "reflections":
                    return mock_reflections_collection
                return MagicMock()
            
            mock_chroma.return_value.get_or_create_collection.side_effect = get_or_create_collection_side_effect
            
            manager = MemoryManager(memory_config)
            # Podmieniamy _embed_text na mock
            manager._embed_text = MagicMock(return_value=np.array([0.1, 0.2, 0.3]))
            
            # Przygotowanie mocka zwracającego wyniki wyszukiwania dla interakcji
            mock_interactions_results = {
                "documents": [["Testowy dokument 1", "Testowy dokument 2"]],
                "metadatas": [[{"source": "user1"}, {"source": "user2"}]],
                "distances": [[0.1, 0.2]]
            }
            mock_interactions_collection.query.return_value = mock_interactions_results
            
            # Przygotowanie mocka zwracającego puste wyniki dla refleksji
            mock_reflections_results = {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }
            mock_reflections_collection.query.return_value = mock_reflections_results
            
            # Test pobierania kontekstu
            context = manager.retrieve_relevant_context("Testowe zapytanie")
            
            # Sprawdź, czy zwrócono listę stringów
            assert isinstance(context, list)
            # Sprawdź, czy kontekst zawiera odpowiednie dokumenty
            assert "Testowy dokument 1" in context
            assert "Testowy dokument 2" in context


def test_store_reflection(memory_config):
    """Test zapisywania refleksji w pamięci."""
    with patch("src.modules.memory.memory_manager.SentenceTransformer"):
        with patch("src.modules.memory.memory_manager.chromadb.Client") as mock_chroma:
            # Przygotowanie mocków dla kolekcji
            mock_interactions_collection = MagicMock()
            mock_reflections_collection = MagicMock()
            
            # Konfiguracja zwracanej wartości dla get_or_create_collection
            def get_or_create_collection_side_effect(name, **kwargs):
                if name == "interactions":
                    return mock_interactions_collection
                elif name == "reflections":
                    return mock_reflections_collection
                return MagicMock()
            
            mock_chroma.return_value.get_or_create_collection.side_effect = get_or_create_collection_side_effect
            
            manager = MemoryManager(memory_config)
            # Podmieniamy _embed_text na mock
            manager._embed_text = MagicMock(return_value=np.array([0.1, 0.2, 0.3]))
            
            # Test zapisywania refleksji
            reflection = "To jest testowa refleksja systemu."
            manager.store_reflection(reflection)
            
            # Sprawdź, czy kolekcja refleksji została wywołana z odpowiednimi parametrami
            mock_reflections_collection.add.assert_called_once()
            
            # Sprawdź, czy przekazano prawidłowe argumenty (dokument, embedding, metadata)
            args, kwargs = mock_reflections_collection.add.call_args
            assert len(kwargs.get('documents', [])) == 1
            assert kwargs.get('documents', [])[0] == reflection
            assert len(kwargs.get('embeddings', [])) == 1
            assert len(kwargs.get('metadatas', [])) == 1
            assert kwargs.get('metadatas', [])[0]['source'] == "system"
            assert kwargs.get('metadatas', [])[0]['type'] == "system_reflection"


def test_retrieve_last_interactions(memory_config):
    """Test pobierania ostatnich interakcji wraz z odpowiedziami."""
    with patch("src.modules.memory.memory_manager.SentenceTransformer"):
        with patch("src.modules.memory.memory_manager.chromadb.Client") as mock_chroma:
            # Przygotowanie mocków dla kolekcji
            mock_interactions_collection = MagicMock()
            mock_reflections_collection = MagicMock()
            
            # Konfiguracja zwracanej wartości dla get_or_create_collection
            def get_or_create_collection_side_effect(name, **kwargs):
                if name == "interactions":
                    return mock_interactions_collection
                elif name == "reflections":
                    return mock_reflections_collection
                return MagicMock()
            
            mock_chroma.return_value.get_or_create_collection.side_effect = get_or_create_collection_side_effect
            
            # Testowe zapytania i odpowiedzi - z dopasowaniem metadanych
            test_query1 = "Jak działa sztuczna inteligencja?"
            test_query2 = "Co to jest uczenie maszynowe?"
            test_query3 = "Wyjaśnij, co to jest transformer?"
            
            test_response1 = "Sztuczna inteligencja to systemy symulujące ludzką inteligencję."
            test_response2 = "Uczenie maszynowe to proces, w którym algorytmy uczą się na podstawie danych."
            
            # Przygotowanie mocka zwracającego wyniki z kolekcji interakcji, zawiera zarówno pytania jak i odpowiedzi
            mock_interactions_collection.get.return_value = {
                "ids": ["id1", "id2", "id3", "id4", "id5"],
                "documents": [test_query1, test_query2, test_query3, test_response1, test_response2],
                "metadatas": [
                    {"source": "user1", "timestamp": 123456789, "type": "user_message"},
                    {"source": "user2", "timestamp": 123456790, "type": "user_message"},
                    {"source": "user1", "timestamp": 123456791, "type": "user_message"},
                    {"source": "system", "timestamp": 123456792, "type": "system_response", 
                     "in_response_to": test_query1, "original_sender": "user1", "original_timestamp": 123456789},
                    {"source": "system", "timestamp": 123456793, "type": "system_response", 
                     "in_response_to": test_query2, "original_sender": "user2", "original_timestamp": 123456790}
                ]
            }
            
            manager = MemoryManager(memory_config)
            
            # Test pobierania ostatnich interakcji
            interactions = manager.retrieve_last_interactions(2)
            
            # Sprawdź, czy wywołano metodę get na kolekcji interakcji
            mock_interactions_collection.get.assert_called_once()
            
            # Sprawdź zwrócone dane
            assert len(interactions) == 2  # Ograniczenie do 2 najnowszych wiadomości użytkownika
            
            # Sprawdź sortowanie (od najnowszych wiadomości)
            assert interactions[0]["content"] == test_query3
            assert interactions[1]["content"] == test_query2
            
            # Sprawdź, czy odpowiedzi zostały prawidłowo dopasowane
            assert "response" in interactions[1]
            assert interactions[1]["response"] == test_response2
            
            # Trzecia wiadomość nie ma odpowiedzi
            assert "response" in interactions[0]
            assert interactions[0]["response"] == ""  # Brak odpowiedzi dla test_query3


def test_save_and_load_state(memory_config, setup_teardown_memory):
    """Test zapisywania i ładowania stanu pamięci."""
    with patch("src.modules.memory.memory_manager.SentenceTransformer") as mock_transformer:
        with patch("src.modules.memory.memory_manager.chromadb.Client") as mock_chroma:
            # Przygotowanie mocków dla kolekcji
            mock_interactions_collection = MagicMock()
            mock_reflections_collection = MagicMock()
            
            # Konfiguracja zwracanej wartości dla get_or_create_collection
            def get_or_create_collection_side_effect(name, **kwargs):
                if name == "interactions":
                    return mock_interactions_collection
                elif name == "reflections":
                    return mock_reflections_collection
                return MagicMock()
            
            mock_chroma.return_value.get_or_create_collection.side_effect = get_or_create_collection_side_effect
            
            manager = MemoryManager(memory_config)
            
            # Test zapisywania stanu
            manager.save_state()
            
            # Sprawdź, czy zapisano stan dla obu kolekcji
            mock_interactions_collection.persist.assert_called_once()
            mock_reflections_collection.persist.assert_called_once()