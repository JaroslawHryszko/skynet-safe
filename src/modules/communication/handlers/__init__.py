"""Implementacje handlerów dla różnych platform komunikacyjnych."""

from typing import Dict, Any

from src.modules.communication.handlers.base_handler import MessageHandler
from src.modules.communication.handlers.signal_handler import SignalHandler
from src.modules.communication.handlers.console_handler import ConsoleHandler
from src.modules.communication.handlers.telegram_handler import TelegramHandler

# Inicjalizuj mapę dostosowującą nazwę platformy do odpowiedniej klasy handlera
PLATFORM_HANDLERS = {
    "signal": SignalHandler,
    "console": ConsoleHandler,  # Prosty handler dla testów przez konsolę
    "telegram": TelegramHandler  # Handler dla komunikatora Telegram
}


def get_message_handler(platform: str, config: Dict[str, Any]) -> MessageHandler:
    """Uzyskanie odpowiedniego handlera wiadomości dla wybranej platformy.
    
    Args:
        platform: Nazwa platformy komunikacyjnej
        config: Konfiguracja dla handlera
        
    Returns:
        Handler wiadomości dla wybranej platformy
        
    Raises:
        ValueError: Jeśli platforma nie jest obsługiwana
    """
    if platform not in PLATFORM_HANDLERS:
        raise ValueError(f"Nieobsługiwana platforma komunikacyjna: {platform}")
    
    handler_class = PLATFORM_HANDLERS[platform]
    return handler_class(config)
