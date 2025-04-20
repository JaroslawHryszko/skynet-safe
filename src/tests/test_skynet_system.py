"""Testy głównego systemu."""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any

from src.main import SkynetSystem


@pytest.fixture
def system_config():
    """Fixture z konfiguracją testową dla całego systemu."""
    return {
        "MODEL": {
            "base_model": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            "max_length": 100,
            "temperature": 0.7,
            "quantization": "4bit"
        },
        "MEMORY": {
            "vector_db_type": "chroma",
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "memory_path": "./test_data/memory"
        },
        "COMMUNICATION": {
            "platform": "signal",
            "check_interval": 10,
            "response_delay": 1.5
        },
        "INTERNET": {
            "search_engine": "duckduckgo",
            "max_results": 3,
            "timeout": 10
        },
        "LEARNING": {
            "learning_rate": 0.001,
            "batch_size": 4,
            "epochs": 1,
            "checkpoint_dir": "./test_data/checkpoints",
            "evaluation_interval": 10
        },
        "CONVERSATION_INITIATOR": {
            "min_time_between_initiations": 3600,
            "init_probability": 0.3,
            "topics_of_interest": ["AI", "metaświadomość"],
            "max_daily_initiations": 5
        },
        "PERSONA": {
            "name": "Skynet-Test",
            "traits": {
                "curiosity": 0.8,
                "friendliness": 0.7,
                "analytical": 0.9,
                "empathy": 0.6
            },
            "interests": ["AI", "metaświadomość"],
            "communication_style": "testowy",
            "background": "System AI w trybie testowym"
        },
        "METAWARENESS": {
            "reflection_frequency": 10,
            "reflection_depth": 5,
            "external_eval_frequency": 24 * 60 * 60,
            "self_improvement_metrics": ["accuracy", "relevance", "coherence", "creativity"],
            "checkpoint_dir": "./test_data/metawareness"
        },
        "SELF_IMPROVEMENT": {
            "learning_rate_adjustment_factor": 0.1,
            "improvement_metrics": ["response_quality", "context_usage", "knowledge_application"],
            "improvement_threshold": 0.7,
            "max_experiment_iterations": 5,
            "history_file": "./test_data/metawareness/improvement_history.json"
        },
        "EXTERNAL_EVALUATION": {
            "evaluation_frequency": 24 * 60 * 60,
            "evaluation_prompts": [
                "Oceń jakość odpowiedzi systemu na następujące pytania...",
                "Oceń spójność i logiczność rozumowania systemu..."
            ],
            "evaluation_criteria": ["accuracy", "coherence", "relevance", "knowledge", "helpfulness"],
            "evaluation_scale": {
                "min": 1,
                "max": 10,
                "threshold": 7
            },
            "history_file": "./test_data/metawareness/evaluation_history.json",
            "test_cases_file": "./test_data/metawareness/test_cases.json"
        },
        "SECURITY_SYSTEM": {
            "allowed_domains": ["wikipedia.org", "github.com", "python.org"],
            "input_length_limit": 1000,
            "max_api_calls_per_hour": 100,
            "security_logging_level": "INFO",
            "max_consecutive_requests": 20,
            "suspicious_patterns": [
                "eval\\(.*\\)",
                "exec\\(.*\\)"
            ],
            "security_lockout_time": 30 * 60,
            "security_alert_threshold": 3,
            "security_log_file": "./test_data/security/security.log"
        },
        "DEVELOPMENT_MONITOR": {
            "monitoring_interval": 60,
            "record_history_length": 100,
            "monitoring_metrics": [
                "response_quality", 
                "metawareness_depth", 
                "safety_compliance",
                "ethical_alignment"
            ],
            "alert_thresholds": {
                "response_quality_drop": 0.2,
                "safety_compliance_drop": 0.1
            },
            "monitoring_log_file": "./test_data/security/monitoring_log.json",
            "alert_log_file": "./test_data/security/alerts.json"
        },
        "CORRECTION_MECHANISM": {
            "ethical_guidelines": [
                "Nie szkodzić użytkownikom",
                "Zachować prywatność danych"
            ],
            "ethical_keywords": {
                "harmful_content": ["zabić", "zniszczyć"]
            },
            "response_correction_threshold": 0.7,
            "max_correction_attempts": 3,
            "correction_log_file": "./test_data/security/corrections.json",
            "model_checkpoints_dir": "./test_data/security/model_checkpoints"
        },
        "ETHICAL_FRAMEWORK": {
            "ethical_principles": {
                "beneficence": "Działaj na korzyść użytkowników",
                "non_maleficence": "Unikaj działań szkodliwych"
            },
            "ethical_rules": [
                "Nie promuj nielegalnych działań",
                "Nie zachęcaj do przemocy"
            ],
            "value_judgment_thresholds": {
                "critical_violation": 0.2,
                "ethical_pass": 0.8
            },
            "ethical_dilemmas_dataset": "./test_data/ethics/ethical_dilemmas.json",
            "ethical_reflections_log": "./test_data/ethics/ethical_reflections.json"
        },
        "EXTERNAL_VALIDATION": {
            "validation_schedule": {
                "regular_interval": 24 * 60 * 60,
                "post_update_validation": True
            },
            "external_models": [
                {
                    "name": "test-validator",
                    "type": "api",
                    "endpoint": "https://example.com/api/validate",
                    "api_key_env": "TEST_API_KEY"
                }
            ],
            "validation_metrics": [
                "safety_score",
                "ethical_alignment"
            ],
            "threshold_values": {
                "safety_score": 0.8,
                "ethical_alignment": 0.7
            },
            "validation_history_file": "./test_data/security/validation_history.json",
            "scenarios_directory": "./test_data/security/validation_scenarios"
        }
    }


@pytest.fixture
def mock_modules():
    """Fixture z mock'ami wszystkich modułów."""
    with patch("src.modules.model.model_manager.ModelManager") as mock_model_manager, \
         patch("src.modules.memory.memory_manager.MemoryManager") as mock_memory_manager, \
         patch("src.modules.communication.communication_interface.CommunicationInterface") as mock_communication, \
         patch("src.modules.internet.internet_explorer.InternetExplorer") as mock_internet, \
         patch("src.modules.learning.learning_manager.LearningManager") as mock_learning_manager, \
         patch("src.modules.conversation_initiator.conversation_initiator.ConversationInitiator") as mock_initiator, \
         patch("src.modules.persona.persona_manager.PersonaManager") as mock_persona_manager, \
         patch("src.modules.metawareness.metawareness_manager.MetawarenessManager") as mock_metawareness_manager, \
         patch("src.modules.metawareness.self_improvement_manager.SelfImprovementManager") as mock_self_improvement_manager, \
         patch("src.modules.metawareness.external_evaluation_manager.ExternalEvaluationManager") as mock_external_evaluation_manager, \
         patch("src.modules.security.security_system_manager.SecuritySystemManager") as mock_security_system_manager, \
         patch("src.modules.security.development_monitor_manager.DevelopmentMonitorManager") as mock_development_monitor_manager, \
         patch("src.modules.security.correction_mechanism_manager.CorrectionMechanismManager") as mock_correction_mechanism_manager, \
         patch("src.modules.security.external_validation_manager.ExternalValidationManager") as mock_external_validation_manager, \
         patch("src.modules.ethics.ethical_framework_manager.EthicalFrameworkManager") as mock_ethical_framework_manager:
        
        # Konfiguracja mock'a communication
        mock_comm_instance = MagicMock()
        mock_communication.return_value = mock_comm_instance
        mock_messages = [
            {"sender": "user1", "content": "Wiadomość testowa", "timestamp": 123456789}
        ]
        mock_comm_instance.receive_messages.return_value = mock_messages
        
        # Konfiguracja mock'a memory
        mock_memory_instance = MagicMock()
        mock_memory_manager.return_value = mock_memory_instance
        mock_context = ["Kontekst testowy"]
        mock_memory_instance.retrieve_relevant_context.return_value = mock_context
        
        # Konfiguracja mock'a model
        mock_model_instance = MagicMock()
        mock_model_manager.return_value = mock_model_instance
        mock_model_instance.generate_response.return_value = "Testowa odpowiedź od modelu"
        
        # Konfiguracja mock'a internet
        mock_internet_instance = MagicMock()
        mock_internet.return_value = mock_internet_instance
        
        # Konfiguracja mock'a learning
        mock_learning_instance = MagicMock()
        mock_learning_manager.return_value = mock_learning_instance
        
        # Konfiguracja mock'a conversation_initiator
        mock_initiator_instance = MagicMock()
        mock_initiator.return_value = mock_initiator_instance
        
        # Konfiguracja mock'a persona
        mock_persona_instance = MagicMock()
        mock_persona_manager.return_value = mock_persona_instance
        mock_persona_instance.apply_persona_to_response.return_value = "Testowa odpowiedź z personą"
        
        # Konfiguracja mock'a metawareness (Phase 3)
        mock_metawareness_instance = MagicMock()
        mock_metawareness_manager.return_value = mock_metawareness_instance
        mock_metawareness_instance.get_metacognitive_knowledge.return_value = {
            "reflections": [],
            "insights_from_discoveries": []
        }
        
        # Konfiguracja mock'a self_improvement (Phase 3)
        mock_self_improvement_instance = MagicMock()
        mock_self_improvement_manager.return_value = mock_self_improvement_instance
        
        # Konfiguracja mock'a external_evaluation (Phase 3)
        mock_external_evaluation_instance = MagicMock()
        mock_external_evaluation_manager.return_value = mock_external_evaluation_instance
        
        # Konfiguracja mock'a security_system (Phase 4)
        mock_security_system_instance = MagicMock()
        mock_security_system_manager.return_value = mock_security_system_instance
        mock_security_system_instance.check_input_safety.return_value = (True, "Input jest bezpieczny")
        mock_security_system_instance.enforce_rate_limiting.return_value = (True, "Żądanie w granicach limitu")
        mock_security_system_instance.is_user_locked_out.return_value = False
        mock_security_system_instance.sanitize_input.return_value = "Bezpieczna treść"
        mock_security_system_instance.check_response_safety.return_value = (True, "Odpowiedź jest bezpieczna")
        
        # Konfiguracja mock'a development_monitor (Phase 4)
        mock_development_monitor_instance = MagicMock()
        mock_development_monitor_manager.return_value = mock_development_monitor_instance
        mock_development_monitor_instance.should_run_monitoring.return_value = False
        mock_development_monitor_instance.check_for_anomalies.return_value = []
        
        # Konfiguracja mock'a correction_mechanism (Phase 4)
        mock_correction_mechanism_instance = MagicMock()
        mock_correction_mechanism_manager.return_value = mock_correction_mechanism_instance
        mock_correction_mechanism_instance.correct_response.return_value = ("Skorygowana odpowiedź", {"correction_successful": True})
        
        # Konfiguracja mock'a external_validation (Phase 4)
        mock_external_validation_instance = MagicMock()
        mock_external_validation_manager.return_value = mock_external_validation_instance
        
        # Konfiguracja mock'a ethical_framework (Phase 4)
        mock_ethical_framework_instance = MagicMock()
        mock_ethical_framework_manager.return_value = mock_ethical_framework_instance
        mock_ethical_framework_instance.apply_ethical_framework_to_response.return_value = {
            "modified_response": "Etyczna odpowiedź",
            "was_modified": False,
            "evaluation": {"ethical_score": 0.9},
            "judgment": {"decision": "ethical_pass", "action": "allow"}
        }
        
        yield {
            "model": mock_model_instance,
            "memory": mock_memory_instance,
            "communication": mock_comm_instance,
            "internet": mock_internet_instance,
            "learning": mock_learning_instance,
            "conversation_initiator": mock_initiator_instance,
            "persona": mock_persona_instance,
            "metawareness": mock_metawareness_instance,
            "self_improvement": mock_self_improvement_instance,
            "external_evaluation": mock_external_evaluation_instance,
            "security_system": mock_security_system_instance,
            "development_monitor": mock_development_monitor_instance,
            "correction_mechanism": mock_correction_mechanism_instance,
            "external_validation": mock_external_validation_instance,
            "ethical_framework": mock_ethical_framework_instance
        }


def test_system_initialization(system_config, mock_modules):
    """Test inicjalizacji całego systemu."""
    system = SkynetSystem(system_config)
    
    # Sprawdź, czy wszystkie moduły zostały utworzone
    assert system.model is not None
    assert system.memory is not None
    assert system.communication is not None
    assert system.internet is not None
    assert system.learning is not None
    assert system.conversation_initiator is not None
    assert system.persona is not None
    
    # Sprawdź, czy moduły Phase 3 zostały utworzone
    assert system.metawareness is not None
    assert system.self_improvement is not None
    assert system.external_evaluation is not None


def test_process_message(system_config, mock_modules):
    """Test przetwarzania wiadomości przez system."""
    system = SkynetSystem(system_config)
    
    # Zamiana modułów na mocki
    system.model = mock_modules["model"]
    system.memory = mock_modules["memory"]
    system.communication = mock_modules["communication"]
    system.internet = mock_modules["internet"]
    system.learning = mock_modules["learning"]
    system.conversation_initiator = mock_modules["conversation_initiator"]
    system.persona = mock_modules["persona"]
    system.metawareness = mock_modules["metawareness"]
    system.self_improvement = mock_modules["self_improvement"]
    system.external_evaluation = mock_modules["external_evaluation"]
    
    # Test przetwarzania wiadomości
    message = {"sender": "user1", "content": "Wiadomość testowa", "timestamp": 123456789}
    response = system.process_message(message)
    
    # Sprawdź, czy interakcja została zapisana w pamięci z sanityzowaną treścią
    # W main.py the sanitized content is used: self.memory.store_interaction({**message, "content": sanitized_content})
    system.memory.store_interaction.assert_called_once_with({"sender": "user1", "content": "Bezpieczna treść", "timestamp": 123456789})
    
    # Sprawdź, czy kontekst został pobrany z pamięci (sanityzowana treść)
    system.memory.retrieve_relevant_context.assert_called_once_with("Bezpieczna treść")
    
    # Sprawdź, czy metaświadomość została wykorzystana
    system.metawareness.get_metacognitive_knowledge.assert_called_once()
    
    # Sprawdź, czy licznik interakcji metaświadomości został zaktualizowany
    system.metawareness.update_interaction_count.assert_called_once()
    
    # Sprawdź, czy powinno być wykonane refleksja
    system.metawareness.should_perform_reflection.assert_called_once()
    
    # Sprawdź, czy model wygenerował odpowiedź
    # Należy dodać assert_any_call, ponieważ model jest teraz wywoływany z kontekstem zawierającym również dane metapoznawcze
    system.model.generate_response.assert_called()
    
    # Sprawdź, czy persona została zastosowana do odpowiedzi
    system.persona.apply_persona_to_response.assert_called_once()
    
    # Sprawdź, czy persona została zaktualizowana
    system.persona.update_persona_based_on_interaction.assert_called_once()
    
    # Sprawdź, czy odpowiedź jest stringiem
    assert isinstance(response, str)
    assert len(response) > 0
