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
        logger.info("Applying successful improvements to the model")
        
        applied = False
        
        # Review experiments and apply successful ones
        for experiment in self.experiments:
            if "evaluation" in experiment and experiment["evaluation"]["success"]:
                # Apply parameter changes
                for param_name, param_value in experiment["parameters"].items():
                    if param_name in model_manager.config:
                        old_value = model_manager.config[param_name]
                        model_manager.config[param_name] = param_value
                        
                        # Save information about the change
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
                        
                        logger.info(f"Improvement applied: {param_name} = {param_value}")
        
        # Save improvement history
        if applied:
            self.save_improvement_history()
        
        return applied

    def save_improvement_history(self) -> None:
        """Saves improvement history to a file."""
        logger.info(f"Saving improvement history to: {self.history_file}")
        
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.improvement_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving improvement history: {e}")

    def load_improvement_history(self) -> None:
        """Loads improvement history from a file."""
        if os.path.exists(self.history_file):
            logger.info(f"Loading improvement history from: {self.history_file}")
            
            try:
                with open(self.history_file, 'r') as f:
                    self.improvement_history = json.load(f)
            except Exception as e:
                logger.error(f"Error loading improvement history: {e}")
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