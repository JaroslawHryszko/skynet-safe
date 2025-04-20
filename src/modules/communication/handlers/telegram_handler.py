"""Handler wiadomości dla platformy Telegram."""

import logging
import time
import os
import requests
import json
from typing import Dict, List, Any, Optional

from src.modules.communication.handlers.base_handler import MessageHandler

logger = logging.getLogger("SKYNET-SAFE.TelegramHandler")


class TelegramHandler(MessageHandler):
    """Handler wiadomości dla platformy Telegram używający Telegram Bot API.
    
    Wykorzystuje Telegram Bot API do komunikacji z użytkownikami Telegram.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Inicjalizacja handlera Telegram.
        
        Args:
            config: Konfiguracja dla handlera Telegram zawierająca bot_token i inne parametry
        """
        super().__init__(config)
        logger.info("Inicjalizacja handlera wiadomości Telegram...")
        
        # Pobranie konfiguracji
        self.bot_token = config.get("telegram_bot_token")
        if not self.bot_token:
            raise ValueError("Brak tokenu bota w konfiguracji Telegram")
            
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.polling_timeout = config.get("telegram_polling_timeout", 30)
        self.allowed_users = config.get("telegram_allowed_users", [])
        self.chat_state_file = config.get("telegram_chat_state_file", "./data/telegram/chat_state.json")
        
        # Tworzenie katalogów jeśli nie istnieją
        os.makedirs(os.path.dirname(self.chat_state_file), exist_ok=True)
        
        # Inicjalizacja stanu chatu
        self.chats = {}
        self.load_chat_state()
        
        # Ostatnio widziany update_id
        self.last_update_id = 0
        
        # Sprawdzenie czy bot działa
        try:
            response = requests.get(f"{self.api_url}/getMe")
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get("ok"):
                    bot_name = bot_info["result"].get("username")
                    logger.info(f"Bot Telegram połączony pomyślnie: @{bot_name}")
                else:
                    logger.error(f"Błąd połączenia z API Telegram: {bot_info.get('description')}")
                    raise ConnectionError(f"Błąd API Telegram: {bot_info.get('description')}")
            else:
                logger.error(f"Błąd połączenia z API Telegram: {response.status_code}")
                raise ConnectionError(f"Błąd połączenia z API Telegram: {response.status_code}")
        except Exception as e:
            logger.error(f"Błąd podczas inicjalizacji bota Telegram: {e}")
            raise
        
        logger.info("Handler wiadomości Telegram zainicjalizowany pomyślnie")
    
    def get_new_messages(self) -> List[Dict[str, Any]]:
        """Pobranie nowych wiadomości z Telegram.
        
        Returns:
            Lista nowych wiadomości w formacie [{"sender": str, "content": str, "timestamp": int}]
        """
        messages = []
        
        try:
            # Pobranie aktualizacji z API Telegram
            params = {
                "offset": self.last_update_id + 1,
                "timeout": self.polling_timeout,
                "allowed_updates": ["message"]
            }
            
            response = requests.get(f"{self.api_url}/getUpdates", params=params)
            if response.status_code != 200:
                logger.error(f"Błąd podczas pobierania aktualizacji: {response.status_code}")
                return messages
            
            updates = response.json()
            
            if not updates.get("ok"):
                logger.error(f"Błąd API Telegram: {updates.get('description')}")
                return messages
            
            for update in updates.get("result", []):
                update_id = update.get("update_id", 0)
                self.last_update_id = max(self.last_update_id, update_id)
                
                if "message" not in update:
                    continue
                
                message = update["message"]
                
                # Sprawdzenie czy wiadomość zawiera tekst
                if "text" not in message:
                    continue
                
                # Pobranie informacji o nadawcy
                chat_id = str(message.get("chat", {}).get("id", ""))
                user_id = str(message.get("from", {}).get("id", ""))
                username = message.get("from", {}).get("username", "")
                first_name = message.get("from", {}).get("first_name", "")
                last_name = message.get("from", {}).get("last_name", "")
                
                # Sprawdzenie czy użytkownik jest na liście dozwolonych (jeśli lista istnieje)
                if self.allowed_users and user_id not in self.allowed_users:
                    logger.warning(f"Odrzucono wiadomość od nieautoryzowanego użytkownika: {user_id} ({username})")
                    continue
                
                # Dodanie użytkownika do listy znanych chatów
                self._add_chat(chat_id, user_id, username, first_name, last_name)
                
                # Dodanie wiadomości do listy
                timestamp = message.get("date", int(time.time()))
                content = message.get("text", "")
                
                messages.append({
                    "sender": chat_id,  # Używamy chat_id jako identyfikatora nadawcy
                    "content": content,
                    "timestamp": timestamp,
                    "metadata": {
                        "user_id": user_id,
                        "username": username,
                        "first_name": first_name,
                        "last_name": last_name
                    }
                })
            
            if messages:
                logger.info(f"Odebrano {len(messages)} nowych wiadomości z Telegram")
                # Zapisanie aktualizacji stanu chatów
                self.save_chat_state()
                
        except Exception as e:
            logger.error(f"Błąd podczas pobierania wiadomości z Telegram: {e}")
        
        return messages
    
    def send_message(self, recipient: str, content: str) -> bool:
        """Wysłanie wiadomości do odbiorcy przez Telegram.
        
        Args:
            recipient: Identyfikator odbiorcy (chat_id)
            content: Treść wiadomości
            
        Returns:
            True, jeśli wysłanie się powiodło, False w przeciwnym wypadku
        """
        try:
            # Przygotowanie danych do wysłania
            payload = {
                "chat_id": recipient,
                "text": content,
                "parse_mode": "HTML"  # Możliwość formatowania HTML
            }
            
            # Wysłanie wiadomości przez API Telegram
            response = requests.post(f"{self.api_url}/sendMessage", json=payload)
            
            if response.status_code != 200:
                logger.error(f"Błąd podczas wysyłania wiadomości: {response.status_code}")
                return False
            
            result = response.json()
            
            if not result.get("ok"):
                logger.error(f"Błąd API Telegram: {result.get('description')}")
                return False
            
            logger.info(f"Wysłano wiadomość przez Telegram do {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania wiadomości przez Telegram: {e}")
            return False
    
    def _add_chat(self, chat_id: str, user_id: str, username: str, first_name: str, last_name: str) -> None:
        """Dodaje lub aktualizuje informacje o chacie.
        
        Args:
            chat_id: ID chatu
            user_id: ID użytkownika
            username: Nazwa użytkownika
            first_name: Imię użytkownika
            last_name: Nazwisko użytkownika
        """
        self.chats[chat_id] = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "last_activity": int(time.time())
        }
    
    def load_chat_state(self) -> None:
        """Wczytuje stan chatów z pliku."""
        if os.path.exists(self.chat_state_file):
            try:
                with open(self.chat_state_file, 'r') as f:
                    self.chats = json.load(f)
                logger.info(f"Wczytano stan {len(self.chats)} chatów z {self.chat_state_file}")
            except Exception as e:
                logger.error(f"Błąd podczas wczytywania stanu chatów: {e}")
    
    def save_chat_state(self) -> None:
        """Zapisuje stan chatów do pliku."""
        try:
            with open(self.chat_state_file, 'w') as f:
                json.dump(self.chats, f, indent=2)
            logger.debug(f"Zapisano stan {len(self.chats)} chatów do {self.chat_state_file}")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania stanu chatów: {e}")
    
    def close(self) -> None:
        """Zamknięcie połączenia z Telegram i sprzątanie zasobów."""
        # Zapisanie stanu chatów przed zamknięciem
        self.save_chat_state()
        logger.info("Zamknięcie handlera Telegram")