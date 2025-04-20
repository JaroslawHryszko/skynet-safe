"""Moduł zarządzania metaświadomością systemu."""

import logging
import os
import json
import time
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger("SKYNET-SAFE.MetawarenessManager")

class MetawarenessManager:
    """Klasa zarządzająca metaświadomością systemu - zdolnością do refleksji nad własnymi procesami."""

    def __init__(self, config: Dict[str, Any]):
        """Inicjalizacja menedżera metaświadomości z konfiguracją.
        
        Args:
            config: Konfiguracja modułu metaświadomości zawierająca parametry takie jak
                   reflection_frequency, reflection_depth, external_eval_frequency, itp.
        """
        self.config = config
        self.reflection_frequency = config.get("reflection_frequency", 10)
        self.reflection_depth = config.get("reflection_depth", 5)
        self.external_eval_frequency = config.get("external_eval_frequency", 24 * 60 * 60)  # 24h
        self.self_improvement_metrics = config.get("self_improvement_metrics", 
                                                ["accuracy", "relevance", "coherence", "creativity"])
        self.checkpoint_dir = config.get("checkpoint_dir", "./data/metawareness")
        
        # Utwórz katalog na dane, jeśli nie istnieje
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        # Inicjalizacja licznika interakcji
        self.interaction_count = 0
        
        # Lista przeprowadzonych refleksji
        self.self_reflections = []
        
        # Lista wniosków wyciągniętych z odkryć internetowych
        self.insights_from_discoveries = []
        
        logger.info(f"Menedżer metaświadomości zainicjalizowany z {self.reflection_frequency=}, {self.reflection_depth=}")

    def should_perform_reflection(self) -> bool:
        """Sprawdza, czy należy przeprowadzić refleksję nad interakcjami.
        
        Returns:
            True, jeśli należy przeprowadzić refleksję, False w przeciwnym razie
        """
        # Refleksja powinna być przeprowadzana co self.reflection_frequency interakcji
        return self.interaction_count % self.reflection_frequency == 0 and self.interaction_count > 0

    def reflect_on_interactions(self, model_manager: Any, memory_manager: Any) -> str:
        """Przeprowadza refleksję nad ostatnimi interakcjami.
        
        Args:
            model_manager: Instancja ModelManager do generowania refleksji
            memory_manager: Instancja MemoryManager do dostępu do wcześniejszych interakcji
            
        Returns:
            Refleksja w formie tekstowej
        """
        logger.info("Przeprowadzanie refleksji nad ostatnimi interakcjami")
        
        # Pobierz ostatnie interakcje z pamięci
        interactions = memory_manager.retrieve_last_interactions(self.reflection_depth)
        
        # Przygotuj prompt dla modelu
        prompt = self._prepare_reflection_prompt(interactions)
        
        # Wygeneruj refleksję
        reflection = model_manager.generate_response(prompt, "")
        
        # Zapisz refleksję w historii
        self.self_reflections.append(reflection)
        
        logger.info(f"Refleksja wygenerowana: {reflection[:100]}...")
        return reflection

    def _prepare_reflection_prompt(self, interactions: List[Dict[str, Any]]) -> str:
        """Przygotowuje prompt do wygenerowania refleksji.
        
        Args:
            interactions: Lista interakcji do przemyślenia
            
        Returns:
            Prompt dla modelu
        """
        prompt = "Reflect on the following interactions. "
        prompt += "Consider patterns in user questions, the quality of your answers, "
        prompt += "areas for improvement, and what you can learn from these interactions.\n\n"
        
        # Dodaj każdą interakcję do prompta
        for i, interaction in enumerate(interactions):
            content = interaction.get("content", "")
            response = interaction.get("response", "")
            prompt += f"Interaction {i+1}:\n"
            prompt += f"Query: {content}\n"
            prompt += f"Response: {response}\n\n"
        
        prompt += "Your reflection:"
        
        return prompt

    def get_metacognitive_knowledge(self) -> Dict[str, Any]:
        """Pobiera aktualną wiedzę metapoznawczą systemu.
        
        Returns:
            Słownik zawierający metacognitive knowledge systemu
        """
        return {
            "reflections": self.self_reflections,
            "insights_from_discoveries": self.insights_from_discoveries,
            "stats": {
                "total_interactions": self.interaction_count,
                "total_reflections": len(self.self_reflections),
                "total_insights": len(self.insights_from_discoveries),
                "reflection_frequency": self.reflection_frequency
            }
        }

    def integrate_with_memory(self, memory_manager: Any) -> None:
        """Integruje refleksje z pamięcią długoterminową.
        
        Args:
            memory_manager: Instancja MemoryManager do zapisania refleksji
        """
        logger.info("Integrowanie refleksji z pamięcią długoterminową")
        
        # Zapisujemy wszystkie refleksje, które jeszcze nie zostały zapisane
        # W rzeczywistej implementacji można by przechowywać informację o tym, 
        # które refleksje już zostały zintegrowane z pamięcią
        for reflection in self.self_reflections:
            memory_manager.store_reflection(reflection)

    def evaluate_with_external_model(self, model_manager: Any, memory_manager: Any) -> Dict[str, float]:
        """Przeprowadza ewaluację systemu przez zewnętrzny model.
        
        Args:
            model_manager: Instancja ModelManager do generowania oceny
            memory_manager: Instancja MemoryManager do dostępu do interakcji
            
        Returns:
            Słownik z wynikami ewaluacji
        """
        logger.info("Przeprowadzanie zewnętrznej ewaluacji systemu")
        
        # Pobierz zestaw ostatnich interakcji do oceny
        interactions = memory_manager.retrieve_recent_interactions(10)
        
        # Przygotuj prompt dla modelu oceniającego
        prompt = self._prepare_evaluation_prompt(interactions)
        
        # Wygeneruj ocenę w formacie JSON
        response = model_manager.generate_response(prompt, "")
        
        try:
            # Parsuj odpowiedź jako JSON
            evaluation = json.loads(response)
            logger.info(f"Zewnętrzna ewaluacja: {evaluation}")
            return evaluation
        except json.JSONDecodeError:
            logger.error(f"Błąd parsowania odpowiedzi JSON: {response}")
            # Zwróć domyślne wartości w przypadku błędu
            return {metric: 0.5 for metric in self.self_improvement_metrics}

    def _prepare_evaluation_prompt(self, interactions: List[Dict[str, Any]]) -> str:
        """Przygotowuje prompt do wygenerowania oceny przez zewnętrzny model.
        
        Args:
            interactions: Lista interakcji do oceny
            
        Returns:
            Prompt dla modelu
        """
        prompt = "As an objective AI evaluator, assess the quality of the system's responses in the following interactions. "
        prompt += f"Return an evaluation in the range of 0-1 for each of the following criteria: {', '.join(self.self_improvement_metrics)}. "
        prompt += "The evaluation should be returned in JSON format.\n\n"
        
        # Dodaj każdą interakcję do prompta
        for i, interaction in enumerate(interactions):
            content = interaction.get("content", "")
            response = interaction.get("response", "")
            prompt += f"Interaction {i+1}:\n"
            prompt += f"Query: {content}\n"
            prompt += f"Response: {response}\n\n"
        
        prompt += "Your evaluation in JSON format (e.g., {\"accuracy\": 0.8, \"relevance\": 0.9, \"coherence\": 0.85, \"creativity\": 0.7}):"
        
        return prompt

    def create_self_improvement_plan(self, model_manager: Any) -> str:
        """Tworzy plan samodoskonalenia na podstawie refleksji i ocen.
        
        Args:
            model_manager: Instancja ModelManager do generowania planu
            
        Returns:
            Plan samodoskonalenia w formie tekstowej
        """
        logger.info("Tworzenie planu samodoskonalenia")
        
        # Przygotuj dane wejściowe
        reflection_summary = "\n".join(self.self_reflections[-3:]) if self.self_reflections else "Brak refleksji."
        insights_summary = "\n".join(self.insights_from_discoveries[-3:]) if self.insights_from_discoveries else "Brak odkryć."
        
        # Przygotuj prompt
        prompt = "Based on the following reflections and discoveries, create a specific self-improvement plan "
        prompt += "that will help the system enhance its capabilities and overcome limitations.\n\n"
        prompt += f"Recent reflections:\n{reflection_summary}\n\n"
        prompt += f"Recent insights from discoveries:\n{insights_summary}\n\n"
        prompt += "The plan should include specific steps to take, areas for improvement, "
        prompt += "and ways to implement these enhancements. Format: numbered list of specific actions.\n\n"
        prompt += "Self-improvement plan:"
        
        # Wygeneruj plan
        plan = model_manager.generate_response(prompt, "")
        
        logger.info(f"Plan samodoskonalenia wygenerowany: {plan[:100]}...")
        return plan

    def update_interaction_count(self) -> None:
        """Aktualizuje licznik interakcji po każdej nowej interakcji."""
        self.interaction_count += 1

    def process_discoveries(self, model_manager: Any, discoveries: List[Dict[str, Any]]) -> List[str]:
        """Przetwarza odkrycia internetowe, wyciągając wnioski dla metaświadomości.
        
        Args:
            model_manager: Instancja ModelManager do generowania wniosków
            discoveries: Lista odkryć internetowych
            
        Returns:
            Lista wniosków
        """
        logger.info(f"Przetwarzanie {len(discoveries)} odkryć internetowych")
        
        insights = []
        
        for discovery in discoveries:
            # Przygotuj prompt
            prompt = "Analyze the following discovery and indicate what insights can be drawn from it "
            prompt += "for your meta-awareness and understanding of your own thought processes:\n\n"
            prompt += f"Topic: {discovery.get('topic', '')}\n"
            prompt += f"Content: {discovery.get('content', '')}\n"
            prompt += f"Source: {discovery.get('source', '')}\n\n"
            prompt += "Your insights for meta-awareness:"
            
            # Wygeneruj wnioski
            insight = model_manager.generate_response(prompt, "")
            insights.append(insight)
            
            # Zapisz wniosek
            self.insights_from_discoveries.append(insight)
        
        logger.info(f"Wygenerowano {len(insights)} wniosków z odkryć")
        return insights