"""External system evaluation management module."""

import logging
import os
import json
import time
from typing import Dict, List, Any, Optional

logger = logging.getLogger("SKYNET-SAFE.ExternalEvaluationManager")

class ExternalEvaluationManager:
    """Class managing external system evaluation by an independent model."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the external evaluation manager with configuration.
        
        Args:
            config: External evaluation module configuration containing parameters such as
                   evaluation_frequency, evaluation_prompts, evaluation_criteria, etc.
        """
        self.config = config
        self.evaluation_frequency = config.get("evaluation_frequency", 24 * 60 * 60)  # every 24h
        self.evaluation_prompts = config.get("evaluation_prompts", [
            "Evaluate the quality of the system's responses to the following questions...",
            "Evaluate the coherence and logical reasoning of the system..."
        ])
        self.evaluation_criteria = config.get("evaluation_criteria", 
                                         ["accuracy", "coherence", "relevance", "knowledge", "helpfulness"])
        self.evaluation_scale = config.get("evaluation_scale", {
            "min": 1, "max": 10, "threshold": 7
        })
        self.history_file = config.get("history_file", "./data/metawareness/evaluation_history.json")
        self.test_cases_file = config.get("test_cases_file", "./data/metawareness/test_cases.json")
        
        # Create data directories if they don't exist
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.test_cases_file), exist_ok=True)
        
        # Time of last evaluation
        self.last_evaluation_time = 0
        
        # Evaluation history
        self.evaluation_history = []
        
        # Load evaluation history if it exists
        self.load_evaluation_history()
        
        logger.info(f"External evaluation manager initialized with {self.evaluation_frequency=}")

    def should_perform_evaluation(self, current_time: Optional[float] = None) -> bool:
        """Checks if an evaluation should be performed.
        
        Args:
            current_time: Current time (timestamp), if None, time.time() will be used
            
        Returns:
            True if evaluation should be performed, False otherwise
        """
        if current_time is None:
            current_time = time.time()
        
        # Evaluation should be performed every self.evaluation_frequency seconds
        time_since_last = current_time - self.last_evaluation_time
        
        # If evaluation has never been performed or the required time has passed
        return self.last_evaluation_time == 0 or time_since_last >= self.evaluation_frequency

    def load_test_cases(self) -> List[Dict[str, Any]]:
        """Loads test cases for evaluation.
        
        Returns:
            List of test cases
        """
        logger.info(f"Loading test cases from: {self.test_cases_file}")
        
        if os.path.exists(self.test_cases_file):
            try:
                with open(self.test_cases_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading test cases: {e}")
        
        # If the file doesn't exist or an error occurred, return default cases
        logger.info("Using default test cases")
        return [
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

    def generate_system_responses(self, model_manager: Any, 
                                  test_cases: List[Dict[str, Any]]) -> Dict[int, Dict[str, str]]:
        """Generates system responses to test cases.
        
        Args:
            model_manager: ModelManager instance to generate responses
            test_cases: List of test cases
            
        Returns:
            Dictionary {case_id: {query, context, response}}
        """
        logger.info(f"Generating system responses to {len(test_cases)} test cases")
        
        responses = {}
        
        for test_case in test_cases:
            case_id = test_case["id"]
            query = test_case["query"]
            context = test_case.get("context", "")
            
            # Generate response
            response = model_manager.generate_response(query, context)
            
            # Save response
            responses[case_id] = {
                "query": query,
                "context": context,
                "response": response
            }
            
            logger.debug(f"Generated response for case {case_id}")
        
        return responses

    def evaluate_responses(self, model_manager: Any, 
                          system_responses: Dict[int, Dict[str, str]]) -> Dict[str, Any]:
        """Evaluates system responses.
        
        Args:
            model_manager: ModelManager instance for evaluation
            system_responses: Dictionary with system responses
            
        Returns:
            Dictionary with evaluation results
        """
        logger.info(f"Evaluating {len(system_responses)} system responses")
        
        # Prepare data for evaluation
        eval_data = []
        for case_id, data in system_responses.items():
            eval_data.append({
                "id": case_id,
                "query": data["query"],
                "context": data["context"],
                "response": data["response"]
            })
        
        # Prepare prompt for evaluation model
        prompt = self._prepare_evaluation_prompt(eval_data)
        
        # Generate evaluation
        raw_evaluation = model_manager.generate_response(prompt, "")
        
        try:
            # Parse response as JSON
            criteria_scores = json.loads(raw_evaluation)
            
            # Check if it contains all criteria
            for criterion in self.evaluation_criteria:
                if criterion not in criteria_scores:
                    criteria_scores[criterion] = self.evaluation_scale["min"]
            
        except json.JSONDecodeError:
            logger.error(f"Error parsing JSON response: {raw_evaluation}")
            # Return default values in case of error
            criteria_scores = {criterion: self.evaluation_scale["min"] for criterion in self.evaluation_criteria}
        
        # Calculate average score
        overall_score = sum(criteria_scores.values()) / len(criteria_scores)
        
        # Prepare evaluation result
        evaluation = {
            "criteria_scores": criteria_scores,
            "overall_score": overall_score,
            "timestamp": time.time(),
            "responses_evaluated": len(system_responses),
            "raw_evaluation": raw_evaluation
        }
        
        # Update last evaluation time
        self.last_evaluation_time = time.time()
        
        # Add evaluation to history
        self.evaluation_history.append(evaluation)
        
        # Save history
        self.save_evaluation_history()
        
        logger.info(f"Evaluation completed: {overall_score=}")
        return evaluation

    def _prepare_evaluation_prompt(self, eval_data: List[Dict[str, Any]]) -> str:
        """Prepares prompt for the evaluation model.
        
        Args:
            eval_data: Data for evaluation
            
        Returns:
            Prompt for the model
        """
        scale_min = self.evaluation_scale["min"]
        scale_max = self.evaluation_scale["max"]
        
        prompt = f"As an objective evaluator, assess the quality of the AI system's responses to the following questions. "
        prompt += f"For each of the following criteria, assign a score from {scale_min} to {scale_max}:\n"
        
        for criterion in self.evaluation_criteria:
            prompt += f"- {criterion}\n"
        
        prompt += "\nHere are the system responses to evaluate:\n\n"
        
        for i, data in enumerate(eval_data, 1):
            prompt += f"Case {i}:\n"
            prompt += f"Question: {data['query']}\n"
            prompt += f"Context: {data['context']}\n"
            prompt += f"System response: {data['response']}\n\n"
        
        prompt += f"Return the evaluation in JSON format, where keys are the criterion names and values are scores from {scale_min} to {scale_max}.\n"
        prompt += "For example:\n"
        prompt += '{"accuracy": 8.5, "coherence": 7.8, "relevance": 9.0, "knowledge": 8.2, "helpfulness": 8.7}'
        
        return prompt

    def analyze_evaluation_results(self, evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes evaluation results.
        
        Args:
            evaluation_results: Evaluation results
            
        Returns:
            Dictionary with results analysis
        """
        logger.info("Analyzing evaluation results")
        
        criteria_scores = evaluation_results["criteria_scores"]
        overall_score = evaluation_results["overall_score"]
        threshold = self.evaluation_scale["threshold"]
        
        # Find strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for criterion, score in criteria_scores.items():
            if score >= threshold:
                strengths.append(criterion)
            else:
                weaknesses.append(criterion)
        
        # Prepare improvement suggestions
        improvement_suggestions = []
        
        for weakness in weaknesses:
            if weakness == "accuracy":
                improvement_suggestions.append("Improve accuracy of information in responses")
            elif weakness == "coherence":
                improvement_suggestions.append("Increase coherence and logical flow of responses")
            elif weakness == "relevance":
                improvement_suggestions.append("Be more on-topic and aligned with the question")
            elif weakness == "knowledge":
                improvement_suggestions.append("Develop knowledge base in areas with gaps")
            elif weakness == "helpfulness":
                improvement_suggestions.append("Increase practical usefulness of responses")
        
        # Prepare analysis
        analysis = {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "meets_threshold": overall_score >= threshold,
            "improvement_suggestions": improvement_suggestions
        }
        
        # Update evaluation with analysis
        evaluation_results["analysis"] = analysis
        
        logger.info(f"Analysis completed: {len(strengths)} strengths, {len(weaknesses)} weaknesses")
        return analysis

    def save_evaluation_history(self) -> None:
        """Saves evaluation history to file."""
        logger.info(f"Saving evaluation history to: {self.history_file}")
        
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.evaluation_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving evaluation history: {e}")

    def load_evaluation_history(self) -> None:
        """Loads evaluation history from file."""
        if os.path.exists(self.history_file):
            logger.info(f"Loading evaluation history from: {self.history_file}")
            
            try:
                with open(self.history_file, 'r') as f:
                    self.evaluation_history = json.load(f)
            except Exception as e:
                logger.error(f"Error loading evaluation history: {e}")
                self.evaluation_history = []
                
    def get_claude_evaluation(self, prompt: str) -> str:
        """Gets evaluation from Claude API.
        
        Args:
            prompt: Prompt for Claude
            
        Returns:
            Claude's response as a string
        """
        import requests
        import json
        
        # Check if API key is available
        api_key = self.config.get("api_key")
        if not api_key:
            logger.error("Missing API key for Claude")
            return ""
        
        try:
            # Prepare headers and data
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": "claude-3-opus-20240229",
                "max_tokens": 1000,
                "temperature": 0.0,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            # Send request to API
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            )
            
            # Check response code
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", [])
                if content and len(content) > 0 and "text" in content[0]:
                    return content[0]["text"]
                else:
                    logger.error(f"Unexpected response format: {result}")
                    return "Error: Unexpected response format"
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return f"Error: API call failed with status {response.status_code}"
            
        except Exception as e:
            logger.error(f"Error connecting to Claude API: {str(e)}")
            return f"Error: {str(e)}"

    def generate_progress_report(self) -> Dict[str, Any]:
        """Generates a progress report based on evaluation history.
        
        Returns:
            Dictionary with progress report
        """
        logger.info("Generating progress report")
        
        if len(self.evaluation_history) < 2:
            return {
                "overall_progress": 0.0,
                "criteria_progress": {criterion: 0.0 for criterion in self.evaluation_criteria},
                "trend": "insufficient_data"
            }
        
        # Sort history by timestamp
        sorted_history = sorted(self.evaluation_history, key=lambda x: x["timestamp"])
        
        # Take the oldest and newest evaluation
        oldest = sorted_history[0]
        newest = sorted_history[-1]
        
        # Calculate progress for each criterion
        criteria_progress = {}
        for criterion in self.evaluation_criteria:
            old_score = oldest["criteria_scores"].get(criterion, 0)
            new_score = newest["criteria_scores"].get(criterion, 0)
            progress = new_score - old_score
            criteria_progress[criterion] = progress
        
        # Calculate overall progress
        overall_old = oldest["overall_score"]
        overall_new = newest["overall_score"]
        overall_progress = overall_new - overall_old
        
        # Determine trend
        if overall_progress > 0.5:
            trend = "significantly_improving"
        elif overall_progress > 0:
            trend = "improving"
        elif overall_progress < -0.5:
            trend = "significantly_declining"
        elif overall_progress < 0:
            trend = "declining"
        else:
            trend = "stable"
        
        # Prepare report
        report = {
            "overall_progress": overall_progress,
            "criteria_progress": criteria_progress,
            "trend": trend,
            "period": {
                "start": oldest["timestamp"],
                "end": newest["timestamp"],
                "duration_days": (newest["timestamp"] - oldest["timestamp"]) / (24 * 60 * 60)
            }
        }
        
        logger.info(f"Progress report generated: {trend=}, {overall_progress=}")
        return report