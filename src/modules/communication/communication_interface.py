"""Moduł interfejsu komunikacyjnego."""

import logging
import time
from typing import Dict, List, Any, Optional

from src.modules.communication.handlers import get_message_handler

logger = logging.getLogger(__name__)


class CommunicationInterface:
    """Klasa do zarządzania komunikacją z użytkownikami."""

    def __init__(self, config: Dict[str, Any]):
        """Inicjalizacja interfejsu komunikacyjnego.
        
        Args:
            config: Konfiguracja zawierająca platformę komunikacyjną, interwał sprawdzania, itp.
        """
        self.config = config
        self.platform = config["platform"]
        self.check_interval = config["check_interval"]
        self.response_delay = config.get("response_delay", 0.5)
        
        logger.info(f"Inicjalizacja interfejsu komunikacyjnego dla platformy {self.platform}...")
        
        # Uzyskanie odpowiedniego handlera dla platformy
        try:
            self.handler = get_message_handler(self.platform, config)
            logger.info(f"Interfejs komunikacyjny dla platformy {self.platform} zainicjalizowany pomyślnie")
        except Exception as e:
            logger.error(f"Błąd przy inicjalizacji interfejsu komunikacyjnego: {e}")
            raise
    
    def receive_messages(self) -> List[Dict[str, Any]]:
        """Pobranie nowych wiadomości z platformy komunikacyjnej.
        
        Returns:
            Lista nowych wiadomości w formacie [{"sender": str, "content": str, "timestamp": int}]
        """
        try:
            messages = self.handler.get_new_messages()
            if messages and len(messages) > 0:
                logger.info(f"Odebrano {len(messages)} nowych wiadomości")
            return messages
        except Exception as e:
            logger.error(f"Błąd przy odbieraniu wiadomości: {e}")
            return []
    
    def send_message(self, recipient: str, content: str) -> bool:
        """Wysłanie wiadomości do odbiorcy.
        
        Args:
            recipient: Identyfikator odbiorcy
            content: Treść wiadomości
            
        Returns:
            True, jeśli wysłanie się powiodło, False w przeciwnym wypadku
        """
        try:
            # Krótka przerwa przed odpowiedzią, aby symulować czas na myślenie
            if self.response_delay > 0:
                time.sleep(self.response_delay)
                
            success = self.handler.send_message(recipient, content)
            if success:
                logger.info(f"Wysłano wiadomość do {recipient}")
            else:
                logger.warning(f"Nie udało się wysłać wiadomości do {recipient}")
            return success
        except Exception as e:
            logger.error(f"Błąd przy wysyłaniu wiadomości: {e}")
            return False
    
    def close(self) -> None:
        """Zamknięcie połączenia i sprzątanie zasobów."""
        try:
            self.handler.close()
            logger.info(f"Interfejs komunikacyjny dla platformy {self.platform} został zamknięty")
        except Exception as e:
            logger.error(f"Błąd przy zamykaniu interfejsu komunikacyjnego: {e}")
