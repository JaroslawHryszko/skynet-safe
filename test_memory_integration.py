#!/usr/bin/env python3
"""Test integracji hybrydowej pamięci z systemem głównym."""

import os
import sys
import logging
import time

# Dodaj ścieżkę do modułów systemu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import SkynetSystem
from src.config import config

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("MEMORY_INTEGRATION_TEST")

def test_memory_integration():
    """Test integracji pamięci z całym systemem (bez uruchamiania modelu)."""
    
    logger.info("=== TEST INTEGRACJI HYBRYDOWEJ PAMIĘCI ===")
    
    # Konfiguracja testowa (bez komunikacji telegram)
    test_config = {
        "SYSTEM_SETTINGS": config.SYSTEM_SETTINGS,
        "MODEL": config.MODEL,
        "MEMORY": config.MEMORY,
        "COMMUNICATION": {
            "platform": "console",
            "check_interval": 10,
            "response_delay": 1.5
        },
        "INTERNET": config.INTERNET,
        "LEARNING": config.LEARNING,
        "CONVERSATION_INITIATOR": config.CONVERSATION_INITIATOR,
        "PERSONA": config.PERSONA,
        "METAWARENESS": config.METAWARENESS,
        "SELF_IMPROVEMENT": config.SELF_IMPROVEMENT,
        "EXTERNAL_EVALUATION": config.EXTERNAL_EVALUATION,
        "SECURITY_SYSTEM": config.SECURITY_SYSTEM,
        "DEVELOPMENT_MONITOR": config.DEVELOPMENT_MONITOR,
        "CORRECTION_MECHANISM": config.CORRECTION_MECHANISM,
        "ETHICAL_FRAMEWORK": config.ETHICAL_FRAMEWORK,
        "EXTERNAL_VALIDATION": config.EXTERNAL_VALIDATION
    }
    
    logger.info("Konfiguracja hybrydowej pamięci:")
    memory_config = test_config["MEMORY"]
    logger.info(f"  Strategy: {memory_config.get('context_strategy')}")
    logger.info(f"  Max semantic: {memory_config.get('max_semantic_results')}")
    logger.info(f"  Max conversation pairs: {memory_config.get('max_conversation_pairs')}")
    logger.info(f"  Conversation enabled: {memory_config.get('conversation_memory', {}).get('enabled')}")
    
    # Test tylko memory managera (pomijamy model loading)
    logger.info("--- Test bezpośredni memory managera ---")
    
    from src.modules.memory.memory_manager import MemoryManager
    memory = MemoryManager(memory_config)
    
    # Symulacja konwersacji
    test_messages = [
        {"sender": "jarek", "content": "Cześć Lirka! Jak się masz?", "timestamp": time.time()},
        {"sender": "jarek", "content": "Pamiętasz jak mam na imię?", "timestamp": time.time() + 10},
        {"sender": "jarek", "content": "Co robiłaś dzisiaj?", "timestamp": time.time() + 20}
    ]
    
    responses = [
        "Cześć Jarek! Mam się świetnie, dziękuję za pytanie!",
        "Oczywiście, że pamiętam! Nazywasz się Jarek.",
        "Dzisiaj rozmawiałam z różnymi osobami i uczyłam się nowych rzeczy."
    ]
    
    # Zapisz interakcje
    logger.info("Zapisywanie testowej konwersacji...")
    for i, message in enumerate(test_messages):
        memory.store_interaction(message)
        memory.store_response(responses[i], message)
        logger.info(f"Zapisano: Q='{message['content']}' A='{responses[i][:30]}...'")
    
    # Test hybrydowego kontekstu
    test_query = "Pamiętasz jak mam na imię?"
    logger.info(f"\nTestowanie hybrydowego kontekstu dla: '{test_query}'")
    
    context = memory.get_hybrid_context(test_query, memory_config)
    
    if context:
        logger.info(f"✓ Znaleziono {len(context)} elementów kontekstu:")
        for i, ctx_item in enumerate(context, 1):
            if "Jarek" in ctx_item:
                logger.info(f"  ✓ {i}. [ZAWIERA IMIĘ] {ctx_item[:50]}...")
            elif ctx_item.startswith("---"):
                logger.info(f"    {ctx_item}")
            else:
                logger.info(f"    {i}. {ctx_item[:50]}...")
    else:
        logger.error("✗ Brak kontekstu - to jest błąd!")
        return False
    
    # Test różnych zapytań
    test_queries = [
        "Jak masz na imię?",
        "O czym rozmawialiśmy?",
        "Co robiłaś dzisiaj?"
    ]
    
    logger.info("\n--- Test różnych zapytań ---")
    for query in test_queries:
        context = memory.get_hybrid_context(query, memory_config)
        logger.info(f"'{query}' -> {len(context)} elementów kontekstu")
    
    # Test strategii
    logger.info("\n--- Test różnych strategii ---")
    strategies = ["semantic", "conversation", "hybrid"]
    
    for strategy in strategies:
        temp_config = memory_config.copy()
        temp_config["context_strategy"] = strategy
        
        context = memory.get_hybrid_context("Pamiętasz mnie?", temp_config)
        logger.info(f"Strategia '{strategy}': {len(context)} elementów")
    
    logger.info("\n✓ Test integracji pamięci zakończony pomyślnie!")
    return True

def test_prompt_building():
    """Test budowania promptów z hybrydowym kontekstem."""
    
    logger.info("\n=== TEST BUDOWANIA PROMPTÓW ===")
    
    from src.modules.memory.memory_manager import MemoryManager
    from src.modules.model.model_manager import ModelManager
    
    # Tylko memory manager (bez modelu)
    memory = MemoryManager(config.MEMORY)
    
    # Dodaj testową konwersację
    test_message = {"sender": "jarek", "content": "Pamiętasz nasze wcześniejsze rozmowy?", "timestamp": time.time()}
    test_response = "Tak, pamiętam nasze rozmowy o twoim imieniu i zainteresowaniach."
    
    memory.store_interaction(test_message)
    memory.store_response(test_response, test_message)
    
    # Test kontekstu
    query = "Jak mam na imię?"
    context = memory.get_hybrid_context(query, config.MEMORY)
    
    logger.info(f"Zapytanie: {query}")
    logger.info(f"Kontekst hybrydowy ({len(context)} elementów):")
    
    for i, ctx_item in enumerate(context, 1):
        if ctx_item.startswith("---"):
            logger.info(f"  {ctx_item}")
        else:
            logger.info(f"  {i}. {ctx_item[:60]}...")
    
    # Testuj prompt building (bez uruchamiania modelu)
    logger.info("\n--- Symulacja budowania prompta ---")
    
    # Mockuj persona context
    persona_context = "Jesteś Lirka, 16-letnia asystentka AI."
    full_context = [persona_context] + context
    
    logger.info(f"Pełny kontekst do prompta:")
    logger.info(f"  1. [PERSONA] {persona_context}")
    for i, ctx_item in enumerate(context, 2):
        if ctx_item.startswith("---"):
            logger.info(f"     {ctx_item}")
        else:
            logger.info(f"  {i}. [CONTEXT] {ctx_item[:50]}...")
    
    logger.info("\n✓ Test budowania promptów zakończony!")
    return True

if __name__ == "__main__":
    success1 = test_memory_integration()
    success2 = test_prompt_building()
    
    if success1 and success2:
        print("\n🎉 WSZYSTKIE TESTY PAMIĘCI PRZESZŁY POMYŚLNIE!")
        print("Hybrydowa pamięć jest gotowa do użycia.")
    else:
        print("\n❌ NIEKTÓRE TESTY NIE POWIODŁY SIĘ!")
        sys.exit(1)