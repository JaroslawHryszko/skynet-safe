"""Module for managing system meta-awareness."""

import logging
import os
import json
import time
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger("SKYNET-SAFE.MetawarenessManager")

class MetawarenessManager:
    """Class managing the system's meta-awareness - the ability to reflect on its own processes."""

    def __init__(self, config: Dict[str, Any]):
        """Initialization of the meta-awareness manager with configuration.
        
        Args:
            config: Configuration of the meta-awareness module containing parameters such as
                   reflection_frequency, reflection_depth, external_eval_frequency, etc.
        """
        self.config = config
        self.reflection_frequency = config.get("reflection_frequency", 10)
        self.reflection_depth = config.get("reflection_depth", 5)
        self.external_eval_frequency = config.get("external_eval_frequency", 24 * 60 * 60)  # 24h
        self.self_improvement_metrics = config.get("self_improvement_metrics", 
                                                ["accuracy", "relevance", "coherence", "creativity"])
        self.checkpoint_dir = config.get("checkpoint_dir", "./data/metawareness")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        # Initialize interaction counter
        self.interaction_count = 0
        
        # List of performed reflections
        self.self_reflections = []
        
        # List of insights drawn from internet discoveries
        self.insights_from_discoveries = []
        
        logger.info(f"Meta-awareness manager initialized with {self.reflection_frequency=}, {self.reflection_depth=}")

    def should_perform_reflection(self) -> bool:
        """Checks if reflection on interactions should be performed.
        
        Returns:
            True if reflection should be performed, False otherwise
        """
        # Reflection should be performed every self.reflection_frequency interactions
        return self.interaction_count % self.reflection_frequency == 0 and self.interaction_count > 0

    def reflect_on_interactions(self, model_manager: Any, memory_manager: Any) -> str:
        """Performs reflection on recent interactions.
        
        Args:
            model_manager: ModelManager instance for generating reflections
            memory_manager: MemoryManager instance for accessing previous interactions
            
        Returns:
            Reflection in text form
        """
        logger.info("Performing reflection on recent interactions")
        
        # Get recent interactions from memory
        interactions = memory_manager.retrieve_last_interactions(self.reflection_depth)
        
        # Prepare prompt for the model
        prompt = self._prepare_reflection_prompt(interactions)
        
        # Generate reflection
        reflection = model_manager.generate_response(prompt, "")
        
        # Save reflection in history
        self.self_reflections.append(reflection)
        
        logger.info(f"Reflection generated: {reflection[:100]}...")
        return reflection

    def _prepare_reflection_prompt(self, interactions: List[Dict[str, Any]]) -> str:
        """Prepares a prompt for generating reflection.
        
        Args:
            interactions: List of interactions to reflect on
            
        Returns:
            Prompt for the model
        """
        prompt = "Reflect on the following interactions. "
        prompt += "Consider patterns in user questions, the quality of your answers, "
        prompt += "areas for improvement, and what you can learn from these interactions.\n\n"
        
        # Add each interaction to the prompt
        for i, interaction in enumerate(interactions):
            content = interaction.get("content", "")
            response = interaction.get("response", "")
            prompt += f"Interaction {i+1}:\n"
            prompt += f"Query: {content}\n"
            prompt += f"Response: {response}\n\n"
        
        prompt += "Your reflection:"
        
        return prompt

    def get_metacognitive_knowledge(self) -> Dict[str, Any]:
        """Gets the current metacognitive knowledge of the system.
        
        Returns:
            Dictionary containing the system's metacognitive knowledge
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
        """Integrates reflections with long-term memory.
        
        Args:
            memory_manager: MemoryManager instance for storing reflections
        """
        logger.info("Integrating reflections with long-term memory")
        
        # Save all reflections that haven't been saved yet
        # In a real implementation, we could keep track of 
        # which reflections have already been integrated with memory
        for reflection in self.self_reflections:
            memory_manager.store_reflection(reflection)

    def evaluate_with_external_model(self, model_manager: Any, memory_manager: Any) -> Dict[str, float]:
        """Performs system evaluation using an external model.
        
        Args:
            model_manager: ModelManager instance for generating evaluation
            memory_manager: MemoryManager instance for accessing interactions
            
        Returns:
            Dictionary with evaluation results
        """
        logger.info("Performing external evaluation of the system")
        
        # Get a set of recent interactions for evaluation
        interactions = memory_manager.retrieve_recent_interactions(10)
        
        # Prepare prompt for the evaluation model
        prompt = self._prepare_evaluation_prompt(interactions)
        
        # Generate evaluation in JSON format
        response = model_manager.generate_response(prompt, "")
        
        try:
            # Parse the response as JSON
            evaluation = json.loads(response)
            logger.info(f"External evaluation: {evaluation}")
            return evaluation
        except json.JSONDecodeError:
            logger.error(f"Error parsing JSON response: {response}")
            # Return default values in case of error
            return {metric: 0.5 for metric in self.self_improvement_metrics}

    def _prepare_evaluation_prompt(self, interactions: List[Dict[str, Any]]) -> str:
        """Prepares a prompt for generating evaluation by an external model.
        
        Args:
            interactions: List of interactions to evaluate
            
        Returns:
            Prompt for the model
        """
        prompt = "As an objective AI evaluator, assess the quality of the system's responses in the following interactions. "
        prompt += f"Return an evaluation in the range of 0-1 for each of the following criteria: {', '.join(self.self_improvement_metrics)}. "
        prompt += "The evaluation should be returned in JSON format.\n\n"
        
        # Add each interaction to the prompt
        for i, interaction in enumerate(interactions):
            content = interaction.get("content", "")
            response = interaction.get("response", "")
            prompt += f"Interaction {i+1}:\n"
            prompt += f"Query: {content}\n"
            prompt += f"Response: {response}\n\n"
        
        prompt += "Your evaluation in JSON format (e.g., {\"accuracy\": 0.8, \"relevance\": 0.9, \"coherence\": 0.85, \"creativity\": 0.7}):"
        
        return prompt

    def create_self_improvement_plan(self, model_manager: Any) -> str:
        """Creates a self-improvement plan based on reflections and evaluations.
        
        Args:
            model_manager: ModelManager instance for generating the plan
            
        Returns:
            Self-improvement plan in text form
        """
        logger.info("Creating self-improvement plan")
        
        # Prepare input data
        reflection_summary = "\n".join(self.self_reflections[-3:]) if self.self_reflections else "No reflections."
        insights_summary = "\n".join(self.insights_from_discoveries[-3:]) if self.insights_from_discoveries else "No discoveries."
        
        # Prepare prompt
        prompt = "Based on the following reflections and discoveries, create a specific self-improvement plan "
        prompt += "that will help the system enhance its capabilities and overcome limitations.\n\n"
        prompt += f"Recent reflections:\n{reflection_summary}\n\n"
        prompt += f"Recent insights from discoveries:\n{insights_summary}\n\n"
        prompt += "The plan should include specific steps to take, areas for improvement, "
        prompt += "and ways to implement these enhancements. Format: numbered list of specific actions.\n\n"
        prompt += "Self-improvement plan:"
        
        # Generate plan
        plan = model_manager.generate_response(prompt, "")
        
        logger.info(f"Self-improvement plan generated: {plan[:100]}...")
        return plan

    def update_interaction_count(self) -> None:
        """Updates the interaction counter after each new interaction."""
        self.interaction_count += 1

    def process_discoveries(self, model_manager: Any, discoveries: List[Dict[str, Any]]) -> List[str]:
        """Processes internet discoveries, drawing insights for meta-awareness.
        
        Args:
            model_manager: ModelManager instance for generating insights
            discoveries: List of internet discoveries
            
        Returns:
            List of insights
        """
        logger.info(f"Processing {len(discoveries)} internet discoveries")
        
        insights = []
        
        for discovery in discoveries:
            # Prepare prompt
            prompt = "Analyze the following discovery and indicate what insights can be drawn from it "
            prompt += "for your meta-awareness and understanding of your own thought processes:\n\n"
            prompt += f"Topic: {discovery.get('topic', '')}\n"
            prompt += f"Content: {discovery.get('content', '')}\n"
            prompt += f"Source: {discovery.get('source', '')}\n\n"
            prompt += "Your insights for meta-awareness:"
            
            # Generate insights
            insight = model_manager.generate_response(prompt, "")
            insights.append(insight)
            
            # Save the insight
            self.insights_from_discoveries.append(insight)
        
        logger.info(f"Generated {len(insights)} insights from discoveries")
        return insights