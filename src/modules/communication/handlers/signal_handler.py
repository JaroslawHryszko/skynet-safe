"""Handler wiadomości dla platformy Signal z wykorzystaniem signal-cli."""

import logging
import time
import subprocess
import json
import os
from typing import Dict, List, Any
import re

from src.modules.communication.handlers.base_handler import MessageHandler

logger = logging.getLogger(__name__)


class SignalHandler(MessageHandler):
    """Handler wiadomości dla platformy Signal używający signal-cli.
    
    Wykorzystuje signal-cli (https://github.com/AsamK/signal-cli) jako interfejs do
    komunikacji z usługą Signal.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Inicjalizacja handlera Signal.
        
        Args:
            config: Konfiguracja dla handlera Signal zawierająca phone_number i config_path
        """
        super().__init__(config)
        logger.info("Inicjalizacja handlera wiadomości Signal...")
        
        # Pobranie konfiguracji
        self.phone_number = config.get("signal_phone_number")
        if not self.phone_number:
            raise ValueError("Brak numeru telefonu w konfiguracji Signal")
            
        self.config_path = config.get("signal_config_path")
        if not self.config_path:
            self.config_path = os.path.expanduser("~/.local/share/signal-cli/data")
            
        # Sprawdzenie, czy signal-cli jest zainstalowane
        try:
            result = subprocess.run(["signal-cli", "--version"], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    text=True)
            logger.info(f"Signal-CLI wersja: {result.stdout.strip()}")
        except FileNotFoundError:
            logger.error("Signal-CLI nie jest zainstalowane lub nie jest dostępne w PATH")
            raise
            
        # Czas ostatnio widzianej wiadomości
        self.last_seen_timestamp = int(time.time() * 1000)  # Signal używa milisekund
        
        logger.info(f"Handler wiadomości Signal zainicjalizowany dla numeru {self.phone_number}")
    
    def get_new_messages(self) -> List[Dict[str, Any]]:
        """Pobranie nowych wiadomości z Signala.
        
        Returns:
            Lista nowych wiadomości w formacie [{"sender": str, "content": str, "timestamp": int}]
        """
        messages = []
        
        try:
            # Pobranie wiadomości z signal-cli
            result = subprocess.run(
                [
                    "signal-cli", 
                    "-u", self.phone_number, 
                    "--config", self.config_path, 
                    "receive",
                    "--json"
                ], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Błąd podczas odbierania wiadomości: {result.stderr}")
                return messages
                
            # Parsowanie wyniku
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                    
                try:
                    msg_data = json.loads(line)
                    
                    # Pomijanie starych wiadomości
                    timestamp = msg_data.get("timestamp", 0)
                    if timestamp <= self.last_seen_timestamp:
                        continue
                        
                    # Aktualizacja znacznika czasu ostatnio widzianej wiadomości
                    self.last_seen_timestamp = max(self.last_seen_timestamp, timestamp)
                    
                    # Wyodrębnienie nadawcy i treści
                    sender = msg_data.get("sourceNumber", "unknown")
                    if "dataMessage" in msg_data and "message" in msg_data["dataMessage"]:
                        content = msg_data["dataMessage"]["message"]
                        
                        # Dodanie wiadomości do listy
                        messages.append({
                            "sender": sender,
                            "content": content,
                            "timestamp": int(timestamp / 1000)  # Konwersja z milisekund na sekundy
                        })
                except json.JSONDecodeError:
                    logger.warning(f"Nie można sparsować linii JSON: {line}")
                except Exception as e:
                    logger.warning(f"Błąd podczas przetwarzania wiadomości: {e}")
            
            if messages:
                logger.info(f"Odebrano {len(messages)} nowych wiadomości z Signal")
                
        except Exception as e:
            logger.error(f"Błąd podczas pobierania wiadomości z Signal: {e}")
        
        return messages
    
    def send_message(self, recipient: str, content: str) -> bool:
        """Wysłanie wiadomości do odbiorcy przez Signala.
        
        Args:
            recipient: Identyfikator odbiorcy (numer telefonu)
            content: Treść wiadomości
            
        Returns:
            True, jeśli wysłanie się powiodło, False w przeciwnym wypadku
        """
        # Upewnienie się, że odbiorca ma format numeru telefonu
        if not re.match(r'^\+[0-9]+$', recipient):
            logger.warning(f"Nieprawidłowy format numeru telefonu: {recipient}")
            return False
            
        try:
            # Wysłanie wiadomości przez signal-cli
            result = subprocess.run(
                [
                    "signal-cli", 
                    "-u", self.phone_number, 
                    "--config", self.config_path, 
                    "send", 
                    "-m", content, 
                    recipient
                ], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Błąd podczas wysyłania wiadomości: {result.stderr}")
                return False
                
            logger.info(f"Wysłano wiadomość przez Signal do {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania wiadomości przez Signal: {e}")
            return False
    
    def close(self) -> None:
        """Zamknięcie połączenia z Signalem i sprzątanie zasobów."""
        # Signal-CLI nie wymaga zamykania połączenia,
        # ponieważ dla każdego polecenia tworzone jest nowe połączenie
        logger.info("Zamknięcie handlera Signal")
