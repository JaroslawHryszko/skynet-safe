#!/usr/bin/env python3
"""Test kontekstu w modelu językowym."""

import os
import sys
import logging

# Dodaj ścieżkę do modułów systemu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.modules.model.model_manager import ModelManager
from src.config import config

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("MODEL_CONTEXT_TEST")

def test_model_context():
    """Test czy model wykorzystuje kontekst w generowaniu odpowiedzi."""
    
    logger.info("=== ROZPOCZĘCIE TESTU KONTEKSTU MODELU ===")
    
    # Inicjalizacja modelu (może potrwać długo)
    logger.info("Ładowanie modelu... To może potrwać kilka minut.")
    model_config = config.MODEL
    model = ModelManager(model_config)
    
    # Test 1: Odpowiedź bez kontekstu
    logger.info("--- Test 1: Odpowiedź bez kontekstu ---")
    query = "Jak mam na imię?"
    response_no_context = model.generate_response(query, context=[])
    logger.info(f"Zapytanie: {query}")
    logger.info(f"Odpowiedź bez kontekstu: {response_no_context}")
    
    # Test 2: Odpowiedź z kontekstem
    logger.info("--- Test 2: Odpowiedź z kontekstem ---")
    context = [
        "Użytkownik powiedział wcześniej: 'Nazywam się Jan'",
        "W poprzedniej rozmowie użytkownik przedstawił się jako Jan",
        "Imię użytkownika to Jan"
    ]
    response_with_context = model.generate_response(query, context=context)
    logger.info(f"Zapytanie: {query}")
    logger.info(f"Kontekst: {context}")
    logger.info(f"Odpowiedź z kontekstem: {response_with_context}")
    
    # Test 3: Test pamięci poprzednich odpowiedzi
    logger.info("--- Test 3: Test pamięci poprzednich odpowiedzi ---")
    query2 = "O czym rozmawialiśmy wcześniej?"
    context2 = [
        "Poprzednie zapytanie: 'Jak mam na imię?'",
        "Poprzednia odpowiedź: 'Nie znam Twojego imienia'",
        "Użytkownik pytał o swoje imię"
    ]
    response_memory = model.generate_response(query2, context=context2)
    logger.info(f"Zapytanie: {query2}")
    logger.info(f"Kontekst: {context2}")
    logger.info(f"Odpowiedź z pamięcią: {response_memory}")
    
    logger.info("=== KONIEC TESTU KONTEKSTU MODELU ===")

if __name__ == "__main__":
    test_model_context()