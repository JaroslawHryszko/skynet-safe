#!/usr/bin/env python3
"""
Interaktywny tryb uruchamiania systemu SKYNET-SAFE.
Umożliwia bezpośrednią komunikację z systemem poprzez konsolę.
"""

import os
import logging
import time
from datetime import datetime

from src.main import SkynetSystem
from src.config import config
from src.modules.communication.handlers.console_handler import ConsoleHandler

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("skynet_interactive.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("SKYNET-INTERACTIVE")


def setup_environment():
    """Przygotowanie środowiska przed uruchomieniem."""
    # Utworzenie katalogów, jeśli nie istnieją
    os.makedirs("./data/memory", exist_ok=True)
    
    # Modyfikacja konfiguracji dla trybu interaktywnego
    interactive_config = {
        "MODEL": config.MODEL,
        "MEMORY": config.MEMORY,
        "COMMUNICATION": {
            "platform": "console",  # Użycie handlera konsoli
            "check_interval": 1,
            "response_delay": 0.5
        },
        "INTERNET": config.INTERNET
    }
    
    # Usunięcie starych plików wiadomości, jeśli istnieją
    if os.path.exists("console_messages.json"):
        os.remove("console_messages.json")
    if os.path.exists("skynet_responses.json"):
        os.remove("skynet_responses.json")
    
    logger.info("Środowisko interaktywne przygotowane pomyślnie")
    return interactive_config


def main():
    """Główna funkcja trybu interaktywnego."""
    logger.info("Uruchamianie interaktywnego trybu SKYNET-SAFE...")
    
    # Przygotowanie środowiska
    interactive_config = setup_environment()
    
    try:
        # Inicjalizacja systemu
        system = SkynetSystem(interactive_config)
        
        print("\n" + "="*70)
        print(" SKYNET-SAFE Tryb Interaktywny ".center(70, "="))
        print("="*70)
        print(" Wpisz 'exit' lub 'quit', aby zakończyć sesję ".center(70, "-"))
        print("="*70 + "\n")
        
        # Główna pętla interakcji
        user_id = "user1"  # Domyślny identyfikator użytkownika
        
        while True:
            # Pobierz wiadomość od użytkownika
            user_input = input("\nTy: ")
            
            # Sprawdź, czy użytkownik chce zakończyć
            if user_input.lower() in ['exit', 'quit']:
                print("\nKończenie sesji...\n")
                system._cleanup()
                break
            
            # Dodaj wiadomość do pliku console_messages.json
            timestamp = int(time.time())
            ConsoleHandler.add_test_message(user_id, user_input, timestamp)
            
            # Odbiór wiadomości
            messages = system.communication.receive_messages()
            
            for message in messages:
                # Przetwarzanie wiadomości i generowanie odpowiedzi
                print("\nSKYNET przetwarza wiadomość...")
                response = system.process_message(message)
                
                # Wyświetlenie odpowiedzi (bez wysyłania jej przez system komunikacji)
                print(f"\nSKYNET: {response}\n")
        
    except KeyboardInterrupt:
        logger.info("Zatrzymywanie systemu przez użytkownika...")
        system._cleanup()
    except Exception as e:
        logger.error(f"Błąd podczas pracy w trybie interaktywnym: {e}")
        if 'system' in locals():
            system._cleanup()
        raise


if __name__ == "__main__":
    main()