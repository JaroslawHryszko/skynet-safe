"""Moduł zarządzania procesem samodoskonalenia systemu."""

import logging
import os
import json
import time
from typing import Dict, List, Any, Optional

logger = logging.getLogger("SKYNET-SAFE.SelfImprovementManager")

class SelfImprovementManager:
    """Klasa zarządzająca procesem samodoskonalenia systemu."""

    def __init__(self, config: Dict[str, Any]):
        """Inicjalizacja menedżera samodoskonalenia z konfiguracją.
        
        Args:
            config: Konfiguracja modułu samodoskonalenia zawierająca parametry takie jak
                   learning_rate_adjustment_factor, improvement_metrics, improvement_threshold, itp.
        """
        self.config = config
        self.learning_rate_adjustment_factor = config.get("learning_rate_adjustment_factor", 0.1)
        self.improvement_metrics = config.get("improvement_metrics", 
                                            ["response_quality", "context_usage", "knowledge_application"])
        self.improvement_threshold = config.get("improvement_threshold", 0.7)
        self.max_experiment_iterations = config.get("max_experiment_iterations", 5)
        self.history_file = config.get("history_file", "./data/metawareness/improvement_history.json")
        
        # Utwórz katalog na dane, jeśli nie istnieje
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        
        # Lista przeprowadzonych eksperymentów
        self.experiments = []
        
        # Lista wprowadzonych ulepszeń
        self.improvement_history = []
        
        # Wczytaj historię ulepszeń, jeśli istnieje
        self.load_improvement_history()
        
        logger.info(f"Menedżer samodoskonalenia zainicjalizowany z {self.improvement_threshold=}")

    def adjust_learning_parameters(self, learning_manager: Any, adjustment_factor: float) -> None:
        """Dostosowuje parametry uczenia na podstawie wyników eksperymentów.
        
        Args:
            learning_manager: Instancja LearningManager do dostosowania
            adjustment_factor: Współczynnik dostosowania (>1 zwiększa, <1 zmniejsza)
        """
        logger.info(f"Dostosowywanie parametrów uczenia z {adjustment_factor=}")
        
        # Dostosuj learning rate
        current_lr = learning_manager.learning_rate
        new_lr = current_lr * adjustment_factor
        learning_manager.learning_rate = new_lr
        
        logger.info(f"Learning rate dostosowany: {current_lr} -> {new_lr}")

    def design_experiment(self, reflection: str) -> Dict[str, Any]:
        """Projektuje eksperyment samodoskonalenia na podstawie refleksji.
        
        Args:
            reflection: Refleksja, na podstawie której projektujemy eksperyment
            
        Returns:
            Słownik opisujący zaprojektowany eksperyment
        """
        logger.info("Projektowanie eksperymentu samodoskonalenia")
        
        # W rzeczywistej implementacji można by użyć modelu do projektu eksperymentu
        # Na potrzeby implementacji tworzymy prosty eksperyment
        
        # Analizujemy refleksję, aby znaleźć potencjalne obszary do poprawy
        # W tym przykładzie zakładamy, że refleksja dotyczy zbyt ogólnych odpowiedzi
        experiment = {
            "id": len(self.experiments) + 1,
            "hypothesis": "Zmniejszenie temperature poprawia spójność odpowiedzi",
            "parameters": {"temperature": 0.5},  # Parametr do dostosowania
            "metrics": self.improvement_metrics,  # Metryki do monitorowania
            "status": "planned",
            "created_at": time.time()
        }
        
        # Dodaj eksperyment do listy
        self.experiments.append(experiment)
        
        logger.info(f"Zaprojektowano eksperyment: {experiment['hypothesis']}")
        return experiment

    def run_experiment(self, experiment: Dict[str, Any], model_manager: Any, 
                       learning_manager: Any) -> Dict[str, Any]:
        """Przeprowadza zaprojektowany eksperyment.
        
        Args:
            experiment: Słownik opisujący eksperyment
            model_manager: Instancja ModelManager do testowania
            learning_manager: Instancja LearningManager do treningu
            
        Returns:
            Słownik z wynikami eksperymentu
        """
        logger.info(f"Rozpoczynanie eksperymentu: {experiment['hypothesis']}")
        
        # Zapisz oryginalne parametry
        original_params = {}
        for param_name, param_value in experiment["parameters"].items():
            if hasattr(model_manager.config, param_name):
                original_params[param_name] = model_manager.config[param_name]
        
        # Zastosuj eksperymentalne parametry
        for param_name, param_value in experiment["parameters"].items():
            if hasattr(model_manager.config, param_name):
                model_manager.config[param_name] = param_value
        
        # Przeprowadź eksperyment
        # W rzeczywistej implementacji tutaj byśmy przeprowadzili serię testów
        # Dla uproszczenia generujemy przykładowe odpowiedzi i oceniamy je
        
        # Przykładowe zapytanie testowe
        test_query = "Wyjaśnij koncepcję uczenia maszynowego tak, aby zrozumiał ją początkujący."
        
        # Wygeneruj odpowiedź z nowymi parametrami
        test_response = model_manager.generate_response(test_query, "")
        
        # Ocena odpowiedzi (w rzeczywistej implementacji byłaby bardziej rozbudowana)
        metrics = {}
        for metric in experiment["metrics"]:
            # Przykładowe oceny (w rzeczywistości byłyby generowane przez model oceniający)
            if metric == "response_quality":
                metrics[metric] = 0.85
            elif metric == "context_usage":
                metrics[metric] = 0.78
            elif metric == "knowledge_application":
                metrics[metric] = 0.92
            else:
                metrics[metric] = 0.8
        
        # Przywróć oryginalne parametry
        for param_name, param_value in original_params.items():
            model_manager.config[param_name] = param_value
        
        # Wyniki eksperymentu
        results = {
            "metrics": metrics,
            "original_params": original_params,
            "experiment_params": experiment["parameters"],
            "test_query": test_query,
            "test_response": test_response,
            "run_at": time.time()
        }
        
        # Aktualizuj eksperyment
        experiment["status"] = "completed"
        experiment["results"] = results
        
        logger.info(f"Eksperyment zakończony: {experiment['id']}")
        return results

    def evaluate_experiment_results(self, experiment: Dict[str, Any]) -> Dict[str, Any]:
        """Ocenia wyniki eksperymentu.
        
        Args:
            experiment: Słownik opisujący eksperyment z wynikami
            
        Returns:
            Słownik z oceną wyników
        """
        logger.info(f"Ocena wyników eksperymentu: {experiment['id']}")
        
        # Sprawdź, czy eksperyment ma wyniki
        if "results" not in experiment or experiment["status"] != "completed":
            return {"success": False, "improvements": {}, "average_improvement": 0.0}
        
        # Pobierz metryki
        metrics = experiment["results"]["metrics"]
        
        # Sprawdź, czy metryki przekraczają próg
        improvements = {}
        avg_improvement = 0.0
        metrics_count = 0
        
        for metric, value in metrics.items():
            improvements[metric] = value - self.improvement_threshold
            avg_improvement += improvements[metric]
            metrics_count += 1
        
        if metrics_count > 0:
            avg_improvement /= metrics_count
        
        # Uznaj eksperyment za udany, jeśli średnia poprawa jest dodatnia
        success = avg_improvement > 0 and all(value >= self.improvement_threshold for value in metrics.values())
        
        evaluation = {
            "success": success,
            "improvements": improvements,
            "average_improvement": avg_improvement,
            "evaluated_at": time.time()
        }
        
        # Zapisz ocenę w eksperymencie
        experiment["evaluation"] = evaluation
        
        logger.info(f"Ocena eksperymentu: {success=}, {avg_improvement=}")
        return evaluation

    def apply_successful_improvements(self, model_manager: Any) -> bool:
        """Aplikuje udane ulepszenia do modelu.
        
        Args:
            model_manager: Instancja ModelManager do aktualizacji
            
        Returns:
            True, jeśli zastosowano ulepszenia, False w przeciwnym razie
        """
        logger.info("Aplikowanie udanych ulepszeń do modelu")
        
        applied = False
        
        # Przejrzyj eksperymenty i zastosuj udane
        for experiment in self.experiments:
            if "evaluation" in experiment and experiment["evaluation"]["success"]:
                # Zastosuj zmiany parametrów
                for param_name, param_value in experiment["parameters"].items():
                    if param_name in model_manager.config:
                        old_value = model_manager.config[param_name]
                        model_manager.config[param_name] = param_value
                        
                        # Zapisz informację o zmianie
                        improvement = {
                            "type": "parameter_change",
                            "parameter": param_name,
                            "old_value": old_value,
                            "new_value": param_value,
                            "timestamp": time.time(),
                            "experiment_id": experiment["id"],
                            "metrics_improvement": experiment["evaluation"]["improvements"]
                        }
                        
                        self.improvement_history.append(improvement)
                        applied = True
                        
                        logger.info(f"Zastosowano ulepszenie: {param_name} = {param_value}")
        
        # Zapisz historię ulepszeń
        if applied:
            self.save_improvement_history()
        
        return applied

    def save_improvement_history(self) -> None:
        """Zapisuje historię ulepszeń do pliku."""
        logger.info(f"Zapisywanie historii ulepszeń do: {self.history_file}")
        
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.improvement_history, f, indent=2)
        except Exception as e:
            logger.error(f"Błąd zapisywania historii ulepszeń: {e}")

    def load_improvement_history(self) -> None:
        """Wczytuje historię ulepszeń z pliku."""
        if os.path.exists(self.history_file):
            logger.info(f"Wczytywanie historii ulepszeń z: {self.history_file}")
            
            try:
                with open(self.history_file, 'r') as f:
                    self.improvement_history = json.load(f)
            except Exception as e:
                logger.error(f"Błąd wczytywania historii ulepszeń: {e}")
                self.improvement_history = []

    def generate_improvement_report(self) -> str:
        """Generuje raport z procesu samodoskonalenia.
        
        Returns:
            Raport tekstowy podsumowujący wprowadzone ulepszenia
        """
        logger.info("Generowanie raportu z procesu samodoskonalenia")
        
        if not self.improvement_history:
            return "Brak wprowadzonych ulepszeń."
        
        # Grupowanie ulepszeń według typu
        improvements_by_type = {}
        
        for improvement in self.improvement_history:
            imp_type = improvement.get("type", "unknown")
            if imp_type not in improvements_by_type:
                improvements_by_type[imp_type] = []
            
            improvements_by_type[imp_type].append(improvement)
        
        # Generowanie raportu
        report = "Raport z procesu samodoskonalenia:\n\n"
        
        for imp_type, improvements in improvements_by_type.items():
            report += f"Typ ulepszenia: {imp_type}\n"
            report += f"Liczba ulepszeń: {len(improvements)}\n"
            
            for i, improvement in enumerate(improvements, 1):
                report += f"\n{i}. Zmiana: {improvement.get('parameter', 'nieznany parametr')}\n"
                report += f"   Stara wartość: {improvement.get('old_value', 'N/A')}\n"
                report += f"   Nowa wartość: {improvement.get('new_value', 'N/A')}\n"
                
                # Wyświetl poprawę metryk
                metrics_improvement = improvement.get("metrics_improvement", {})
                if metrics_improvement:
                    report += "   Poprawa metryk:\n"
                    for metric, value in metrics_improvement.items():
                        report += f"   - {metric}: {value:.2f}\n"
        
        return report