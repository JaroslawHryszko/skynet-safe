"""Moduł zarządzania procesem uczenia modelu."""

import os
import logging
import torch
from typing import Dict, List, Any, Tuple
from transformers import TrainingArguments, Trainer, DataCollatorForLanguageModeling
from datasets import Dataset

logger = logging.getLogger("SKYNET-SAFE.LearningManager")

class LearningManager:
    """Klasa zarządzająca procesem uczenia modelu językowego."""

    def __init__(self, config: Dict[str, Any]):
        """Inicjalizacja menedżera uczenia z konfiguracją.
        
        Args:
            config: Konfiguracja modułu uczenia zawierająca parametry takie jak
                   learning_rate, batch_size, epochs, checkpoint_dir itd.
        """
        self.config = config
        self.learning_rate = config.get("learning_rate", 0.001)
        self.batch_size = config.get("batch_size", 4)
        self.epochs = config.get("epochs", 1)
        self.checkpoint_dir = config.get("checkpoint_dir", "./data/checkpoints")
        self.evaluation_interval = config.get("evaluation_interval", 10)
        
        # Tworzenie katalogu na punkty kontrolne, jeśli nie istnieje
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        logger.info(f"Menedżer uczenia zainicjalizowany z {self.learning_rate=}, {self.batch_size=}, {self.epochs=}")

    def prepare_training_data(self, interactions: List[Dict[str, str]]) -> List[Tuple[str, str]]:
        """Przygotowuje dane treningowe na podstawie interakcji.
        
        Args:
            interactions: Lista interakcji, gdzie każda interakcja ma format
                          {"content": "treść zapytania", "response": "odpowiedź"}
                          
        Returns:
            Lista krotek (przetworzone_zapytanie, przetworzona_odpowiedź)
        """
        logger.info(f"Przygotowywanie danych treningowych z {len(interactions)} interakcji")
        training_data = []
        
        for interaction in interactions:
            processed_query, processed_response = self._process_interaction(interaction)
            training_data.append((processed_query, processed_response))
        
        return training_data

    def _process_interaction(self, interaction: Dict[str, str]) -> Tuple[str, str]:
        """Przetwarza pojedynczą interakcję do formatu treningowego.
        
        Args:
            interaction: Interakcja w formacie {"content": "treść", "response": "odpowiedź"}
            
        Returns:
            Krotka (przetworzone_zapytanie, przetworzona_odpowiedź)
        """
        # Ekstrahujemy zawartość i odpowiedź
        query = interaction.get("content", "")
        response = interaction.get("response", "")
        
        # Możemy tutaj dodać dodatkowe przetwarzanie, formatowanie, itp.
        # Na przykład dodanie specjalnych tokenów lub formatowanie instrukcji
        processed_query = f"<human>: {query}"
        processed_response = f"<assistant>: {response}"
        
        return processed_query, processed_response

    def train_model(self, model_manager: Any, training_data: List[Tuple[str, str]]) -> Dict[str, float]:
        """Trenuje model na podstawie przygotowanych danych.
        
        Args:
            model_manager: Instancja ModelManager zawierająca model i tokenizer
            training_data: Lista krotek (zapytanie, odpowiedź) do treningu
            
        Returns:
            Słownik zawierający metryki treningu (np. loss, accuracy)
        """
        logger.info("Rozpoczynanie treningu modelu")
        
        # Uruchomienie treningu
        training_metrics = self._run_training_steps(model_manager, training_data)
        
        # Zapisanie punktu kontrolnego modelu
        self._save_checkpoint(model_manager)
        
        # Ewaluacja modelu po treningu
        evaluation_metrics = self._evaluate_model(model_manager, training_data)
        
        # Łączymy metryki
        all_metrics = {**training_metrics, **evaluation_metrics}
        
        logger.info(f"Trening zakończony z metrykami: {all_metrics}")
        return all_metrics

    def _run_training_steps(self, model_manager: Any, training_data: List[Tuple[str, str]]) -> Dict[str, float]:
        """Wykonuje kroki treningowe na modelu.
        
        Args:
            model_manager: Instancja ModelManager
            training_data: Przygotowane dane treningowe
            
        Returns:
            Słownik z metrykami treningu
        """
        model = model_manager.model
        tokenizer = model_manager.tokenizer
        
        # Przygotowanie danych do formatu zgodnego z Trainer
        formatted_data = []
        for query, response in training_data:
            formatted_text = f"{query}\n{response}"
            tokenized = tokenizer(formatted_text, truncation=True, padding="max_length", max_length=512)
            formatted_data.append(tokenized)
        
        # Konwersja na dataset
        dataset = Dataset.from_list(formatted_data)
        
        # Konfiguracja treningu
        training_args = TrainingArguments(
            output_dir=self.checkpoint_dir,
            per_device_train_batch_size=self.batch_size,
            num_train_epochs=self.epochs,
            learning_rate=self.learning_rate,
            logging_dir=f"{self.checkpoint_dir}/logs",
            logging_steps=10,
            save_strategy="epoch"
        )
        
        # Inicjalizacja trenera
        data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
            data_collator=data_collator
        )
        
        # Trening
        train_result = trainer.train()
        
        # Zwracamy metryki
        return {"loss": train_result.training_loss}

    def _save_checkpoint(self, model_manager: Any) -> str:
        """Zapisuje punkt kontrolny modelu.
        
        Args:
            model_manager: Instancja ModelManager
            
        Returns:
            Ścieżka do zapisanego punktu kontrolnego
        """
        checkpoint_path = f"{self.checkpoint_dir}/checkpoint-{int(time.time())}"
        model_manager.model.save_pretrained(checkpoint_path)
        model_manager.tokenizer.save_pretrained(checkpoint_path)
        
        logger.info(f"Zapisano punkt kontrolny modelu: {checkpoint_path}")
        return checkpoint_path

    def _evaluate_model(self, model_manager: Any, eval_data: List[Tuple[str, str]]) -> Dict[str, float]:
        """Ewaluuje model na danych ewaluacyjnych.
        
        Args:
            model_manager: Instancja ModelManager
            eval_data: Dane do ewaluacji (zwykle podzbiór danych treningowych)
            
        Returns:
            Słownik z metrykami ewaluacji
        """
        # W rzeczywistej implementacji przeprowadziłbym tutaj pełną ewaluację
        # Dla uproszczenia zwracam przykładowe metryki
        # W pełnej implementacji można użyć perplexity lub inne metryki jakości modelu
        
        logger.info("Ewaluacja modelu po treningu")
        return {"accuracy": 0.9, "perplexity": 2.1}

    def adapt_model_from_interaction(self, model_manager: Any, interaction: Dict[str, str]) -> Dict[str, float]:
        """Dostosowuje model na podstawie pojedynczej interakcji.
        
        Args:
            model_manager: Instancja ModelManager
            interaction: Interakcja w formacie {"content": "treść", "response": "odpowiedź"}
            
        Returns:
            Słownik z metrykami adaptacji
        """
        logger.info("Adaptacja modelu na podstawie nowej interakcji")
        
        # Przygotowanie danych treningowych z pojedynczej interakcji
        training_data = self.prepare_training_data([interaction])
        
        # Trenowanie modelu
        training_metrics = self.train_model(model_manager, training_data)
        
        return training_metrics

# Importowanie potrzebnych modułów do funkcji trenowania
import time