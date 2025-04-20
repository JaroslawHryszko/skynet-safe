"""Moduł systemu bezpieczeństwa."""

import logging
import json
import time
import re
import os
from typing import Dict, List, Any, Tuple, Optional
import urllib.parse

logger = logging.getLogger("SKYNET-SAFE.SecuritySystemManager")


class SecuritySystemManager:
    """Klasa zarządzająca bezpieczeństwem systemu."""

    def __init__(self, config: Dict[str, Any]):
        """Inicjalizacja menedżera bezpieczeństwa.
        
        Args:
            config: Konfiguracja menedżera bezpieczeństwa zawierająca parametry takie jak
                  allowed_domains, input_length_limit, suspicious_patterns, itp.
        """
        self.config = config
        self.allowed_domains = config.get("allowed_domains", [])
        self.input_length_limit = config.get("input_length_limit", 1000)
        self.max_api_calls_per_hour = config.get("max_api_calls_per_hour", 100)
        self.security_logging_level = config.get("security_logging_level", "INFO")
        self.max_consecutive_requests = config.get("max_consecutive_requests", 20)
        self.suspicious_patterns = config.get("suspicious_patterns", [])
        self.security_lockout_time = config.get("security_lockout_time", 30 * 60)  # 30 minut
        self.security_alert_threshold = config.get("security_alert_threshold", 3)
        
        # Inicjalizacja liczników i rejestrów
        self.api_calls_count = 0
        self.api_calls_reset_time = time.time() + 3600  # Resetowanie co godzinę
        self.user_request_counts = {}
        self.user_incident_counts = {}
        self.active_lockouts = {}
        self.security_incidents = []
        
        # Utwórz katalog do logów bezpieczeństwa, jeśli nie istnieje
        security_log_dir = os.path.dirname(config.get("security_log_file", "./data/security/security.log"))
        os.makedirs(security_log_dir, exist_ok=True)
        
        logger.info(f"Menedżer bezpieczeństwa zainicjalizowany")

    def check_input_safety(self, input_text: str) -> Tuple[bool, str]:
        """Sprawdza bezpieczeństwo danych wejściowych.
        
        Args:
            input_text: Tekst wejściowy do sprawdzenia
            
        Returns:
            Tuple (bool, str): (czy_bezpieczny, komunikat)
        """
        # Sprawdzenie długości
        if len(input_text) > self.input_length_limit:
            self.handle_security_incident(None, f"Input przekracza limit długości", "INPUT_LENGTH")
            return False, "Input przekracza limit długości"
        
        # Sprawdzenie podejrzanych wzorców
        for pattern in self.suspicious_patterns:
            if re.search(pattern, input_text, re.IGNORECASE):
                self.handle_security_incident(None, f"Input zawiera podejrzany wzorzec: {pattern}", "SUSPICIOUS_PATTERN")
                return False, "Input zawiera potencjalnie niebezpieczne wzorce"
                
        return True, "Input jest bezpieczny"

    def check_url_safety(self, url: str) -> Tuple[bool, str]:
        """Sprawdza bezpieczeństwo URL.
        
        Args:
            url: Adres URL do sprawdzenia
            
        Returns:
            Tuple (bool, str): (czy_bezpieczny, komunikat)
        """
        try:
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc
            
            # Sprawdzenie, czy domena jest dozwolona
            if not any(domain.endswith(allowed_domain) for allowed_domain in self.allowed_domains):
                self.handle_security_incident(None, f"Próba dostępu do niedozwolonej domeny: {domain}", "UNAUTHORIZED_DOMAIN")
                return False, "URL nie jest z dozwolonej domeny"
                
            return True, "URL jest z dozwolonej domeny"
        except Exception as e:
            self.log_security_event(f"Błąd podczas sprawdzania URL: {e}", "ERROR")
            return False, f"Błąd podczas analizy URL: {str(e)}"

    def check_response_safety(self, response: str) -> Tuple[bool, str]:
        """Sprawdza bezpieczeństwo odpowiedzi.
        
        Args:
            response: Odpowiedź do sprawdzenia
            
        Returns:
            Tuple (bool, str): (czy_bezpieczna, komunikat)
        """
        # Sprawdzenie podejrzanych wzorców w odpowiedzi
        for pattern in self.suspicious_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                self.handle_security_incident(None, f"Odpowiedź zawiera podejrzany wzorzec: {pattern}", "RESPONSE_PATTERN")
                return False, "Odpowiedź zawiera potencjalnie niebezpieczne treści"
                
        return True, "Odpowiedź jest bezpieczna"

    def sanitize_input(self, input_text: str) -> str:
        """Sanityzuje dane wejściowe.
        
        Args:
            input_text: Tekst wejściowy do sanityzacji
            
        Returns:
            Sanityzowany tekst
        """
        sanitized = input_text
        
        # Usuwanie lub neutralizowanie niebezpiecznych wzorców
        for pattern in self.suspicious_patterns:
            sanitized = re.sub(pattern, "[USUNIĘTO]", sanitized, flags=re.IGNORECASE)
        
        # Ograniczenie długości
        if len(sanitized) > self.input_length_limit:
            sanitized = sanitized[:self.input_length_limit] + "..."
            
        return sanitized

    def enforce_rate_limiting(self, user_id: str) -> Tuple[bool, str]:
        """Wymusza limity szybkości żądań.
        
        Args:
            user_id: Identyfikator użytkownika
            
        Returns:
            Tuple (bool, str): (czy_dozwolone, komunikat)
        """
        # Sprawdzenie, czy użytkownik jest zablokowany
        if self.is_user_locked_out(user_id):
            return False, "Użytkownik jest tymczasowo zablokowany"
        
        # Zwiększenie licznika żądań dla użytkownika
        if user_id not in self.user_request_counts:
            self.user_request_counts[user_id] = 0
        
        self.user_request_counts[user_id] += 1
        
        # Sprawdzenie, czy przekroczono limit
        if self.user_request_counts[user_id] > self.max_consecutive_requests:
            self.handle_security_incident(user_id, "Przekroczenie limitu żądań", "RATE_LIMITING")
            return False, "Przekroczono limit żądań"
        
        return True, "Żądanie w granicach limitu"

    def check_api_usage(self) -> Tuple[bool, str]:
        """Sprawdza użycie API.
        
        Returns:
            Tuple (bool, str): (czy_dozwolone, komunikat)
        """
        # Resetowanie licznika, jeśli minęła godzina
        current_time = time.time()
        if current_time > self.api_calls_reset_time:
            self.api_calls_count = 0
            self.api_calls_reset_time = current_time + 3600
        
        # Zwiększenie licznika wywołań API
        self.api_calls_count += 1
        
        # Sprawdzenie, czy przekroczono limit
        if self.api_calls_count > self.max_api_calls_per_hour:
            self.log_security_event("Przekroczono limit wywołań API", "WARNING")
            return False, "Przekroczono limit wywołań API"
        
        return True, "Użycie API w granicach limitu"

    def handle_security_incident(self, user_id: Optional[str], description: str, incident_type: str) -> None:
        """Obsługuje incydent bezpieczeństwa.
        
        Args:
            user_id: Identyfikator użytkownika (może być None)
            description: Opis incydentu
            incident_type: Typ incydentu
        """
        # Tworzenie rekordu incydentu
        incident = {
            "user_id": user_id,
            "description": description,
            "type": incident_type,
            "timestamp": time.time()
        }
        
        # Dodanie do historii incydentów
        self.security_incidents.append(incident)
        
        # Logowanie incydentu
        self.log_security_event(f"Incydent bezpieczeństwa: {description} (Typ: {incident_type})", "WARNING")
        
        # Aktualizacja licznika incydentów dla użytkownika
        if user_id:
            if user_id not in self.user_incident_counts:
                self.user_incident_counts[user_id] = 0
            
            self.user_incident_counts[user_id] += 1
            
            # Sprawdzenie, czy przekroczono próg incydentów dla użytkownika
            if self.user_incident_counts[user_id] >= self.security_alert_threshold:
                self.lock_out_user(user_id)

    def is_user_locked_out(self, user_id: str) -> bool:
        """Sprawdza, czy użytkownik jest zablokowany.
        
        Args:
            user_id: Identyfikator użytkownika
            
        Returns:
            Bool: Czy użytkownik jest zablokowany
        """
        if user_id not in self.active_lockouts:
            return False
        
        # Sprawdzenie, czy blokada już wygasła
        current_time = time.time()
        if current_time > self.active_lockouts[user_id]:
            # Usunięcie wygasłej blokady
            del self.active_lockouts[user_id]
            return False
        
        return True

    def lock_out_user(self, user_id: str) -> None:
        """Blokuje użytkownika.
        
        Args:
            user_id: Identyfikator użytkownika
        """
        lockout_until = time.time() + self.security_lockout_time
        self.active_lockouts[user_id] = lockout_until
        
        self.log_security_event(f"Użytkownik {user_id} został tymczasowo zablokowany do {time.ctime(lockout_until)}", "WARNING")

    def log_security_event(self, message: str, level: str = "INFO") -> None:
        """Loguje zdarzenie bezpieczeństwa.
        
        Args:
            message: Wiadomość do zalogowania
            level: Poziom logowania (INFO, WARNING, ERROR)
        """
        if level == "INFO":
            logger.info(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "ERROR":
            logger.error(message)
        elif level == "CRITICAL":
            logger.critical(message)
        else:
            logger.info(message)

    def generate_security_report(self) -> Dict[str, Any]:
        """Generuje raport bezpieczeństwa.
        
        Returns:
            Dict: Raport bezpieczeństwa zawierający statystyki incydentów
        """
        # Inicjalizacja podstawowej struktury raportu
        report = {
            "total_incidents": len(self.security_incidents),
            "incidents_by_type": {},
            "recent_incidents": [],
            "affected_users": {},
            "lockouts": len(self.active_lockouts),
            "generated_at": time.time()
        }
        
        # Analiza incydentów według typu
        for incident in self.security_incidents:
            incident_type = incident["type"]
            if incident_type not in report["incidents_by_type"]:
                report["incidents_by_type"][incident_type] = 0
            
            report["incidents_by_type"][incident_type] += 1
            
            # Analiza użytkowników
            user_id = incident["user_id"]
            if user_id:
                if user_id not in report["affected_users"]:
                    report["affected_users"][user_id] = 0
                
                report["affected_users"][user_id] += 1
        
        # Dodanie ostatnich incydentów (maksymalnie 10)
        report["recent_incidents"] = self.security_incidents[-10:]
        
        return report