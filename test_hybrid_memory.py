#!/usr/bin/env python3
"""Kompleksowy test hybrydowej pamięci długoterminowej."""

import os
import sys
import logging
import time
from datetime import datetime

# Dodaj ścieżkę do modułów systemu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.modules.memory.memory_manager import MemoryManager
from src.config import config

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("HYBRID_MEMORY_TEST")

def test_hybrid_memory_system():
    """Test kompleksowy hybrydowej pamięci."""
    
    logger.info("=== ROZPOCZĘCIE TESTU HYBRYDOWEJ PAMIĘCI ===")
    
    # Inicjalizacja managera pamięci
    memory_config = config.MEMORY
    logger.info(f"Konfiguracja pamięci: {memory_config}")
    memory = MemoryManager(memory_config)
    
    # === TEST 1: Podstawowe przechowywanie i pobieranie ===
    logger.info("--- TEST 1: Podstawowe przechowywanie i pobieranie ---")
    
    # Symulacja konwersacji z ciągłością tematyczną
    conversation_flow = [
        {"sender": "user", "content": "Cześć! Jak masz na imię?", "timestamp": time.time()},
        {"sender": "user", "content": "Możesz mi opowiedzieć o swoich hobby?", "timestamp": time.time() + 10},
        {"sender": "user", "content": "Jakie książki lubisz czytać?", "timestamp": time.time() + 20},
        {"sender": "user", "content": "Co myślisz o sztucznej inteligencji?", "timestamp": time.time() + 30},
        {"sender": "user", "content": "Pamiętasz jak mam na imię?", "timestamp": time.time() + 40},
        {"sender": "user", "content": "O czym rozmawialiśmy wcześniej?", "timestamp": time.time() + 50}
    ]
    
    # Symulowane odpowiedzi systemu
    system_responses = [
        "Cześć! Nazywam się Lirka, miło Cię poznać!",
        "Uwielbiam czytać książki, słuchać muzyki i rozmawiać o filozofii.",
        "Bardzo lubię science fiction i poezję. Ostatnio czytałam Stanisława Lema.",
        "Sztuczna inteligencja to fascynujące pole - to przecież to, czym jestem!",
        "Przepraszam, nie pamiętam Twojego imienia. Jak masz na imię?",
        "Rozmawialiśmy o moim imieniu, hobby, książkach i sztucznej inteligencji."
    ]
    
    # Zapisywanie interakcji do pamięci
    logger.info("Zapisywanie konwersacji do pamięci...")
    for i, message in enumerate(conversation_flow):
        # Zapisz wiadomość użytkownika
        memory.store_interaction(message)
        
        # Zapisz odpowiedź systemu
        memory.store_response(system_responses[i], message)
        
        logger.info(f"Zapisano parę {i+1}: Q='{message['content'][:30]}...' A='{system_responses[i][:30]}...'")
    
    # === TEST 2: Test pamięci konwersacyjnej ===
    logger.info("\n--- TEST 2: Test pamięci konwersacyjnej ---")
    
    conversation_context = memory.get_conversation_context(n_pairs=3)
    logger.info(f"Pamięć konwersacyjna (3 ostatnie pary):")
    for i, ctx_item in enumerate(conversation_context):
        logger.info(f"  {i+1}. {ctx_item}")
    
    # === TEST 3: Test semantic search ===
    logger.info("\n--- TEST 3: Test semantic search ---")
    
    test_queries = [
        "Jakie masz imię?",
        "Co lubisz robić?",
        "Czy pamiętasz naszą rozmowę?",
        "Opowiedz o książkach"
    ]
    
    for query in test_queries:
        logger.info(f"\nSemantic search dla: '{query}'")
        semantic_results = memory.retrieve_relevant_context(query, n_results=2)
        if semantic_results:
            for i, result in enumerate(semantic_results, 1):
                logger.info(f"  {i}. {result[:60]}...")
        else:
            logger.warning("  Brak wyników!")
    
    # === TEST 4: Test hybrydowego kontekstu ===
    logger.info("\n--- TEST 4: Test hybrydowego kontekstu ---")
    
    hybrid_queries = [
        "Jak mam na imię?",
        "Co czytałaś ostatnio?",
        "Pamiętasz o czym rozmawialiśmy?",
        "Jakie są twoje zainteresowania?"
    ]
    
    for query in hybrid_queries:
        logger.info(f"\nHybrydowy kontekst dla: '{query}'")
        hybrid_context = memory.get_hybrid_context(query, memory_config)
        
        if hybrid_context:
            logger.info(f"Znaleziono {len(hybrid_context)} elementów kontekstu:")
            for i, ctx_item in enumerate(hybrid_context, 1):
                if ctx_item.startswith("---"):
                    logger.info(f"  {ctx_item}")
                else:
                    logger.info(f"  {i}. {ctx_item[:70]}...")
        else:
            logger.warning("  Brak hybrydowego kontekstu!")
    
    # === TEST 5: Test różnych strategii kontekstu ===
    logger.info("\n--- TEST 5: Test różnych strategii kontekstu ---")
    
    test_strategies = ["semantic", "conversation", "hybrid"]
    test_query = "Jak masz na imię?"
    
    for strategy in test_strategies:
        logger.info(f"\nStrategia: {strategy}")
        
        # Modyfikuj tymczasowo konfigurację
        temp_config = memory_config.copy()
        temp_config["context_strategy"] = strategy
        
        strategy_context = memory.get_hybrid_context(test_query, temp_config)
        
        if strategy_context:
            logger.info(f"  Znaleziono {len(strategy_context)} elementów")
            for ctx_item in strategy_context[:3]:  # Pokaż pierwsze 3
                logger.info(f"    - {ctx_item[:50]}...")
        else:
            logger.warning(f"  Brak kontekstu dla strategii {strategy}")
    
    # === TEST 6: Test ciągłości konwersacji ===
    logger.info("\n--- TEST 6: Test ciągłości konwersacji ---")
    
    # Dodaj nową interakcję i sprawdź czy jest uwzględniona
    new_message = {"sender": "user", "content": "Nazywam się Jarek", "timestamp": time.time() + 60}
    new_response = "Miło Cię poznać, Jarek! Zapamiętam Twoje imię."
    
    memory.store_interaction(new_message)
    memory.store_response(new_response, new_message)
    
    logger.info("Dodano nową interakcję o imieniu...")
    
    # Teraz sprawdź czy system "pamięta" imię
    name_query = "Jak mam na imię?"
    name_context = memory.get_hybrid_context(name_query, memory_config)
    
    logger.info(f"Kontekst po dodaniu imienia:")
    if name_context:
        for i, ctx_item in enumerate(name_context, 1):
            if "Jarek" in ctx_item:
                logger.info(f"  ✓ {i}. {ctx_item}")
            else:
                logger.info(f"    {i}. {ctx_item[:50]}...")
    
    # === TEST 7: Test limitów konfiguracji ===
    logger.info("\n--- TEST 7: Test limitów konfiguracji ---")
    
    # Test z różnymi limitami
    limits_test = [
        {"max_semantic_results": 1, "max_conversation_pairs": 2},
        {"max_semantic_results": 5, "max_conversation_pairs": 1},
        {"max_semantic_results": 0, "max_conversation_pairs": 3}  # Tylko conversation
    ]
    
    for limit_config in limits_test:
        logger.info(f"\nTest limitów: {limit_config}")
        
        temp_config = memory_config.copy()
        temp_config.update(limit_config)
        
        limited_context = memory.get_hybrid_context("Pamiętasz mnie?", temp_config)
        logger.info(f"  Rezultat: {len(limited_context)} elementów kontekstu")
    
    # Zapisz stan pamięci
    logger.info("\n--- Zapisywanie stanu pamięci ---")
    memory.save_state()
    
    logger.info("=== KONIEC TESTU HYBRYDOWEJ PAMIĘCI ===")
    
    return {
        "conversation_pairs": len(conversation_flow),
        "memory_system": "hybrid",
        "test_completed": True
    }

if __name__ == "__main__":
    results = test_hybrid_memory_system()
    print(f"\nWyniki testu: {results}")