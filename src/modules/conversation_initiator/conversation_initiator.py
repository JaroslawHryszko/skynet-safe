"""Moduł inicjowania konwersacji z użytkownikiem."""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger("SKYNET-SAFE.ConversationInitiator")

class ConversationInitiator:
    """Klasa odpowiedzialna za inicjowanie konwersacji z użytkownikiem."""

    def __init__(self, config: Dict[str, Any]):
        """Inicjalizacja inicjatora konwersacji z konfiguracją.
        
        Args:
            config: Konfiguracja inicjatora konwersacji zawierająca parametry takie jak
                   min_time_between_initiations, init_probability, topics_of_interest, itp.
        """
        self.config = config
        self.min_time_between_initiations = config.get("min_time_between_initiations", 3600)  # sekundy
        self.init_probability = config.get("init_probability", 0.3)
        self.topics_of_interest = config.get("topics_of_interest", ["AI", "metaświadomość", "uczenie maszynowe"])
        self.max_daily_initiations = config.get("max_daily_initiations", 5)
        
        # Historia zainicjowanych konwersacji (timestampy)
        self.initiated_conversations = []
        
        logger.info(f"Inicjator konwersacji zainicjalizowany z {self.init_probability=}, tematy: {self.topics_of_interest}")

    def should_initiate_conversation(self) -> bool:
        """Sprawdza, czy należy zainicjować konwersację.
        
        Returns:
            True, jeśli system powinien zainicjować konwersację, False w przeciwnym razie
        """
        # Losowy czynnik - prawdopodobieństwo inicjacji
        if random.random() > self.init_probability:
            logger.debug("Prawdopodobieństwo inicjacji nie zostało osiągnięte")
            return False
        
        # Sprawdzamy, czy minął minimalny czas od ostatniej inicjacji
        current_time = datetime.now()
        if self.initiated_conversations:
            last_initiation = max(self.initiated_conversations)
            time_since_last = (current_time - last_initiation).total_seconds()
            
            if time_since_last < self.min_time_between_initiations:
                logger.debug(f"Za wcześnie na nową inicjację, minęło tylko {time_since_last} sekund")
                return False
        
        # Sprawdzamy, czy nie przekroczyliśmy limitu dziennych inicjacji
        today = current_time.date()
        today_initiations = sum(1 for ts in self.initiated_conversations 
                               if ts.date() == today)
        
        if today_initiations >= self.max_daily_initiations:
            logger.debug(f"Przekroczono limit dziennych inicjacji: {today_initiations}/{self.max_daily_initiations}")
            return False
        
        logger.info("Warunki do inicjacji konwersacji zostały spełnione")
        return True

    def get_topic_for_initiation(self, discoveries: List[Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        """Wybiera temat do inicjacji konwersacji.
        
        Args:
            discoveries: Lista odkryć z modułu internetowego
            
        Returns:
            Temat konwersacji (string lub słownik z odkryciem)
        """
        if discoveries:
            # Jeśli mamy odkrycia, wybieramy losowo jedno z nich
            logger.info(f"Wybór tematu z {len(discoveries)} dostępnych odkryć")
            return random.choice(discoveries)
        else:
            # Jeśli nie mamy odkryć, wybieramy losowo jeden z tematów zainteresowań
            logger.info("Brak odkryć, wybór tematu z predefiniowanych zainteresowań")
            return random.choice(self.topics_of_interest)

    def generate_initiation_message(self, model_manager: Any, topic: Union[str, Dict[str, Any]]) -> str:
        """Generuje wiadomość inicjującą konwersację.
        
        Args:
            model_manager: Instancja ModelManager do generowania odpowiedzi
            topic: Temat konwersacji (string lub słownik z odkryciem)
            
        Returns:
            Wygenerowana wiadomość inicjująca
        """
        if isinstance(topic, dict):
            # Jeśli mamy pełne odkrycie, używamy jego treści
            topic_content = topic.get("content", "")
            topic_name = topic.get("topic", "")
            prompt = (
                f"I want to start an interesting conversation with a user about '{topic_name}'. "
                f"I found the following information: '{topic_content}'. "
                f"Generate a short, natural opening message that will interest the user in this topic. "
                f"Don't mention that you 'found information', but naturally refer to this topic."
            )
        else:
            # Jeśli mamy tylko nazwę tematu
            prompt = (
                f"I want to start an interesting conversation with a user about '{topic}'. "
                f"Generate a short, natural opening message that will interest the user in this topic."
            )
        
        logger.info(f"Generowanie wiadomości inicjującej dla tematu: {topic}")
        message = model_manager.generate_response(prompt, "")
        return message

    def initiate_conversation(self, model_manager: Any, communication_interface: Any, 
                              discoveries: List[Dict[str, Any]], recipients: List[str]) -> bool:
        """Inicjuje konwersację z użytkownikami.
        
        Args:
            model_manager: Instancja ModelManager do generowania odpowiedzi
            communication_interface: Interfejs komunikacyjny do wysyłania wiadomości
            discoveries: Lista odkryć z modułu internetowego
            recipients: Lista identyfikatorów odbiorców
            
        Returns:
            True, jeśli konwersacja została zainicjowana, False w przeciwnym razie
        """
        # Sprawdzamy, czy powinniśmy zainicjować konwersację
        if not self.should_initiate_conversation():
            return False
        
        # Wybieramy temat
        topic = self.get_topic_for_initiation(discoveries)
        
        # Generujemy wiadomość
        message = self.generate_initiation_message(model_manager, topic)
        
        # Wysyłamy wiadomość do wszystkich odbiorców
        success = False
        for recipient in recipients:
            logger.info(f"Inicjowanie konwersacji z {recipient} na temat: {topic}")
            # Wysyłamy wiadomość przez wszystkie dostępne kanały komunikacyjne
            result = communication_interface.send_message(recipient, message)
            if result:
                success = True
        
        # Zapisujemy czas inicjacji tylko jeśli udało się wysłać wiadomość
        if success:
            self.initiated_conversations.append(datetime.now())
            return True
        
        return False