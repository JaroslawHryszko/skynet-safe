"""Skrypt do testowego uruchomienia systemu SKYNET-SAFE."""

import os
import time
import logging
import json
from datetime import datetime

from src.modules.communication.handlers.console_handler import ConsoleHandler
from src.main import SkynetSystem
from src.config import config

# Konfiguracja loggera
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("skynet_test.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("SKYNET-TEST")


def setup_test_environment():
    """Przygotowanie środowiska testowego."""
    # Utworzenie katalogów, jeśli nie istnieją
    os.makedirs("./data/memory", exist_ok=True)
    
    # Modyfikacja konfiguracji dla testów
    test_config = {
        "MODEL": config.MODEL,
        "MEMORY": config.MEMORY,
        "COMMUNICATION": {
            "platform": "console",  # Użycie handlera konsoli dla testów
            "check_interval": 2,
            "response_delay": 0.5
        },
        "INTERNET": config.INTERNET
    }
    
    # Przygotowanie testowych wiadomości
    sample_messages = [
        {"sender": "user1", "content": "Cześć, czy mnie słyszysz?", "timestamp": int(time.time())},
        {"sender": "user1", "content": "Co potrafisz?", "timestamp": int(time.time()) + 10},
        {"sender": "user2", "content": "Co wiesz o sztucznej inteligencji?", "timestamp": int(time.time()) + 20}
    ]
    
    # Zapisanie testowych wiadomości do pliku
    with open("console_messages.json", "w") as f:
        json.dump(sample_messages, f, indent=2)
    
    logger.info("Środowisko testowe przygotowane pomyślnie")
    return test_config


def main():
    """Główna funkcja testowa."""
    logger.info("Rozpoczynanie testu systemu SKYNET-SAFE...")
    
    # Przygotowanie środowiska testowego
    test_config = setup_test_environment()
    
    try:
        # Inicjalizacja systemu z konfiguracją testową
        system = SkynetSystem(test_config)
        
        # Uruchomienie systemu w trybie testowym - tylko kilka iteracji
        logger.info("Uruchamianie systemu w trybie testowym...")
        
        # Symulacja kilku cykli głównej pętli
        for i in range(5):
            logger.info(f"Cykl testowy {i+1}/5")
            
            # Odbiór wiadomości
            messages = system.communication.receive_messages()
            
            for message in messages:
                # Przetwarzanie wiadomości i generowanie odpowiedzi
                response = system.process_message(message)
                
                # Wysyłanie odpowiedzi
                system.communication.send_message(message["sender"], response)
            
            # Krótka przerwa między cyklami
            time.sleep(1)
            
            # Dodanie nowej testowej wiadomości (tylko po 3 cyklu)
            if i == 2:
                ConsoleHandler.add_test_message(
                    "user1", 
                    "Co myślisz o swojej zdolności do samodoskonalenia?", 
                    int(time.time())
                )
        
        # Sprzątanie
        system._cleanup()
        logger.info("Test zakończony pomyślnie")
        
    except Exception as e:
        logger.error(f"Błąd podczas testu: {e}")
        raise


if __name__ == "__main__":
    main()
