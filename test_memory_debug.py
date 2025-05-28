#!/usr/bin/env python3
"""Test debug pamięci długoterminowej."""

import os
import sys
import logging
import time
from datetime import datetime

# Dodaj ścieżkę do modułów systemu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.modules.memory.memory_manager import MemoryManager
from src.modules.model.model_manager import ModelManager
from src.config import config

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("MEMORY_DEBUG")

def test_memory_conversation_context():
    """Test pamięci długoterminowej w kontekście konwersacji."""
    
    logger.info("=== ROZPOCZĘCIE TESTU PAMIĘCI DŁUGOTERMINOWEJ ===")
    
    # Inicjalizacja managera pamięci
    memory_config = config.MEMORY
    memory = MemoryManager(memory_config)
    
    # Symulacja konwersacji
    conversation = [
        {"sender": "user", "content": "Jak masz na imię?", "timestamp": time.time()},
        {"sender": "user", "content": "Jakie są twoje hobby?", "timestamp": time.time() + 10},
        {"sender": "user", "content": "Opowiedz mi o sztucznej inteligencji", "timestamp": time.time() + 20},
        {"sender": "user", "content": "Czy pamiętasz jak mam na imię?", "timestamp": time.time() + 30}
    ]
    
    # Symulowane odpowiedzi systemu
    responses = [
        "Nazywam się Lira, jestem asystentem AI.",
        "Interesuje mnie uczenie maszynowe i technologie AI.",
        "Sztuczna inteligencja to fascynujące pole nauki o maszynach myślących.",
        "Przepraszam, nie pamiętam Twojego imienia. Jak masz na imię?"
    ]
    
    # Przechowywanie interakcji w pamięci
    logger.info("--- Zapisywanie interakcji do pamięci ---")
    for i, message in enumerate(conversation):
        # Zapisz wiadomość użytkownika
        memory.store_interaction(message)
        logger.info(f"Zapisano wiadomość: {message['content']}")
        
        # Zapisz odpowiedź systemu
        memory.store_response(responses[i], message)
        logger.info(f"Zapisano odpowiedź: {responses[i]}")
    
    # Test pobierania kontekstu
    logger.info("--- Testowanie pobierania kontekstu ---")
    
    # Test 1: Kontekst dla pytania o imię
    test_queries = [
        "Jak mam na imię?",
        "Jakie masz hobby?",
        "Co to jest AI?",
        "Czy pamiętasz naszą wcześniejszą rozmowę?"
    ]
    
    for query in test_queries:
        logger.info(f"\nTest dla zapytania: {query}")
        context = memory.retrieve_relevant_context(query, n_results=3)
        
        if context:
            logger.info(f"Znaleziono {len(context)} elementów kontekstu:")
            for j, ctx_item in enumerate(context, 1):
                logger.info(f"  {j}. {ctx_item[:100]}...")
        else:
            logger.warning("Brak kontekstu dla tego zapytania!")
    
    # Test ostatnich interakcji
    logger.info("\n--- Test ostatnich interakcji ---")
    recent_interactions = memory.retrieve_last_interactions(n=3)
    
    if recent_interactions:
        logger.info(f"Znaleziono {len(recent_interactions)} ostatnich interakcji:")
        for interaction in recent_interactions:
            logger.info(f"Zapytanie: {interaction['content']}")
            logger.info(f"Odpowiedź: {interaction.get('response', 'Brak odpowiedzi')}")
    else:
        logger.warning("Brak ostatnich interakcji!")
    
    # Test zapisywania stanu
    logger.info("\n--- Test zapisywania stanu pamięci ---")
    memory.save_state()
    logger.info("Stan pamięci zapisany")
    
    logger.info("=== KONIEC TESTU PAMIĘCI DŁUGOTERMINOWEJ ===")

if __name__ == "__main__":
    test_memory_conversation_context()