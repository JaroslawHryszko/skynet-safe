"""Handler wiadomości dla prostej komunikacji przez konsolę (do testów)."""

import logging
import time
from typing import Dict, List, Any
import os
import json

from src.modules.communication.handlers.base_handler import MessageHandler

logger = logging.getLogger(__name__)


class ConsoleHandler(MessageHandler):
    """Handler wiadomości symulujący komunikację przez konsolę.
    
    Przydatny do testów systemu bez konieczności konfigurowania prawdziwej platformy komunikacyjnej.
    Wiadomości są przechowywane w prostym pliku JSON.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Inicjalizacja handlera konsoli.
        
        Args:
            config: Konfiguracja dla handlera konsoli
        """
        super().__init__(config)
        logger.info("Inicjalizacja handlera wiadomości konsoli...")
        
        # Ścieżka do pliku z wiadomościami
        self.messages_file = os.path.join(os.getcwd(), "console_messages.json")
        
        # Timestamp ostatnio widzianej wiadomości
        self.last_seen_timestamp = int(time.time())
        
        # Utworzenie pliku z wiadomościami, jeśli nie istnieje
        if not os.path.exists(self.messages_file):
            with open(self.messages_file, "w") as f:
                json.dump([], f)
        
        logger.info(f"Handler wiadomości konsoli zainicjalizowany, plik: {self.messages_file}")
    
    def get_new_messages(self) -> List[Dict[str, Any]]:
        """Pobranie nowych wiadomości z pliku.
        
        Returns:
            Lista nowych wiadomości w formacie [{"sender": str, "content": str, "timestamp": int}]
        """
        try:
            # Odczytanie wszystkich wiadomości z pliku
            with open(self.messages_file, "r") as f:
                all_messages = json.load(f)
            
            # Filtrowanie tylko nowych wiadomości
            new_messages = [msg for msg in all_messages if msg["timestamp"] > self.last_seen_timestamp]
            
            if new_messages:
                # Aktualizacja timestampu ostatniej widzianej wiadomości
                self.last_seen_timestamp = max(msg["timestamp"] for msg in new_messages)
                logger.info(f"Odebrano {len(new_messages)} nowych wiadomości z konsoli")
            
            return new_messages
        except Exception as e:
            logger.error(f"Błąd przy odczytywaniu wiadomości z konsoli: {e}")
            return []
    
    def send_message(self, recipient: str, content: str) -> bool:
        """Wysłanie wiadomości do odbiorcy (zapis do pliku i konsoli).
        
        Args:
            recipient: Identyfikator odbiorcy
            content: Treść wiadomości
            
        Returns:
            True, jeśli wysłanie się powiodło, False w przeciwnym wypadku
        """
        try:
            # Wyświetlenie wiadomości w konsoli
            print(f"\n[SKYNET do {recipient}]: {content}\n")
            
            # Zapis wiadomości do pliku odpowiedzi (dla celów testowych)
            response_file = os.path.join(os.getcwd(), "skynet_responses.json")
            
            # Odczytanie istniejących odpowiedzi, jeśli plik istnieje
            responses = []
            if os.path.exists(response_file):
                with open(response_file, "r") as f:
                    try:
                        responses = json.load(f)
                    except json.JSONDecodeError:
                        responses = []
            
            # Dodanie nowej odpowiedzi
            response = {
                "recipient": recipient,
                "content": content,
                "timestamp": int(time.time())
            }
            responses.append(response)
            
            # Zapisanie zaktualizowanych odpowiedzi
            with open(response_file, "w") as f:
                json.dump(responses, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Błąd przy wysyłaniu wiadomości konsoli: {e}")
            return False
    
    def close(self) -> None:
        """Zamknięcie handlera konsoli."""
        # Nie ma potrzeby zamykania czegokłowiek
        logger.info("Handler wiadomości konsoli zamknięty")
    
    @staticmethod
    def add_test_message(sender: str, content: str, timestamp: int = None) -> bool:
        """Dodanie testowej wiadomości "od użytkownika" do pliku.
        
        Ta metoda jest przeznaczona do testów - pozwala symulować otrzymanie wiadomości od użytkownika.
        
        Args:
            sender: Identyfikator nadawcy
            content: Treść wiadomości
            timestamp: Timestamp wiadomości (jeśli None, używany jest obecny czas)
            
        Returns:
            True, jeśli dodanie się powiodło, False w przeciwnym wypadku
        """
        try:
            messages_file = os.path.join(os.getcwd(), "console_messages.json")
            
            # Odczytanie istniejących wiadomości, jeśli plik istnieje
            messages = []
            if os.path.exists(messages_file):
                with open(messages_file, "r") as f:
                    try:
                        messages = json.load(f)
                    except json.JSONDecodeError:
                        messages = []
            
            # Dodanie nowej wiadomości
            message = {
                "sender": sender,
                "content": content,
                "timestamp": timestamp or int(time.time())
            }
            messages.append(message)
            
            # Zapisanie zaktualizowanych wiadomości
            with open(messages_file, "w") as f:
                json.dump(messages, f, indent=2)
            
            # Wyświetlenie informacji w konsoli
            print(f"\n[Użytkownik {sender}]: {content}\n")
            
            return True
        except Exception as e:
            logger.error(f"Błąd przy dodawaniu testowej wiadomości: {e}")
            return False
