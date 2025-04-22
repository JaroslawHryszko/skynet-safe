"""Language model management module."""

import logging
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import re

from src.config.config import MODEL_PROMPT

# Import the consolidated cleanup function
from src.utils.text_cleanup import cleanup_model_output

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Setup dedicated logger for LLM interactions
llm_logger = logging.getLogger("LLM_INTERACTIONS")
llm_logger.setLevel(logging.INFO)

# Get log directory from .env
log_dir = os.getenv("LOG_DIR", "/opt/skynet-safe/logs")

# Create logs directory if it doesn't exist
os.makedirs(log_dir, exist_ok=True)

# Setup handler for main system log file as well
main_log_file = os.path.join(log_dir, "skynet.log")

# Add a file handler specifically for LLM interactions
llm_handler = logging.FileHandler(os.path.join(log_dir, "llm_interactions.log"))
llm_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
llm_logger.addHandler(llm_handler)

# Add a handler to also log LLM interactions to the main system log
main_handler = logging.FileHandler(main_log_file)
main_handler.setFormatter(logging.Formatter('%(asctime)s - LLM_INTERACTION - %(levelname)s - %(message)s'))
llm_logger.addHandler(main_handler)


class ModelManager:
    """Class for managing the language model."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the language model.
        
        Args:
            config: Model configuration containing model name, generation parameters, etc.
        """
        self.config = config
        logger.info(f"Initializing language model {config['base_model']}...")
        
        # Apply quantization if configured
        quantization_config = None
        if 'quantization' in config and config['quantization'] == '4bit':
            logger.info("Applying 4-bit quantization for efficient operation on available hardware")
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True
            )
        
        # Load model and tokenizer
        try:
            # Prepare common parameters
            use_local_files = 'use_local_files_only' in config and config['use_local_files_only']
            if use_local_files:
                logger.info(f"Using only local files for model {config['base_model']}")
            
            # Parameters only for from_pretrained method (not for model constructor)
            pretrained_kwargs = {}
            if use_local_files:
                pretrained_kwargs["use_local_files_only"] = True
            
            # Parameters for model constructor
            model_kwargs = {
                "device_map": "auto",
            }
            
            # Add quantization configuration to model parameters
            if quantization_config:
                model_kwargs["quantization_config"] = quantization_config
            
            # Parameters for tokenizer
            tokenizer_kwargs = {}
            if use_local_files:
                tokenizer_kwargs["use_local_files_only"] = True
            
            logger.info(f"Loading model {config['base_model']}...")
            
            # Use try/except to handle various possible errors
            try:
                # First try with all parameters
                self.model = AutoModelForCausalLM.from_pretrained(
                    config['base_model'],
                    **model_kwargs,
                    **pretrained_kwargs
                )
            except TypeError as e:
                if "got an unexpected keyword argument 'use_local_files_only'" in str(e):
                    logger.warning("Model does not support 'use_local_files_only' parameter, trying without it")
                    # Try again without use_local_files_only
                    self.model = AutoModelForCausalLM.from_pretrained(
                        config['base_model'],
                        **model_kwargs
                    )
                else:
                    raise
            
            logger.info(f"Loading tokenizer for {config['base_model']}...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                config['base_model'],
                **tokenizer_kwargs
            )
            
            # Make sure the tokenizer has pad_token
            if self.tokenizer.pad_token is None:
                logger.warning("Tokenizer doesn't have a pad token, setting it to eos_token")
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info(f"Model {config['base_model']} loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def generate_response(self, query: str, context: List[str] = None) -> str:
        """Generate a response based on the query and optional context.
        
        Args:
            query: User query
            context: Optional context from memory to consider in generation
            
        Returns:
            Generated response as a string
        """
        # Record the start time
        start_time = datetime.now()
        
        # Convert empty string context to empty list
        if context == "":
            context = []
            
        # Prepare context for the prompt
        prompt = self._prepare_prompt(query, context)
        
        # Encode the prompt
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.model.device)
        
        # Generate response
        try:
            # Set a generation config that doesn't cause infinite loops
            gen_kwargs = {
                "temperature": self.config.get('temperature', 0.5),
                "do_sample": self.config.get('do_sample', True),
                "num_return_sequences": 1,
                "pad_token_id": self.tokenizer.eos_token_id,
                # Add these parameters to prevent infinite loops
                "max_new_tokens": self.config.get('max_new_tokens', 512),  # Limit new tokens
                "min_length": self.config.get('min_length', 2),        # Ensure some output
                "repetition_penalty": 1.2,  # Penalize repetition
                "no_repeat_ngram_size": 3  # Prevent repeating 3-grams
            }
            
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    **gen_kwargs
                )
            
            # Decode the response
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract the response from the full generated text
            response = self._extract_response(generated_text, prompt)
            
            # Record end time and calculate duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Log the interaction with timestamp in structured format
            interaction_log = {
                "timestamp": end_time.isoformat(),
                "query": query,
                "context_length": len(context) if context else 0,
                "response": response,
                "duration_seconds": duration,
                "model": self.config.get('base_model', 'unknown')
            }
            
            # Log as JSON for easy parsing
            llm_logger.info(json.dumps(interaction_log))
            
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            
            # Log the error in interaction log
            error_log = {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "context_length": len(context) if context else 0,
                "error": str(e),
                "model": self.config.get('base_model', 'unknown')
            }
            llm_logger.error(json.dumps(error_log))
            
            return "I'm sorry, there was a technical problem generating the response."
    
    def _prepare_prompt(self, query: str, context: Optional[List[str]]) -> str:
        """Prepare prompt from query and context.
        
        Args:
            query: User query
            context: Optional context to include
            
        Returns:
            Complete prompt for the model
        """
        if not context:
            return f"<|begin_of_text|><|system|>\n{MODEL_PROMPT}\n<|user|>\n{query}\n<|assistant|>\n"

        context_str = "\n".join(f"- {item}" for item in context)
        return f"<|begin_of_text|><|system|>\n{MODEL_PROMPT}\n\nContext:\n{context_str}\n<|user|>\n{query}\n<|assistant|>\n"
    
    def _extract_response(self, generated_text: str, prompt: str) -> str:
        """Extract response from the full generated text.
        
        Args:
            generated_text: Full text generated by the model
            prompt: Original prompt
            
        Returns:
            Extracted response
        """
        # Check if we're using Llama-3 model
        model_name = self.config.get('base_model', '').lower()
        
        # Checking if the model is damaged or 'abliterated' Llama-3
        if "failspy" in model_name or "abliterated" in model_name:
            # Special processing for damaged Llama-3 models
            logger.warning("Detected problematic model output, applying special cleanup")
            
            # Improved answer extraction - try to extract answer using stronger pattern matching
            if "<|assistant|>" in generated_text:
                response = generated_text.split("<|assistant|>")[1].strip()
                if "<|end_of_text|>" in response:
                    response = response.split("<|end_of_text|>")[0].strip()
            elif "Answer (as Lira):" in generated_text:
                response = generated_text.split("Answer (as Lira):")[1].strip()
            elif generated_text.startswith(prompt):
                response = generated_text[len(prompt):].strip()
            else:
                # Fallback - try to find answer after the last occurrence of the query in the text
                # This helps when the prompt is reformatted but query is still there
                query_parts = prompt.split("Question: ")
                if len(query_parts) > 1:
                    user_query = query_parts[-1].split("\n")[0].strip()
                    if user_query in generated_text:
                        last_query_pos = generated_text.rfind(user_query)
                        if last_query_pos >= 0:
                            answer_start = last_query_pos + len(user_query)
                            # Find next newline after the query
                            next_nl = generated_text.find("\n", answer_start)
                            if next_nl >= 0:
                                response = generated_text[next_nl:].strip()
                            else:
                                response = generated_text[answer_start:].strip()
                        else:
                            response = generated_text
                    else:
                        response = generated_text
                else:
                    response = generated_text
            
            # Clean up garbage markers
            return self._cleanup_response(response)
            
        elif "llama-3" in model_name:
            # For standard Llama-3, the response begins after <|assistant|>
            if "<|assistant|>" in generated_text:
                response = generated_text.split("<|assistant|>")[1].strip()
                
                # Remove end marker if present
                if "<|end_of_text|>" in response:
                    response = response.split("<|end_of_text|>")[0].strip()
                
                # Check if the response contains garbage markers that need cleaning
                if self._is_corrupted_output(response):
                    logger.warning("Detected corrupted output from Llama-3 model, applying cleanup")
                    return self._cleanup_response(response)
                
                return response
            else:
                # If we can't find the assistant marker, check for prompt patterns
                if "Question: " in generated_text and "Answer (as Lira):" in generated_text:
                    # Try to extract text after the answer marker
                    parts = generated_text.split("Answer (as Lira):")
                    if len(parts) > 1:
                        response = parts[1].strip()
                    else:
                        # If splitting somehow failed, use the default approach
                        response = generated_text[len(prompt):].strip()
                else:
                    # If we can't find any markers, just remove the prompt
                    response = generated_text[len(prompt):].strip()
                
                # Check if the response needs cleaning
                if self._is_corrupted_output(response):
                    logger.warning("Detected corrupted output from Llama-3 model, applying cleanup")
                    return self._cleanup_response(response)
                
                return response
        else:
            # Standard response extraction for other models
            # Try to find common answer patterns first
            if "Answer (as Lira):" in generated_text:
                parts = generated_text.split("Answer (as Lira):")
                if len(parts) > 1:
                    response = parts[1].strip()
                else:
                    # If splitting somehow failed, use prompt removal
                    if generated_text.startswith(prompt):
                        response = generated_text[len(prompt):].strip()
                    else:
                        # Last resort - return raw output, but log a warning
                        logger.warning("Could not reliably extract model response, may contain prompt text")
                        response = generated_text
            else:
                # If no answer marker found, try prompt removal
                if generated_text.startswith(prompt):
                    response = generated_text[len(prompt):].strip()
                else:
                    # Try to extract response after the query
                    query_parts = prompt.split("Question: ")
                    if len(query_parts) > 1:
                        user_query = query_parts[-1].split("\n")[0].strip()
                        if user_query in generated_text:
                            last_query_pos = generated_text.rfind(user_query)
                            if last_query_pos >= 0:
                                answer_start = last_query_pos + len(user_query)
                                # Look for "Answer", newline, or just use everything after query
                                answer_marker = generated_text.find("Answer", answer_start)
                                next_nl = generated_text.find("\n", answer_start)
                                if answer_marker >= 0:
                                    response = generated_text[answer_marker:].strip()
                                    # If there's "Answer (as Lira):" extract what follows
                                    if "Answer (as Lira):" in response:
                                        response = response.split("Answer (as Lira):")[1].strip()
                                elif next_nl >= 0:
                                    response = generated_text[next_nl:].strip()
                                else:
                                    response = generated_text[answer_start:].strip()
                            else:
                                # If we can't find the query, log a warning and return raw output
                                logger.warning("Failed to extract response by query matching")
                                response = generated_text
                        else:
                            logger.warning("Query not found in generated text")
                            response = generated_text
                    else:
                        # No clear way to extract response, log a warning
                        logger.warning("No reliable markers to extract response, may contain prompt")
                        response = generated_text
                
            # Check if the response needs cleaning
            if self._is_corrupted_output(response):
                logger.warning("Detected corrupted output, applying cleanup")
                return self._cleanup_response(response)
                
            return response
    
    def _is_corrupted_output(self, text: str) -> bool:
        """Check if the model output contains garbage markers that need cleaning.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if the text needs cleaning, False otherwise
        """
        import re
        
        # List of patterns identifying corrupted output
        corruption_patterns = [
            # Nested code markers or tags
            r'```[^`]*```',
            r'`{3,}',
            # HTML/XML style tags
            r'</?[A-Za-z]+/?>',
            # Nested parentheses with paths
            r'/[A-Za-z/_.]+/',
            # Multiple parentheses, braces, etc.
            r'[\)\}\(\{\[\]]{3,}',
            # Markers like (Lira:)
            r'\([A-Za-z]+:?\)',
            # Lines containing mainly invalid characters
            r'\|+\s*\|+',
            # Specific markers from damaged models
            r'=====',
            r'\(/+\)',
            r'\(\*\)',
            r'/LIRA/',
            # Additional patterns detected in logs
            r'```\n\n```',
            r'\(\*\)\s*\(\*\)',
            r'\(\s*\`\s*```\)',
            r'\s*/\)\s*```',
            r'}\s*}\s*}',
            r'\*\*\*\.\*\*\*',
            r'<[/]?lira[/]?>',
            r'<[/]?assistant[/]?>',
            r'\(\.\*\.\*\.\)',
            r'[a-zA-Z]+[/][a-zA-Z]+[/][a-zA-Z]+',
            r'\("`"\)',
            r'\.{3,}',
            r'\("`"\)',
            r'\("```\)',
            r'/usr/local/bin',
            r'<\w+/>'
        ]
        
        # Check for pattern occurrences in the text
        for pattern in corruption_patterns:
            if re.search(pattern, text):
                return True
        
        # Check the proportion of special characters to the entire text
        special_chars = len(re.findall(r'[^\w\s]', text))
        total_length = len(text)
        
        # If the proportion of special characters is too high, the text needs cleaning
        if total_length > 0 and special_chars / total_length > 0.25:
            return True
        
        return False
    
    def _cleanup_response(self, text: str) -> str:
        """Clean response from damaged models by removing garbage markers.
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text
        """        
        logger.info("Cleaning corrupted model response")
        
        # Keep original length for logging
        original_length = len(text)
        
        # Use the consolidated cleanup function
        cleaned_text = cleanup_model_output(text, aggressive=True)
        
        # If the cleanup returned a significantly shorter text, log the reduction
        if len(cleaned_text) < original_length * 0.5:
            logger.info(f"Significant cleanup: {original_length} chars -> {len(cleaned_text)} chars")
        
        return cleaned_text