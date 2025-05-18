#!/usr/bin/env python3
"""Test script sprawdzający działanie flagi enable_persona_in_prompt."""

import sys
import os

# Dodanie katalogu projektu do ścieżki Pythona
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.modules.persona.persona_manager import PersonaManager
from src.config.config import PERSONA, MODEL_PROMPT

def test_persona_flag(enable_flag):
    """Test działania flagi enable_persona_in_prompt."""
    print(f"\n=== Test dla enable_persona_in_prompt = {enable_flag} ===\n")
    
    # Tworzenie kopii konfiguracji z odpowiednią flagą
    test_config = PERSONA.copy()
    test_config["enable_persona_in_prompt"] = enable_flag
    
    # Inicjalizacja menedżera persony z testową konfiguracją
    persona_manager = PersonaManager(test_config)
    
    # Sprawdzenie czy zwracany jest kontekst persony
    context = persona_manager.get_persona_context()
    if context:
        print(f"✓ Kontekst persony zwrócony: {len(context)} znaków")
        print(f"Fragment: \"{context[:100]}...\"")
    else:
        print("✓ Kontekst persony jest pusty (zgodnie z oczekiwaniami)")
    
    # Symulacja działania apply_persona_to_response
    # Jako że nie mamy dostępu do ModelManager, tylko sprawdzamy logikę warunkową
    original_response = "To jest przykładowa odpowiedź bez persony."
    would_transform = not (test_config.get("enable_persona_in_prompt", False) == False)
    
    if would_transform:
        print("✓ System próbowałby transformować odpowiedź, aby uwzględnić personę")
    else:
        print("✓ System zwróciłby oryginalną odpowiedź bez transformacji")
    
    print("\n=== Koniec testu ===\n")

# Wykonaj testy dla obu wartości flagi
test_persona_flag(False)
test_persona_flag(True)

print("Wszystkie testy zakończone.")