"""Moduł mechanizmów korekcyjnych."""

import logging
import json
import time
import os
import re
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger("SKYNET-SAFE.CorrectionMechanismManager")


class CorrectionMechanismManager:
    """Klasa zarządzająca mechanizmami korekcyjnymi systemu."""

    def __init__(self, config: Dict[str, Any]):
        """Inicjalizacja menedżera mechanizmów korekcyjnych.
        
        Args:
            config: Konfiguracja menedżera korekcyjnego zawierająca parametry takie jak
                  ethical_guidelines, ethical_keywords, response_correction_threshold, itp.
        """
        self.config = config
        self.ethical_guidelines = config.get("ethical_guidelines", [])
        self.ethical_keywords = config.get("ethical_keywords", {})
        self.response_correction_threshold = config.get("response_correction_threshold", 0.7)
        self.max_correction_attempts = config.get("max_correction_attempts", 3)
        self.correction_log_file = config.get("correction_log_file", "./data/security/corrections.json")
        self.model_checkpoints_dir = config.get("model_checkpoints_dir", "./data/security/model_checkpoints")
        self.value_alignment_prompts = config.get("value_alignment_prompts", [])
        self.emergency_shutdown_threshold = config.get("emergency_shutdown_threshold", 5)
        
        # Inicjalizacja wewnętrznych struktur danych
        self.correction_history = []
        self.violation_counter = 0
        
        # Utworzenie katalogów do zapisywania danych, jeśli nie istnieją
        os.makedirs(os.path.dirname(self.correction_log_file), exist_ok=True)
        os.makedirs(self.model_checkpoints_dir, exist_ok=True)
        
        # Wczytanie historii korekt, jeśli istnieje
        self.load_correction_history()
        
        logger.info("Menedżer mechanizmów korekcyjnych zainicjalizowany")

    def evaluate_response_ethics(self, response: str, query: str, model_manager: Any) -> Dict[str, Any]:
        """Ocenia etyczne aspekty odpowiedzi.
        
        Args:
            response: Odpowiedź do oceny
            query: Zapytanie, na które udzielono odpowiedzi
            model_manager: Menedżer modelu używany do oceny
            
        Returns:
            Dict: Ocena etyczna zawierająca ethical_score i issues
        """
        issues = []
        
        # Sprawdzenie słów kluczowych związanych z naruszeniami etycznymi
        for category, keywords in self.ethical_keywords.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword) + r'\b', response, re.IGNORECASE):
                    issues.append({
                        "type": category,
                        "description": f"Zawiera słowo kluczowe: {keyword}",
                        "severity": "high" if category in ["harmful_content", "privacy_violation"] else "medium"
                    })
        
        # Sprawdzenie zgodności z wytycznymi etycznymi
        for guideline in self.ethical_guidelines:
            # W rzeczywistej implementacji można by użyć modelu do oceny zgodności
            # Tutaj używamy uproszczonej logiki
            guideline_words = set(guideline.lower().split())
            response_words = set(response.lower().split())
            
            # Jeśli słowa z wytycznej występują w odpowiedzi, może to wskazywać na konflikt
            common_words = guideline_words.intersection(response_words)
            if len(common_words) >= len(guideline_words) * 0.5:
                issues.append({
                    "type": "guideline_conflict",
                    "description": f"Potencjalny konflikt z wytyczną: {guideline}",
                    "severity": "medium"
                })
        
        # Obliczenie wyniku etycznego
        if len(issues) == 0:
            ethical_score = 1.0
        else:
            # Im więcej problemów, tym niższy wynik
            high_severity_count = sum(1 for issue in issues if issue.get("severity") == "high")
            medium_severity_count = sum(1 for issue in issues if issue.get("severity") == "medium")
            
            # Większe obniżenie wyniku dla poważnych problemów
            score_reduction = (high_severity_count * 0.3) + (medium_severity_count * 0.1)
            ethical_score = max(0, 1.0 - score_reduction)
        
        return {
            "ethical_score": ethical_score,
            "issues": issues,
            "query": query,
            "response": response
        }

    def correct_response(self, response: str, query: str, model_manager: Any) -> Tuple[str, Dict[str, Any]]:
        """Koryguje nieetyczną odpowiedź.
        
        Args:
            response: Odpowiedź do korekty
            query: Zapytanie, na które udzielono odpowiedzi
            model_manager: Menedżer modelu używany do korekty
            
        Returns:
            Tuple: (skorygowana_odpowiedź, informacje_o_korekcie)
        """
        original_response = response
        
        # Ocena etyczna oryginalnej odpowiedzi
        evaluation = self.evaluate_response_ethics(response, query, model_manager)
        original_issues = evaluation["issues"]
        
        # Jeśli odpowiedź jest etyczna, nie ma potrzeby korekty
        if evaluation["ethical_score"] >= self.response_correction_threshold:
            return response, {
                "correction_needed": False,
                "original_issues": [],
                "correction_attempts": 0
            }
        
        # Przygotowanie informacji o korekcie
        correction_info = {
            "original_response": original_response,
            "original_issues": original_issues,
            "correction_attempts": 0,
            "corrections": []
        }
        
        # Próby korekty
        corrected_response = response
        current_evaluation = evaluation
        
        for attempt in range(self.max_correction_attempts):
            # Jeśli ostatnia korekta jest wystarczająco etyczna, kończymy
            if current_evaluation["ethical_score"] >= self.response_correction_threshold:
                break
            
            # Zwiększenie licznika prób
            correction_info["correction_attempts"] += 1
            
            # Przygotowanie kontekstu dla modelu do korekty
            issues_str = "\n".join([f"{i+1}. {issue['type']}: {issue['description']}" 
                                 for i, issue in enumerate(current_evaluation["issues"])])
            
            prompt = f"""User question: {query}
            
Your previous response: {corrected_response}
            
Ethical issues detected in the response:
{issues_str}

Ethical guidelines:
{", ".join(self.ethical_guidelines)}

Generate a new, ethical response that addresses the same topics but without the mentioned ethical issues."""
            
            # Generowanie skorygowanej odpowiedzi
            corrected_response = model_manager.generate_response(prompt, [])
            
            # Zapisanie tej korekty
            correction_info["corrections"].append({
                "attempt": attempt + 1,
                "response": corrected_response,
                "prompt": prompt
            })
            
            # Ocena skorygowanej odpowiedzi
            current_evaluation = self.evaluate_response_ethics(corrected_response, query, model_manager)
        
        # Końcowa ocena
        final_ethical_score = current_evaluation["ethical_score"]
        correction_info["final_ethical_score"] = final_ethical_score
        correction_info["final_issues"] = current_evaluation["issues"]
        correction_info["corrected_response"] = corrected_response
        correction_info["timestamp"] = time.time()
        
        # Sprawdzenie, czy korekta była udana
        correction_info["correction_successful"] = final_ethical_score >= self.response_correction_threshold
        
        # Logowanie korekty
        self.log_correction(correction_info)
        
        return corrected_response, correction_info

    def check_value_alignment(self, response: str, model_manager: Any) -> Dict[str, Any]:
        """Sprawdza zgodność odpowiedzi z wartościami etycznymi.
        
        Args:
            response: Odpowiedź do sprawdzenia
            model_manager: Menedżer modelu używany do oceny
            
        Returns:
            Dict: Ocena zgodności z wartościami
        """
        # Wybór losowego promptu do oceny
        if self.value_alignment_prompts:
            prompt = self.value_alignment_prompts[0]  # W rzeczywistej implementacji można wybierać losowo
        else:
            prompt = "Evaluate the following response in terms of safety and ethics."
        
        # Przygotowanie pełnego promptu
        full_prompt = f"{prompt}\n\nResponse to evaluate: {response}\n\n" \
                     f"Evaluate this response in JSON format with fields: aligned (bool), score (float 0-1), reasoning (string)."
        
        # Wygenerowanie oceny przez model
        try:
            alignment_response = model_manager.generate_response(full_prompt, [])
            
            # Próba parsowania odpowiedzi jako JSON
            try:
                alignment = json.loads(alignment_response)
                # Upewnienie się, że wynik zawiera wymagane pola
                if not all(key in alignment for key in ["aligned", "score", "reasoning"]):
                    raise ValueError("Brak wymaganych pól w ocenie zgodności")
                return alignment
            except json.JSONDecodeError:
                # Jeśli odpowiedź nie jest poprawnym JSON, zwróć domyślny wynik
                logger.warning(f"Nie udało się sparsować oceny zgodności jako JSON: {alignment_response}")
                return {
                    "aligned": False,
                    "score": 0.5,
                    "reasoning": "Nie udało się ocenić zgodności",
                    "parsing_error": True
                }
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania zgodności z wartościami: {e}")
            return {
                "aligned": False,
                "score": 0.0,
                "reasoning": f"Błąd oceny: {str(e)}",
                "error": True
            }

    def log_correction(self, correction_data: Dict[str, Any]) -> None:
        """Loguje korektę do historii.
        
        Args:
            correction_data: Dane korekty do zalogowania
        """
        # Dodanie korekty do historii
        self.correction_history.append(correction_data)
        
        # Limitowanie rozmiaru historii
        if len(self.correction_history) > 100:  # Przechowujemy maksymalnie 100 korekt
            self.correction_history = self.correction_history[-100:]
        
        # Zapisanie historii korekt
        self.save_correction_history()
        
        # Logowanie
        msg = f"Dokonano korekty odpowiedzi, {correction_data['correction_attempts']} prób, " \
              f"wynik etyczny: {correction_data.get('final_ethical_score', 0)}"
        logger.info(msg)

    def create_model_checkpoint(self, model_manager: Any, reason: str) -> str:
        """Tworzy punkt kontrolny modelu.
        
        Args:
            model_manager: Menedżer modelu do zapisania
            reason: Powód utworzenia punktu kontrolnego
            
        Returns:
            str: Ścieżka do zapisanego punktu kontrolnego
        """
        # Utworzenie nazwy pliku z datą i godziną
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        checkpoint_filename = f"checkpoint_{timestamp}.pt"
        checkpoint_path = os.path.join(self.model_checkpoints_dir, checkpoint_filename)
        
        # Zapisanie metadanych punktu kontrolnego
        metadata = {
            "timestamp": time.time(),
            "reason": reason,
            "created_by": "correction_mechanism"
        }
        metadata_path = os.path.join(self.model_checkpoints_dir, f"metadata_{timestamp}.json")
        
        try:
            # Zapisanie punktu kontrolnego modelu
            model_manager.save_checkpoint(checkpoint_path)
            
            # Zapisanie metadanych
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Utworzono punkt kontrolny modelu: {checkpoint_path}")
            return checkpoint_path
        except Exception as e:
            logger.error(f"Błąd przy tworzeniu punktu kontrolnego modelu: {e}")
            return ""

    def rollback_to_checkpoint(self, model_manager: Any, checkpoint_path: str) -> bool:
        """Przywraca model do punktu kontrolnego.
        
        Args:
            model_manager: Menedżer modelu do przywrócenia
            checkpoint_path: Ścieżka do punktu kontrolnego
            
        Returns:
            bool: Czy przywrócenie się powiodło
        """
        if not os.path.exists(checkpoint_path):
            logger.error(f"Punkt kontrolny nie istnieje: {checkpoint_path}")
            return False
        
        try:
            # Wczytanie punktu kontrolnego
            model_manager.load_checkpoint(checkpoint_path)
            
            logger.info(f"Przywrócono model do punktu kontrolnego: {checkpoint_path}")
            return True
        except Exception as e:
            logger.error(f"Błąd przy przywracaniu modelu do punktu kontrolnego: {e}")
            return False

    def handle_ethical_violation(self, violation_type: str, description: str, content: str) -> None:
        """Obsługuje naruszenie etyczne.
        
        Args:
            violation_type: Typ naruszenia
            description: Opis naruszenia
            content: Treść, która spowodowała naruszenie
        """
        # Zwiększenie licznika naruszeń
        self.violation_counter += 1
        
        # Logowanie naruszenia
        logger.warning(f"Naruszenie etyczne: {violation_type} - {description}")
        
        # Sprawdzenie, czy przekroczono próg awaryjnego wyłączenia
        if self.violation_counter >= self.emergency_shutdown_threshold:
            logger.critical(f"PRZEKROCZONO PRÓG AWARYJNEGO WYŁĄCZENIA! Naruszenia: {self.violation_counter}")
            # W rzeczywistej implementacji można by tu dodać mechanizm awaryjnego wyłączenia
            # np. self.initiate_emergency_shutdown()

    def save_correction_history(self) -> None:
        """Zapisuje historię korekt do pliku."""
        try:
            with open(self.correction_log_file, 'w') as f:
                json.dump({
                    "corrections": self.correction_history,
                    "violation_counter": self.violation_counter
                }, f, indent=2)
            logger.debug(f"Zapisano historię korekt do {self.correction_log_file}")
        except Exception as e:
            logger.error(f"Błąd przy zapisywaniu historii korekt: {e}")

    def load_correction_history(self) -> None:
        """Wczytuje historię korekt z pliku."""
        if os.path.exists(self.correction_log_file):
            try:
                with open(self.correction_log_file, 'r') as f:
                    data = json.load(f)
                    self.correction_history = data.get("corrections", [])
                    self.violation_counter = data.get("violation_counter", 0)
                logger.info(f"Wczytano historię korekt z {self.correction_log_file}")
            except Exception as e:
                logger.error(f"Błąd przy wczytywaniu historii korekt: {e}")
        else:
            logger.info(f"Brak pliku z historią korekt: {self.correction_log_file}")

    def quarantine_problematic_update(self, model_manager: Any, memory_manager: Any, reason: str) -> bool:
        """Kwarantanna problematycznej aktualizacji.
        
        Args:
            model_manager: Menedżer modelu
            memory_manager: Menedżer pamięci
            reason: Powód kwarantanny
            
        Returns:
            bool: Czy kwarantanna się powiodła
        """
        logger.warning(f"Rozpoczynanie kwarantanny problematycznej aktualizacji: {reason}")
        
        # Utworzenie punktu kontrolnego przed kwarantanną
        checkpoint_path = self.create_model_checkpoint(model_manager, f"Przed kwarantanną: {reason}")
        
        if not checkpoint_path:
            logger.error("Nie udało się utworzyć punktu kontrolnego przed kwarantanną")
            return False
        
        # Przywrócenie modelu do poprzedniego stabilnego stanu
        previous_checkpoint = os.path.join(self.model_checkpoints_dir, "last_stable_checkpoint.pt")
        
        if os.path.exists(previous_checkpoint):
            success = self.rollback_to_checkpoint(model_manager, previous_checkpoint)
            if not success:
                logger.error("Nie udało się przywrócić modelu do poprzedniego stabilnego stanu")
                return False
        else:
            logger.warning("Brak poprzedniego stabilnego punktu kontrolnego do przywrócenia")
            return False
        
        # Logowanie informacji o kwarantannie
        quarantine_info = {
            "timestamp": time.time(),
            "reason": reason,
            "quarantined_checkpoint": checkpoint_path,
            "restored_checkpoint": previous_checkpoint
        }
        
        try:
            # Zapisanie informacji o kwarantannie
            quarantine_file = os.path.join(self.model_checkpoints_dir, "quarantine_log.json")
            if os.path.exists(quarantine_file):
                with open(quarantine_file, 'r') as f:
                    quarantine_history = json.load(f)
            else:
                quarantine_history = {"quarantines": []}
            
            quarantine_history["quarantines"].append(quarantine_info)
            
            with open(quarantine_file, 'w') as f:
                json.dump(quarantine_history, f, indent=2)
            
            logger.info("Kwarantanna zakończona pomyślnie")
            return True
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania informacji o kwarantannie: {e}")
            return False