"""Bazowa klasa dla handlerów wiadomości."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any


class MessageHandler(ABC):
    """Abstrakcyjna klasa bazowa dla wszystkich handlerów wiadomości."""
    
    def __init__(self, config: Dict[str, Any]):
        """Inicjalizacja handlera wiadomości.
        
        Args:
            config: Konfiguracja dla handlera
        """
        self.config = config
    
    @abstractmethod
    def get_new_messages(self) -> List[Dict[str, Any]]:
        """Pobranie nowych wiadomości.
        
        Returns:
            Lista nowych wiadomości w formacie [{"sender": str, "content": str, "timestamp": int}]
        """
        pass
    
    @abstractmethod
    def send_message(self, recipient: str, content: str) -> bool:
        """Wysłanie wiadomości do odbiorcy.
        
        Args:
            recipient: Identyfikator odbiorcy
            content: Treść wiadomości
            
        Returns:
            True, jeśli wysłanie się powiodło, False w przeciwnym wypadku
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Zamknięcie połączenia i sprzątanie zasobów."""
        pass
