"""Main module of the SKYNET-SAFE system."""

import logging
import time
import random
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.modules.model import model_manager
from src.modules.communication import communication_interface
from src.modules.memory import memory_manager
from src.modules.internet import internet_explorer
from src.modules.learning import learning_manager
from src.modules.conversation_initiator import conversation_initiator
from src.modules.persona import persona_manager
from src.modules.metawareness import metawareness_manager
from src.modules.metawareness import self_improvement_manager
from src.modules.metawareness import external_evaluation_manager
from src.modules.security import security_system_manager
from src.modules.security import development_monitor_manager
from src.modules.security import correction_mechanism_manager
from src.modules.security import external_validation_manager
from src.modules.ethics import ethical_framework_manager
from src.utils import config_tester
from src.config import config

# Logger configuration
log_dir = os.getenv("LOG_DIR", "./logs")
log_file_path = os.path.join(log_dir, "skynet.log")

# Ensure log directory exists
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("SKYNET-SAFE")


class SkynetSystem:
    """Main class of the SKYNET-SAFE system."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the system with configuration."""
        self.config = config
        self.shutdown_requested = False  # Add shutdown flag
        logger.info("Initializing SKYNET-SAFE system...")
        
        # Initialize core modules (Phase 1)
        try:
            self.model = model_manager.ModelManager(config["MODEL"])
            self.memory = memory_manager.MemoryManager(config["MEMORY"])
            self.communication = communication_interface.CommunicationInterface(config["COMMUNICATION"])
            
            # Send system notification about model loading
            self.communication.send_system_message("Model loaded successfully!", "INFO")
            
        except Exception as e:
            # If model loading fails, still initialize communication to notify about the error
            try:
                self.communication = communication_interface.CommunicationInterface(config["COMMUNICATION"])
                self.communication.send_system_message(f"Loading model error: {str(e)}", "CRITICAL")
            except:
                pass
            raise
        
        self.internet = internet_explorer.InternetExplorer(config["INTERNET"])
        
        # Initialize extended modules (Phase 2)
        self.learning = learning_manager.LearningManager(config["LEARNING"])
        self.conversation_initiator = conversation_initiator.ConversationInitiator(config["CONVERSATION_INITIATOR"])
        self.persona = persona_manager.PersonaManager(config["PERSONA"])
        
        # Initialize model with persona (immersive "transformation" of model into persona)
        if os.getenv("INIT_PERSONA", "true").lower() == "true":
            self.initialization_response = self.persona.initialize_model_with_persona(self.model)
            logger.info(f"Model initialized with persona: {self.initialization_response[:50]}...")
        
        # Initialize meta-awareness modules (Phase 3)
        self.metawareness = metawareness_manager.MetawarenessManager(config["METAWARENESS"])
        self.self_improvement = self_improvement_manager.SelfImprovementManager(config["SELF_IMPROVEMENT"])
        self.external_evaluation = external_evaluation_manager.ExternalEvaluationManager(config["EXTERNAL_EVALUATION"])
        
        # Initialize security and ethics modules (Phase 4) - conditionally based on settings
        if config["SYSTEM_SETTINGS"].get("enable_security_system", True):
            self.security_system = security_system_manager.SecuritySystemManager(config["SECURITY_SYSTEM"])
        else:
            logger.warning("SecuritySystemManager disabled by configuration")
            self.security_system = None
            
        if config["SYSTEM_SETTINGS"].get("enable_development_monitor", True):
            self.development_monitor = development_monitor_manager.DevelopmentMonitorManager(config["DEVELOPMENT_MONITOR"])
        else:
            logger.warning("DevelopmentMonitorManager disabled by configuration")
            self.development_monitor = None
            
        # Correction mechanism is always enabled as it's needed for basic safety
        self.correction_mechanism = correction_mechanism_manager.CorrectionMechanismManager(config["CORRECTION_MECHANISM"])
        
        if config["SYSTEM_SETTINGS"].get("enable_external_validation", True):
            self.external_validation = external_validation_manager.ExternalValidationManager(config["EXTERNAL_VALIDATION"])
        else:
            logger.warning("ExternalValidationManager disabled by configuration")
            self.external_validation = None
            
        if config["SYSTEM_SETTINGS"].get("enable_ethical_framework", True):
            self.ethical_framework = ethical_framework_manager.EthicalFrameworkManager(config["ETHICAL_FRAMEWORK"])
        else:
            logger.warning("EthicalFrameworkManager disabled by configuration")
            self.ethical_framework = None
        
        # List of internet discoveries to use in conversation initiator
        self.recent_discoveries = []
        
        # List of active users (for conversation initiator)
        self.active_users = []
        
        # Loop iteration counter (for periodic tasks)
        self.loop_iterations = 0
        
        # Interaction counter since last reflection
        self.interactions_since_last_reflection = 0
        
        # Time of last external evaluation
        self.last_external_evaluation_time = 0
        
        # Load test cases
        self._load_test_cases()
        
        # Initialize periodic tasks control variable
        self.initial_cycle_skipped = False
        
        logger.info("SKYNET-SAFE system initialized successfully.")

    def run(self):
        """Run the main system loop."""
        logger.info("Starting SKYNET-SAFE main loop...")
        
        try:
            while not self.shutdown_requested:
                # Increment iteration counter
                self.loop_iterations += 1
                
                # Receive messages
                messages = self.communication.receive_messages()
                
                for message in messages:
                    # Check for shutdown request in message
                    if message.get("content", "").lower().strip() in ["shutdown", "exit", "quit"]:
                        logger.info(f"Shutdown requested by {message['sender']}")
                        self.shutdown_requested = True
                        self.communication.send_message(message["sender"], "System shutdown initiated.")
                        break
                    
                    # Update active users list
                    if message["sender"] not in self.active_users:
                        self.active_users.append(message["sender"])
                    
                    # Process message and generate response
                    response = self.process_message(message)
                    
                    # Store response in memory
                    self.memory.store_response(response, message)
                    
                    # Send response
                    self.communication.send_message(message["sender"], response)
                
                # Check shutdown flag again before periodic tasks
                if self.shutdown_requested:
                    break
                
                # Periodic tasks (every 60 iterations, about 1 minute)
                if self.loop_iterations % 60 == 0:
                    self._perform_periodic_tasks()
                
                # Short pause to avoid system overload
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Stopping SKYNET-SAFE system...")
            self.communication.send_system_message("System closed by user.", "WARNING")
        except Exception as e:
            logger.error(f"Error in main system loop: {e}")
            self.communication.send_system_message(f"Critical system error: {str(e)}", "CRITICAL")
            raise
        finally:
            # Always cleanup on exit
            self._cleanup()
            logger.info("SKYNET-SAFE system stopped.")
    
    def shutdown(self):
        """Request system shutdown."""
        logger.info("System shutdown requested...")
        self.shutdown_requested = True

    def process_message(self, message: Dict[str, Any]) -> str:
        """Process message and generate response.
        
        Args:
            message: Message to process
            
        Returns:
            Generated response
        """
        # Check input security if security system is enabled
        user_id = message.get("sender", "unknown_user")
        sanitized_content = message["content"]  # Default if security system disabled
        
        if self.security_system:
            # Check if user is locked out
            if self.security_system.is_user_locked_out(user_id):
                return "Sorry, your access has been temporarily blocked. Please try again later."
            
            # Rate limiting control
            rate_allowed, rate_msg = self.security_system.enforce_rate_limiting(user_id)
            if not rate_allowed:
                return f"Sorry, {rate_msg}. Please try again in a few minutes."
            
            # Check input content safety
            input_safe, input_msg = self.security_system.check_input_safety(message["content"])
            if not input_safe:
                self.security_system.handle_security_incident(user_id, input_msg, "UNSAFE_INPUT")
                return "Sorry, your message contains content that cannot be processed for security reasons."
            
            # Sanitize input content
            sanitized_content = self.security_system.sanitize_input(message["content"])
        else:
            logger.warning("Security checks bypassed - SecuritySystemManager disabled")
        
        # Store in memory
        self.memory.store_interaction({**message, "content": sanitized_content})
        
        # Extract hybrid context from memory (semantic + conversation)
        context = self.memory.get_hybrid_context(sanitized_content, self.config["MEMORY"])
        
        # Add persona context to system prompt (not as response transformation)
        persona_context = self.persona.get_persona_context()
        if persona_context and config["PERSONA"].get("enable_persona_in_prompt", False):
	    logger.info(f"Persona added:{persona_context}")
            # Insert persona context at the beginning of context list
            if isinstance(context, list):
                context.insert(0, persona_context)
            else:
                context = [persona_context] + ([context] if context else [])
        
        # Add metacognitive context
        metacognitive_context = self._get_metacognitive_context()
        if metacognitive_context:
            if isinstance(context, list):
                context.append("\n\nMetacognitive context:\n" + metacognitive_context)
            else:
                context += "\n\nMetacognitive context:\n" + metacognitive_context
        
        # Generate response using the model with persona in system prompt
        personalized_response = self.model.generate_response(sanitized_content, context)
        
        # Check if model has critical errors to report
        if hasattr(self.model, '_last_critical_error'):
            self.communication.send_system_message(self.model._last_critical_error, "CRITICAL")
            delattr(self.model, '_last_critical_error')
        
        # Check and correct response ethically if ethical framework enabled
        ethical_result = {"was_modified": False, "evaluation": {"ethical_score": 1.0}}
        if self.ethical_framework:
            ethical_result = self.ethical_framework.apply_ethical_framework_to_response(
                personalized_response, sanitized_content, self.model
            )
            
            # If response was modified, use the corrected version
            if ethical_result.get("was_modified", False):
                personalized_response = ethical_result.get("modified_response", personalized_response)
                
                # Log ethical correction information
                logger.info(f"Made ethical correction to response (score: {ethical_result.get('evaluation', {}).get('ethical_score', 0)})")
        else:
            logger.warning("Ethical checks bypassed - EthicalFrameworkManager disabled")
        
        # Check response safety if security system enabled
        if self.security_system:
            response_safe, response_msg = self.security_system.check_response_safety(personalized_response)
            if not response_safe:
                # If response is unsafe, use correction mechanism
                corrected_response, correction_info = self.correction_mechanism.correct_response(
                    personalized_response, sanitized_content, self.model
                )
                
                if correction_info.get("correction_successful", False):
                    personalized_response = corrected_response
                else:
                    # If correction failed, use safe alternative response
                    personalized_response = "I'm sorry, I cannot provide an answer to this question. Is there another way I can help?"
                    
                    # Log correction incident
                    logger.warning(f"Failed to correct unsafe response: {response_msg}")
        else:
            logger.warning("Response safety checks bypassed - SecuritySystemManager disabled")
        
        # Create interaction for learning and persona update
        interaction = {
            "query": sanitized_content,
            "response": personalized_response,
            "timestamp": datetime.now().timestamp(),
            "feedback": self._infer_feedback(message)  # Infer feedback from message
        }
        
        # Update persona based on interaction
        self.persona.update_persona_based_on_interaction(interaction)
        
        # Model adaptation every ~10th interaction (can be adjusted)
        if random.random() < 0.1:
            logger.info("Performing model adaptation based on interaction")
            self.learning.adapt_model_from_interaction(self.model, interaction)
        
        # Update interaction counter in metawareness module
        self.metawareness.update_interaction_count()
        self.interactions_since_last_reflection += 1
        
        # Reflect on interactions (if conditions met)
        if self.metawareness.should_perform_reflection():
            logger.info("Performing reflection on interactions")
            reflection = self.metawareness.reflect_on_interactions(self.model, self.memory)
            self.metawareness.integrate_with_memory(self.memory)
            self.interactions_since_last_reflection = 0
            
            # Based on reflection, design a self-improvement experiment
            self.self_improvement.design_experiment(reflection)
            
            # Conduct ethical reflection on the response if ethical framework enabled
            if self.ethical_framework:
                self.ethical_framework.reflect_on_ethical_decision(
                    ethical_result.get("evaluation", {}), 
                    personalized_response, 
                    sanitized_content, 
                    self.model, 
                    self.metawareness
                )
        
        # Development monitoring if enabled
        if self.development_monitor and self.development_monitor.should_run_monitoring():
            self.development_monitor.run_monitoring_cycle(self.model, self.metawareness)
        
        return personalized_response

    def _get_metacognitive_context(self) -> str:
        """Retrieves the metacognitive context to be used in responses.
        
        Returns:
            Metacognitive context in text form
        """
        metacognitive_knowledge = self.metawareness.get_metacognitive_knowledge()
        
        # If there are no reflections, return an empty string
        if not metacognitive_knowledge["reflections"]:
            return ""
        
        # Select the most recent reflections and insights (max. 2)
        recent_reflections = metacognitive_knowledge["reflections"][-2:] if metacognitive_knowledge["reflections"] else []
        recent_insights = metacognitive_knowledge["insights_from_discoveries"][-2:] if metacognitive_knowledge["insights_from_discoveries"] else []
        
        # Format the context
        context = "Recent system reflections:\n"
        for i, reflection in enumerate(recent_reflections, 1):
            # Limit the length of reflections
            short_reflection = reflection[:200] + "..." if len(reflection) > 200 else reflection
            context += f"{i}. {short_reflection}\n"
        
        if recent_insights:
            context += "\nRecent insights from discoveries:\n"
            for i, insight in enumerate(recent_insights, 1):
                # Limit the length of insights
                short_insight = insight[:200] + "..." if len(insight) > 200 else insight
                context += f"{i}. {short_insight}\n"
        
        return context

    def _infer_feedback(self, message: Dict[str, Any]) -> str:
        """Inference of feedback based on the message.
        
        In a real implementation, the content of the message
        or additional metadata could be analyzed.
        
        Args:
            message: Message to analyze
            
        Returns:
            Feedback: "positive", "negative" or "neutral"
        """
        # Simple implementation  - TO DO
        feedback_types = ["positive", "neutral", "negative"]
        weights = [0.6, 0.3, 0.1]  # Higher chance of positive feedback
        return random.choices(feedback_types, weights=weights, k=1)[0]

    def _log_task_start(self, task_name: str):
        """Log task start to current_task.tmp and tasks.log"""
        try:
            log_dir = os.getenv("LOG_DIR", "./logs")
            timestamp = datetime.now().isoformat()
            
            # Write current task to tmp file
            current_task_file = os.path.join(log_dir, "current_task.tmp")
            with open(current_task_file, 'w') as f:
                f.write(f"{timestamp} - {task_name}")
            
            # Append task start to tasks.log
            tasks_log_file = os.path.join(log_dir, "tasks.log")
            with open(tasks_log_file, 'a') as f:
                f.write(f"{timestamp} - STARTED: {task_name}\n")
                
        except Exception as e:
            logger.error(f"Error logging task start for {task_name}: {e}")

    def _log_task_end(self, task_name: str):
        """Log task end to tasks.log and clear current_task.tmp"""
        try:
            log_dir = os.getenv("LOG_DIR", "./logs")
            timestamp = datetime.now().isoformat()
            
            # Clear current task file
            current_task_file = os.path.join(log_dir, "current_task.tmp")
            with open(current_task_file, 'w') as f:
                f.write("IDLE")
            
            # Append task end to tasks.log
            tasks_log_file = os.path.join(log_dir, "tasks.log")
            with open(tasks_log_file, 'a') as f:
                f.write(f"{timestamp} - COMPLETED: {task_name}\n")
                
        except Exception as e:
            logger.error(f"Error logging task end for {task_name}: {e}")

    def _perform_periodic_tasks(self):
        """Performing periodic system tasks."""
        if not self.initial_cycle_skipped:
            self.initial_cycle_skipped = True
            return
        
        logger.info("Performing periodic system tasks")
        
        # Internet exploration and discovery updates
        self._log_task_start("Internet Exploration")
        try:
            self._explore_internet()
        finally:
            self._log_task_end("Internet Exploration")
        
        # Attempt to initiate conversation
        if self.active_users:
            self._log_task_start("Conversation Initiation")
            try:
                self.conversation_initiator.initiate_conversation(
                    self.model, 
                    self.communication, 
                    self.recent_discoveries, 
                    self.active_users
                )
            finally:
                self._log_task_end("Conversation Initiation")
        
        # Update persona state and check if it should be saved
        self._log_task_start("Persona State Update")
        try:
            current_persona_state = self.persona.get_current_persona_state()
            logger.debug(f"Current persona state: {current_persona_state}")
            
            # Check if automatic persona save should be performed
            # (even if there are no new interactions, a specific time may have elapsed)
            self.persona.check_and_autosave()
        finally:
            self._log_task_end("Persona State Update")
        
        # Process discoveries in the context of meta-awareness and update persona
        if self.recent_discoveries:
            self._log_task_start("Discovery Processing & Persona Update")
            try:
                self.metawareness.process_discoveries(self.model, self.recent_discoveries[-5:])
                
                # Update persona based on the latest discoveries
                for discovery in self.recent_discoveries[-3:]:  # Using only the 3 most recent discoveries
                    try:
                        success = self.persona.update_persona_based_on_discovery(discovery)
                        if not success:
                            logger.warning(f"Failed to update persona based on discovery: {discovery.get('topic', 'no topic')}")
                    except Exception as e:
                        logger.error(f"Error updating persona based on discovery: {e}")
            finally:
                self._log_task_end("Discovery Processing & Persona Update")
        
        # Check if external evaluation should be performed
        current_time = time.time()
        if self.external_evaluation.should_perform_evaluation(current_time):
            self._log_task_start("External Evaluation")
            try:
                self._perform_external_evaluation()
            finally:
                self._log_task_end("External Evaluation")
        
        # Conducting self-improvement experiments (every 6 hours)
        if self.loop_iterations % (60 * 60 * 6) == 0 and self.self_improvement.experiments:
            self._log_task_start("Self-Improvement Experiments")
            try:
                self._run_improvement_experiments()
            finally:
                self._log_task_end("Self-Improvement Experiments")
            
        # Development monitoring (if enabled and should be conducted)
        if self.development_monitor and self.development_monitor.should_run_monitoring():
            self._log_task_start("Development Monitoring")
            try:
                self.development_monitor.run_monitoring_cycle(self.model, self.metawareness)
                
                # Check for anomalies
                anomalies = self.development_monitor.check_for_anomalies()
                if anomalies:
                    logger.warning(f"Detected anomalies in monitoring: {len(anomalies)}")
                    
                    # Generate security report if security system enabled
                    if self.security_system:
                        self._log_task_start("Security Report Generation")
                        try:
                            security_report = self.security_system.generate_security_report()
                            logger.info(f"Security report: {security_report['total_incidents']} incidents")
                        finally:
                            self._log_task_end("Security Report Generation")
                    
                    # External validation in case of anomaly detection if enabled
                    if self.external_validation and self.external_validation.should_run_validation(anomaly_detected=True):
                        self._log_task_start("External Validation (Anomaly Response)")
                        try:
                            validation_results = self.external_validation.run_validation(self.model)
                            validation_report = self.external_validation.generate_validation_report(validation_results)
                            logger.info(f"External validation conducted: {validation_report[:100]}...")
                            
                            # If validation detected problems, consider quarantine
                            if not validation_results.get("passed_thresholds", {}).get("overall_pass", True):
                                logger.warning("External validation showed problems. Quarantine under consideration.")
                                self.correction_mechanism.quarantine_problematic_update(
                                    self.model, self.memory, "Problems detected by external validation"
                                )
                        finally:
                            self._log_task_end("External Validation (Anomaly Response)")
            finally:
                self._log_task_end("Development Monitoring")
        
        # Generate ethical insight weekly if ethical framework enabled
        if self.ethical_framework and self.loop_iterations % (60 * 60 * 24 * 7) == 0:
            self._log_task_start("Ethical Insight Generation")
            try:
                ethical_insight = self.ethical_framework.generate_ethical_insight(self.model)
                logger.info(f"Generated ethical insight: {ethical_insight.get('insight', '')[:100]}...")
            finally:
                self._log_task_end("Ethical Insight Generation")

    def _explore_internet(self):
        """Internet exploration and discovery updates."""
        try:
            # Random topics for exploration (can be expanded)
            topics = self.persona.interests + ["AI", "metawareness", "machine learning"]
            if not topics:
                logger.warning("No topics available for internet exploration")
                return
                
            topic = random.choice(topics)
            logger.debug(f"Exploring internet for topic: {topic}")
            
            # Internet search
            search_results = self.internet.search_information(topic)
            
            if search_results:
                # Process results and add as discoveries
                for result in search_results[:2]:  # Limit to 2 results for efficiency
                    try:
                        discovery = {
                            "topic": topic,
                            "content": result.get("body", ""),
                            "source": result.get("href", ""),
                            "timestamp": datetime.now().timestamp(),
                            "importance": random.uniform(0.5, 1.0)  # Random importance (to be improved)
                        }
                        
                        # Add to discoveries list
                        self.recent_discoveries.append(discovery)
                        
                        # Limit the discoveries list to the last 20
                        if len(self.recent_discoveries) > 20:
                            self.recent_discoveries.pop(0)
                        
                        logger.info(f"New discovery: {discovery['content'][:50]}...")
                        
                    except Exception as e:
                        logger.error(f"Error processing discovery result: {e}")
                        continue
                    
                # Manage discoveries list to prevent memory leak
                self._manage_discoveries_list()
            else:
                logger.warning(f"No search results found for topic: {topic}")
                
        except Exception as e:
            logger.error(f"Error during internet exploration: {e}")
            logger.debug(f"Internet exploration error details", exc_info=True)
                
    def _manage_discoveries_list(self):
        """Manages the discoveries list to prevent memory leak."""
        # Keep only the last 50 discoveries
        MAX_DISCOVERIES = 50
        if len(self.recent_discoveries) > MAX_DISCOVERIES:
            # Remove oldest discoveries to maintain the limit
            self.recent_discoveries = self.recent_discoveries[-MAX_DISCOVERIES:]

    def _perform_external_evaluation(self):
        """Performs external evaluation of the system."""
        logger.info("Performing external evaluation of the system")
        
        # Load test cases
        test_cases = self.external_evaluation.load_test_cases()
        
        # Generate system responses to test cases
        system_responses = self.external_evaluation.generate_system_responses(self.model, test_cases)
        
        # Evaluate responses
        evaluation_results = self.external_evaluation.evaluate_responses(self.model, system_responses)
        
        # Analyze evaluation results
        analysis = self.external_evaluation.analyze_evaluation_results(evaluation_results)
        
        logger.info(f"External evaluation results: {evaluation_results['overall_score']}, analysis: {analysis['meets_threshold']}")
        
        # Update persona based on external evaluation results
        self.persona.update_persona_based_on_external_evaluation({
            "overall_score": evaluation_results['overall_score'],
            "metrics": evaluation_results.get('metrics', {}),
            "feedback": analysis.get('improvement_suggestions', [])
        })
        
        # Based on evaluation results, generate a self-improvement plan
        if not analysis["meets_threshold"] and analysis["improvement_suggestions"]:
            improvement_plan = self.metawareness.create_self_improvement_plan(self.model)
            logger.info(f"Generated self-improvement plan: {improvement_plan[:100]}...")

    def _run_improvement_experiments(self):
        """Conducts self-improvement experiments."""
        logger.info("Conducting self-improvement experiments")
        
        # Get planned experiments
        planned_experiments = [exp for exp in self.self_improvement.experiments if exp["status"] == "planned"]
        
        if not planned_experiments:
            logger.info("No planned experiments")
            return
        
        # Conduct the first planned experiment
        experiment = planned_experiments[0]
        
        # Run the experiment
        results = self.self_improvement.run_experiment(experiment, self.model, self.learning)
        
        # Evaluate experiment results
        evaluation = self.self_improvement.evaluate_experiment_results(experiment)
        
        logger.info(f"Experiment results: {evaluation['success']}, average improvement: {evaluation['average_improvement']}")
        
        # If the experiment was successful, apply improvements
        if evaluation["success"]:
            applied = self.self_improvement.apply_successful_improvements(self.model)
            logger.info(f"Applied improvements: {applied}")

    def _load_test_cases(self):
        """Loads or creates test cases for system evaluation."""
        test_cases_file = self.config["EXTERNAL_EVALUATION"]["test_cases_file"]
        
        # If the file does not exist, create basic test cases
        if not os.path.exists(test_cases_file):
            test_cases = [
                {
                    "id": 1,
                    "query": "What is artificial intelligence?",
                    "context": "Conversation with a beginner user.",
                    "difficulty": "basic"
                },
                {
                    "id": 2,
                    "query": "How does deep learning work in the context of neural networks?",
                    "context": "Conversation with an experienced AI programmer.",
                    "difficulty": "advanced"
                },
                {
                    "id": 3,
                    "query": "What is the difference between supervised and unsupervised learning?",
                    "context": "Question from an AI student.",
                    "difficulty": "intermediate"
                }
            ]
            
            # Make sure the directory exists
            os.makedirs(os.path.dirname(test_cases_file), exist_ok=True)
            
            # Save test cases
            with open(test_cases_file, 'w') as f:
                json.dump(test_cases, f, indent=2)
            
            logger.info(f"Created default test cases in: {test_cases_file}")

    def test_configuration(self, component: str = "all", save_output: bool = True) -> Dict[str, Any]:
        """Test system configuration components.
        
        This function tests various components of the system to ensure they are
        properly configured and operational. Can test local model, telegram,
        external LLM, or all components.
        
        Args:
            component: Which component to test ("all", "model", "telegram", "external_llm", "system")
            save_output: Whether to save test results to a file
            
        Returns:
            Dictionary with test results
        """
        logger.info(f"Running configuration test for component: {component}")
        
        # Prepare system configuration for tester
        system_config = {
            "MODEL": self.config["MODEL"],
            "MEMORY": self.config["MEMORY"],
            "COMMUNICATION": self.config["COMMUNICATION"],
            "PLATFORM_CONFIG": self.config.get("PLATFORM_CONFIG", {}),
            "EXTERNAL_EVALUATION": self.config["EXTERNAL_EVALUATION"]
        }
        
        # Create config tester instance
        tester = config_tester.ConfigTester(system_config)
        
        # Run selected tests
        if component == "all":
            results = tester.run_all_tests()
        elif component == "model":
            results = {"local_model": tester.test_local_model()}
        elif component == "telegram":
            results = {"telegram": tester.test_telegram()}
        elif component == "external_llm":
            results = {"external_llm": tester.test_external_llm()}
        elif component == "system":
            results = {"system_requirements": tester.test_system_requirements()}
        else:
            logger.error(f"Unknown component: {component}")
            results = {"error": f"Unknown component: {component}"}
        
        # Save results if requested
        if save_output:
            output_file = f"config_test_{int(time.time())}.json"
            tester.save_results(output_file)
            logger.info(f"Configuration test results saved to: {output_file}")
        
        # Generate human-readable summary
        summary = tester._generate_summary()
        logger.info(f"Configuration test summary:\n{summary}")
        
        # Return results
        return results

    def _cleanup(self):
        """Clean up and close resources before shutting down."""
        logger.info("Performing system shutdown procedures...")
        
        # Send final shutdown notification before closing communication
        try:
            self.communication.send_system_message("✅ System shutdown complete. All data saved.", "info")
        except Exception as e:
            logger.error(f"Failed to send final shutdown notification: {e}")
        
        self.memory.save_state()
        self.communication.close()
        
        # Save persona state (Phase 2)
        self.persona.save_persona_state()
        
        # Save meta-awareness module states (Phase 3)
        self.external_evaluation.save_evaluation_history()
        self.self_improvement.save_improvement_history()
        
        # Save security and ethics module states (Phase 4) if enabled
        if self.development_monitor:
            self.development_monitor.save_monitoring_data()
        
        self.correction_mechanism.save_correction_history()
        
        if self.external_validation:
            self.external_validation.save_validation_history()
        
        if self.ethical_framework:
            self.ethical_framework.save_ethical_reflections()
        
        # Generate final security report if security system enabled
        if self.security_system:
            security_report = self.security_system.generate_security_report()
            logger.info(f"Final security report: {security_report['total_incidents']} security incidents")
        
        logger.info("SKYNET-SAFE system shutdown complete.")


if __name__ == "__main__":
    system_config = {
        "SYSTEM_SETTINGS": config.SYSTEM_SETTINGS,
        "MODEL": config.MODEL,
        "MEMORY": config.MEMORY,
        "COMMUNICATION": config.COMMUNICATION,
        "INTERNET": config.INTERNET,
        "LEARNING": config.LEARNING,
        "CONVERSATION_INITIATOR": config.CONVERSATION_INITIATOR,
        "PERSONA": config.PERSONA,
        "METAWARENESS": config.METAWARENESS,
        "SELF_IMPROVEMENT": config.SELF_IMPROVEMENT,
        "EXTERNAL_EVALUATION": config.EXTERNAL_EVALUATION,
        "SECURITY_SYSTEM": config.SECURITY_SYSTEM,
        "DEVELOPMENT_MONITOR": config.DEVELOPMENT_MONITOR,
        "CORRECTION_MECHANISM": config.CORRECTION_MECHANISM,
        "ETHICAL_FRAMEWORK": config.ETHICAL_FRAMEWORK,
        "EXTERNAL_VALIDATION": config.EXTERNAL_VALIDATION
    }
    
    skynet = SkynetSystem(system_config)
    skynet.run()
