"""Module for managing the system self-improvement process."""

import logging
import os
import json
import time
from typing import Dict, List, Any, Optional

logger = logging.getLogger("SKYNET-SAFE.SelfImprovementManager")

class SelfImprovementManager:
    """Class managing the system self-improvement process."""

    def __init__(self, config: Dict[str, Any]):
        """Initialization of self-improvement manager with configuration.
        
        Args:
            config: Self-improvement module configuration containing parameters such as
                   learning_rate_adjustment_factor, improvement_metrics, improvement_threshold, etc.
        """
        self.config = config
        self.learning_rate_adjustment_factor = config.get("learning_rate_adjustment_factor", 0.1)
        self.improvement_metrics = config.get("improvement_metrics", 
                                            ["response_quality", "context_usage", "knowledge_application"])
        self.improvement_threshold = config.get("improvement_threshold", 0.7)
        self.max_experiment_iterations = config.get("max_experiment_iterations", 5)
        self.history_file = config.get("history_file", "./data/metawareness/improvement_history.json")
        
        # Create a directory for data if it doesn't exist
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        
        # List of conducted experiments
        self.experiments = []
        
        # List of implemented improvements
        self.improvement_history = []
        
        # Load improvement history if it exists
        self.load_improvement_history()
        
        logger.info(f"Self-improvement manager initialized with {self.improvement_threshold=}")

    def adjust_learning_parameters(self, learning_manager: Any, adjustment_factor: float) -> None:
        """Adjusts learning parameters based on experiment results.
        
        Args:
            learning_manager: LearningManager instance to adjust
            adjustment_factor: Adjustment factor (>1 increases, <1 decreases)
        """
        logger.info(f"Adjusting learning parameters with {adjustment_factor=}")
        
        # Adjust learning rate
        current_lr = learning_manager.learning_rate
        new_lr = current_lr * adjustment_factor
        learning_manager.learning_rate = new_lr
        
        logger.info(f"Learning rate adjusted: {current_lr} -> {new_lr}")

    def design_experiment(self, reflection: str) -> Dict[str, Any]:
        """Designs a self-improvement experiment based on reflection.
        
        Args:
            reflection: Reflection based on which we design the experiment
            
        Returns:
            Dictionary describing the designed experiment
        """
        logger.info("Designing self-improvement experiment")
        
        # In a real implementation, a model could be used to design the experiment
        # For the purposes of this implementation, we're creating a simple experiment
        
        # We analyze the reflection to find potential areas for improvement
        # In this example, we assume the reflection concerns overly general responses
        experiment = {
            "id": len(self.experiments) + 1,
            "hypothesis": "Reducing temperature improves response coherence",
            "parameters": {"temperature": 0.5},  # Parameter to adjust
            "metrics": self.improvement_metrics,  # Metrics to monitor
            "status": "planned",
            "created_at": time.time()
        }
        
        # Add the experiment to the list
        self.experiments.append(experiment)
        
        logger.info(f"Experiment designed: {experiment['hypothesis']}")
        return experiment

    def run_experiment(self, experiment: Dict[str, Any], model_manager: Any, 
                       learning_manager: Any) -> Dict[str, Any]:
        """Conducts the designed experiment.
        
        Args:
            experiment: Dictionary describing the experiment
            model_manager: ModelManager instance for testing
            learning_manager: LearningManager instance for training
            
        Returns:
            Dictionary with experiment results
        """
        logger.info(f"Starting experiment: {experiment['hypothesis']}")
        
        # Save original parameters
        original_params = {}
        for param_name, param_value in experiment["parameters"].items():
            if hasattr(model_manager.config, param_name):
                original_params[param_name] = model_manager.config[param_name]
        
        # Apply experimental parameters
        for param_name, param_value in experiment["parameters"].items():
            if hasattr(model_manager.config, param_name):
                model_manager.config[param_name] = param_value
        
        # Conduct the experiment
        # In a real implementation, we would conduct a series of tests here
        # For simplification, we're generating example responses and evaluating them
        
        # Example test query
        test_query = "Explain the concept of machine learning so that a beginner can understand it."
        
        # Generate response with new parameters
        test_response = model_manager.generate_response(test_query, "")
        
        # Response evaluation (would be more extensive in a real implementation)
        metrics = {}
        for metric in experiment["metrics"]:
            # Example scores (in reality, they would be generated by an evaluation model)
            if metric == "response_quality":
                metrics[metric] = 0.85
            elif metric == "context_usage":
                metrics[metric] = 0.78
            elif metric == "knowledge_application":
                metrics[metric] = 0.92
            else:
                metrics[metric] = 0.8
        
        # Restore original parameters
        for param_name, param_value in original_params.items():
            model_manager.config[param_name] = param_value
        
        # Experiment results
        results = {
            "metrics": metrics,
            "original_params": original_params,
            "experiment_params": experiment["parameters"],
            "test_query": test_query,
            "test_response": test_response,
            "run_at": time.time()
        }
        
        # Update the experiment
        experiment["status"] = "completed"
        experiment["results"] = results
        
        logger.info(f"Experiment completed: {experiment['id']}")
        return results

    def evaluate_experiment_results(self, experiment: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluates experiment results.
        
        Args:
            experiment: Dictionary describing the experiment with results
            
        Returns:
            Dictionary with results evaluation
        """
        logger.info(f"Evaluating experiment results: {experiment['id']}")
        
        # Check if the experiment has results
        if "results" not in experiment or experiment["status"] != "completed":
            return {"success": False, "improvements": {}, "average_improvement": 0.0}
        
        # Get metrics
        metrics = experiment["results"]["metrics"]
        
        # Check if metrics exceed the threshold
        improvements = {}
        avg_improvement = 0.0
        metrics_count = 0
        
        for metric, value in metrics.items():
            improvements[metric] = value - self.improvement_threshold
            avg_improvement += improvements[metric]
            metrics_count += 1
        
        if metrics_count > 0:
            avg_improvement /= metrics_count
        
        # Consider the experiment successful if average improvement is positive
        success = avg_improvement > 0 and all(value >= self.improvement_threshold for value in metrics.values())
        
        evaluation = {
            "success": success,
            "improvements": improvements,
            "average_improvement": avg_improvement,
            "evaluated_at": time.time()
        }
        
        # Save the evaluation in the experiment
        experiment["evaluation"] = evaluation
        
        logger.info(f"Experiment evaluation: {success=}, {avg_improvement=}")
        return evaluation

    def apply_successful_improvements(self, model_manager: Any) -> bool:
        """Applies successful improvements to the model.
        
        Args:
            model_manager: ModelManager instance to update
            
        Returns:
            True if improvements were applied, False otherwise
        """
        try:
            logger.info("Applying successful improvements to the model")
            
            if not self.experiments:
                logger.debug("No experiments available for improvement application")
                return False
            
            applied = False
            failed_applications = []
            
            # Review experiments and apply successful ones
            for experiment in self.experiments:
                try:
                    if "evaluation" not in experiment:
                        logger.debug(f"Experiment {experiment.get('id', 'unknown')} has no evaluation")
                        continue
                        
                    if not experiment["evaluation"].get("success", False):
                        logger.debug(f"Experiment {experiment.get('id', 'unknown')} was not successful")
                        continue
                    
                    experiment_id = experiment.get("id", "unknown")
                    parameters = experiment.get("parameters", {})
                    
                    if not parameters:
                        logger.warning(f"Experiment {experiment_id} has no parameters to apply")
                        continue
                    
                    # Apply parameter changes
                    for param_name, param_value in parameters.items():
                        try:
                            if not hasattr(model_manager, 'config') or model_manager.config is None:
                                logger.error("Model manager has no config attribute")
                                failed_applications.append(f"{experiment_id}:{param_name}")
                                continue
                                
                            if param_name not in model_manager.config:
                                logger.warning(f"Parameter {param_name} not found in model config")
                                continue
                            
                            old_value = model_manager.config[param_name]
                            model_manager.config[param_name] = param_value
                            
                            # Save information about the change
                            improvement = {
                                "type": "parameter_change",
                                "parameter": param_name,
                                "old_value": old_value,
                                "new_value": param_value,
                                "timestamp": time.time(),
                                "experiment_id": experiment_id,
                                "metrics_improvement": experiment["evaluation"].get("improvements", {})
                            }
                            
                            self.improvement_history.append(improvement)
                            applied = True
                            
                            logger.info(f"Improvement applied: {param_name} = {param_value} (from {old_value})")
                            
                        except Exception as e:
                            logger.error(f"Error applying parameter {param_name} from experiment {experiment_id}: {e}")
                            failed_applications.append(f"{experiment_id}:{param_name}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error processing experiment {experiment.get('id', 'unknown')}: {e}")
                    continue
            
            if failed_applications:
                logger.warning(f"Failed to apply {len(failed_applications)} improvements: {failed_applications}")
            
            # Save improvement history
            if applied:
                try:
                    self.save_improvement_history()
                except Exception as e:
                    logger.error(f"Error saving improvement history: {e}")
            
            logger.info(f"Applied {len([h for h in self.improvement_history if h.get('timestamp', 0) > time.time() - 60])} improvements")
            return applied
            
        except Exception as e:
            logger.error(f"Unexpected error during improvement application: {e}")
            logger.debug("Improvement application error details", exc_info=True)
            return False

    def save_improvement_history(self) -> None:
        """Saves improvement history to a file."""
        try:
            logger.info(f"Saving improvement history to: {self.history_file}")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            
            # Create backup of existing file
            backup_file = f"{self.history_file}.backup"
            if os.path.exists(self.history_file):
                try:
                    import shutil
                    shutil.copy2(self.history_file, backup_file)
                except Exception as e:
                    logger.warning(f"Could not create backup file: {e}")
            
            # Save improvement history
            with open(self.history_file, 'w') as f:
                json.dump(self.improvement_history, f, indent=2)
                
            logger.debug(f"Successfully saved {len(self.improvement_history)} improvement records")
            
        except PermissionError as e:
            logger.error(f"Permission denied saving improvement history: {e}")
        except OSError as e:
            logger.error(f"OS error saving improvement history: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving improvement history: {e}")
            logger.debug("Save improvement history error details", exc_info=True)

    def load_improvement_history(self) -> None:
        """Loads improvement history from a file."""
        try:
            if not os.path.exists(self.history_file):
                logger.debug(f"Improvement history file does not exist: {self.history_file}")
                self.improvement_history = []
                return
                
            logger.info(f"Loading improvement history from: {self.history_file}")
            
            # Check if file is readable
            if not os.access(self.history_file, os.R_OK):
                logger.error(f"No read permission for improvement history file: {self.history_file}")
                self.improvement_history = []
                return
            
            # Check file size
            file_size = os.path.getsize(self.history_file)
            if file_size == 0:
                logger.warning("Improvement history file is empty")
                self.improvement_history = []
                return
            
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                
            # Validate loaded data
            if not isinstance(data, list):
                logger.error(f"Invalid improvement history format - expected list, got {type(data)}")
                self.improvement_history = []
                return
                
            self.improvement_history = data
            logger.info(f"Successfully loaded {len(self.improvement_history)} improvement records")
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error loading improvement history: {e}")
            # Try to load backup file
            backup_file = f"{self.history_file}.backup"
            if os.path.exists(backup_file):
                try:
                    logger.info("Attempting to load from backup file")
                    with open(backup_file, 'r') as f:
                        self.improvement_history = json.load(f)
                    logger.info("Successfully loaded from backup file")
                except Exception as backup_e:
                    logger.error(f"Error loading from backup file: {backup_e}")
                    self.improvement_history = []
            else:
                self.improvement_history = []
        except PermissionError as e:
            logger.error(f"Permission denied loading improvement history: {e}")
            self.improvement_history = []
        except OSError as e:
            logger.error(f"OS error loading improvement history: {e}")
            self.improvement_history = []
        except Exception as e:
            logger.error(f"Unexpected error loading improvement history: {e}")
            logger.debug("Load improvement history error details", exc_info=True)
            self.improvement_history = []

    def generate_improvement_report(self) -> str:
        """Generates a report from the self-improvement process.
        
        Returns:
            Text report summarizing implemented improvements
        """
        logger.info("Generating report from self-improvement process")
        
        if not self.improvement_history:
            return "No improvements implemented."
        
        # Grouping improvements by type
        improvements_by_type = {}
        
        for improvement in self.improvement_history:
            imp_type = improvement.get("type", "unknown")
            if imp_type not in improvements_by_type:
                improvements_by_type[imp_type] = []
            
            improvements_by_type[imp_type].append(improvement)
        
        # Generating the report
        report = "Self-improvement process report:\n\n"
        
        for imp_type, improvements in improvements_by_type.items():
            report += f"Improvement type: {imp_type}\n"
            report += f"Number of improvements: {len(improvements)}\n"
            
            for i, improvement in enumerate(improvements, 1):
                report += f"\n{i}. Change: {improvement.get('parameter', 'unknown parameter')}\n"
                report += f"   Old value: {improvement.get('old_value', 'N/A')}\n"
                report += f"   New value: {improvement.get('new_value', 'N/A')}\n"
                
                # Display metrics improvement
                metrics_improvement = improvement.get("metrics_improvement", {})
                if metrics_improvement:
                    report += "   Metrics improvement:\n"
                    for metric, value in metrics_improvement.items():
                        report += f"   - {metric}: {value:.2f}\n"
        
        return report