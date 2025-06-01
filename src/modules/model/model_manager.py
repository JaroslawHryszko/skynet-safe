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
from src.config import config

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
            logger.info("Model loading in progress... This may take several minutes for large models.")
            
            # Use try/except to handle various possible errors
            try:
                # First try with all parameters
                logger.info("Loading model weights...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    config['base_model'],
                    **model_kwargs,
                    **pretrained_kwargs
                )
                logger.info("Model weights loaded successfully")
            except TypeError as e:
                if "got an unexpected keyword argument 'use_local_files_only'" in str(e):
                    logger.warning("Model does not support 'use_local_files_only' parameter, trying without it")
                    # Try again without use_local_files_only
                    logger.info("Loading model weights...")
                    self.model = AutoModelForCausalLM.from_pretrained(
                        config['base_model'],
                        **model_kwargs
                    )
                    logger.info("Model weights loaded successfully")
                else:
                    raise
            
            logger.info(f"Loading tokenizer for {config['base_model']}...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                config['base_model'],
                **tokenizer_kwargs
            )
            logger.info("Tokenizer loaded successfully")
            
            # Make sure the tokenizer has pad_token
            if self.tokenizer.pad_token is None:
                logger.warning("Tokenizer doesn't have a pad token, setting it to eos_token")
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            logger.info(f"🎉 Model {config['base_model']} loaded successfully! System ready to receive messages.")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            # Try to send error notification if communication interface is available
            try:
                # This will be called from main.py which has access to communication
                self._model_loading_error = str(e)
            except:
                pass
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
            
        # Debug logging to track context usage
        if context:
            logger.debug(f"Using context with {len(context)} items for query: {query[:50]}...")
        else:
            logger.debug(f"No context provided for query: {query[:50]}...")
            
        logger.info(f"PROMPT BEFORE:\n {query}\n {context}")
        # Prepare context for the prompt
        prompt = self._prepare_prompt(query, context)
        
        # Debug log the complete prompt being sent to the model
        logger.info(f"FULL PROMPT SENT TO MODEL:\n{'-'*50}\n{prompt}\n{'-'*50}")
        
        # Encode the prompt
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.model.device)
        
        # Generate response
        try:
            # Set a generation config using parameters from config
            gen_kwargs = {
                "temperature": self.config.get('temperature', 0.7),
                "do_sample": self.config.get('do_sample', True),
                "num_return_sequences": 1,
                "pad_token_id": self.tokenizer.eos_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
                # All parameters from config with sensible defaults
                "max_new_tokens": self.config.get('max_new_tokens', 150),
                "min_length": self.config.get('min_length', 10),
                "repetition_penalty": self.config.get('repetition_penalty', 1.2),
                "no_repeat_ngram_size": self.config.get('no_repeat_ngram_size', 3),
                # New sampling parameters - use more permissive defaults
                "top_p": self.config.get('top_p', 0.95),
                "top_k": self.config.get('top_k', 0),  # 0 = disabled
                # Add stop sequences to prevent over-generation
                "early_stopping": True
            }
            
            # Handle stop sequences if provided
            stop_sequences = self.config.get('stop', [])
            if stop_sequences:
                logger.debug(f"Processing stop sequences: {stop_sequences}")
                # Convert stop sequences to token IDs
                stop_token_ids = []
                for stop_seq in stop_sequences:
                    if isinstance(stop_seq, str):
                        tokens = self.tokenizer.encode(stop_seq, add_special_tokens=False)
                        if tokens:
                            stop_token_ids.extend(tokens)
                
                if stop_token_ids:
                    # Remove duplicates and add to existing eos_token_id
                    existing_stop_ids = [self.tokenizer.eos_token_id] if hasattr(self.tokenizer, 'eos_token_id') else []
                    all_stop_ids = list(set(existing_stop_ids + stop_token_ids))
                    gen_kwargs["eos_token_id"] = all_stop_ids
            
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids,
                    **gen_kwargs
                )
            
            # Decode the response
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Extract the response from the full generated text
            response = self._extract_response(generated_text, prompt)
            
            # Check if response was cut off mid-sentence and try to complete it (if enabled)
            if self.config.get('enable_sentence_completion', False):
                response = self._ensure_sentence_completion(response, input_ids, gen_kwargs)
            
            # Additional cleanup to prevent over-generation
            response = self._prevent_over_generation(response)
            
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
            
            # Store critical error for potential communication
            self._last_critical_error = f"Błąd generowania odpowiedzi: {str(e)}"
            
            return "I'm sorry, there was a technical problem generating the response."
    
    def _prepare_prompt(self, query: str, context: Optional[List[str]]) -> str:
        """Prepare prompt from query and context.
        
        Args:
            query: User query
            context: Optional context to include
            
        Returns:
            Complete prompt for the model
        """
        # If context is empty but not None, it might be an empty list passed as context
        if not context:
            # If context is None or empty list, use basic prompt
            return f"<|begin_of_text|><|system|>\n{MODEL_PROMPT}\n{query}\n<|assistant|>\n"
            
        # Check if the first context item is a persona context (added by PersonaManager)
        # or a regular context item (memory, etc.)
        context_starts_with_persona = (
            len(context) > 0 and isinstance(context[0], str) and 
            (context[0].strip().startswith("You are ") or context[0].strip().startswith("Jesteś "))
        )
        if context_starts_with_persona and config["PERSONA"].get("enable_persona_in_prompt", False):
            # This is a persona context from PersonaManager
            persona_context = context[0]
            remaining_context = context[1:] if len(context) > 1 else []
            
            if remaining_context:
                # We have both persona context and additional memory context
                remaining_context_str = "\n".join(remaining_context)  # Remove "- " prefix for conversation context
                return f"<|begin_of_text|><|system|>\n{MODEL_PROMPT}\n\n{persona_context}\n\n{remaining_context_str}\n<|user|>\n{query}\n<|assistant|>\n"
            else:
                # We only have persona context, no additional memory context
                return f"<|begin_of_text|><|system|>\n{MODEL_PROMPT}\n\n{persona_context}\n<|user|>\n{query}\n<|assistant|>\n"
        else:
            # This is regular context, not persona context
            # Special handling for conversation context (Tata:/Juno: format)
            context_str = "\n".join(context)  # Remove "- " prefix for conversation context
            return f"<|begin_of_text|><|system|>\n{MODEL_PROMPT}\n\n{context_str}\n<|user|>\n{query}\n<|assistant|>\n"
    
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
    
    def _prevent_over_generation(self, response: str) -> str:
        """Prevent over-generation by detecting when model impersonates the father/user.
        
        Args:
            response: Raw response from the model
            
        Returns:
            Response cut off before impersonation occurs
        """
        if not response:
            return response
            
        # Patterns that indicate the model is impersonating Tata/Jarek
        impersonation_patterns = [
            r'\btata\s*:',           # "Tata:" or "tata:"
            r'\bjarek\s*:',          # "Jarek:" or "jarek:"
            r'\btato\s*:',           # "Tato:" - vocative form
            r'<\|user\|>',           # User token
            r'\buser\s*:',           # "User:"
            r'\b[Tt]ata\s+mówi',     # "Tata mówi" or "tata mówi"
            r'\b[Jj]arek\s+mówi',    # "Jarek mówi" or "jarek mówi"
            r'\b[Tt]ata\s+odpowiada', # "Tata odpowiada"
            r'\b[Jj]arek\s+odpowiada' # "Jarek odpowiada"
        ]
        
        # Split response into lines for analysis
        lines = response.split('\n')
        safe_lines = []
        
        for line in lines:
            # Check if this line contains impersonation
            line_lower = line.lower()
            found_impersonation = False
            
            for pattern in impersonation_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    logger.warning(f"Detected impersonation pattern in response: {pattern}")
                    found_impersonation = True
                    break
            
            if found_impersonation:
                # Stop here - don't include this line or any following lines
                break
                
            safe_lines.append(line)
        
        # Rejoin the safe lines
        result = '\n'.join(safe_lines).strip()
        
        # Final check: if the response contains any form of dialogue attribution to Tata/Jarek
        # even within sentences, cut it off
        for pattern in impersonation_patterns:
            match = re.search(pattern, result, re.IGNORECASE)
            if match:
                # Cut off everything from the impersonation pattern onwards
                result = result[:match.start()].strip()
                logger.warning(f"Cut off response at impersonation pattern: {pattern}")
                break
        
        return result
    
    def _ensure_sentence_completion(self, response: str, original_input_ids: torch.Tensor, gen_kwargs: dict) -> str:
        """Ensure response ends at a natural sentence boundary.
        
        Args:
            response: Generated response that might be cut off
            original_input_ids: Original input token IDs
            gen_kwargs: Generation kwargs used
            
        Returns:
            Response completed to sentence boundary if needed
        """
        if not response.strip():
            return response
            
        # Check if response ends mid-sentence (no proper punctuation)
        last_char = response.rstrip()[-1] if response.rstrip() else ""
        sentence_endings = ['.', '!', '?', ':', ';']
        
        # If it already ends properly, return as-is
        if last_char in sentence_endings:
            logger.debug("Response already ends with proper punctuation")
            return response
            
        # Check if it ends with incomplete word or thought
        words = response.strip().split()
        if len(words) < 3:  # Too short to analyze or complete
            return response
            
        logger.debug(f"Response seems cut off mid-sentence, attempting completion")
        
        try:
            # Try to complete the sentence with a small additional generation
            # Reconstruct full prompt with current response
            full_prompt_with_response = self._reconstruct_prompt_with_response(original_input_ids, response)
            
            # Small additional generation to complete the sentence
            completion_input_ids = self.tokenizer.encode(full_prompt_with_response, return_tensors="pt").to(self.model.device)
            
            # Use very limited generation for completion
            completion_kwargs = gen_kwargs.copy()
            max_completion_tokens = self.config.get('sentence_completion_max_tokens', 20)
            completion_kwargs["max_new_tokens"] = max_completion_tokens
            completion_kwargs["do_sample"] = False  # Use greedy for completion
            completion_kwargs["temperature"] = 0.3  # Low temperature for stable completion
            completion_kwargs["top_p"] = 0.7  # More focused completion
            
            with torch.no_grad():
                completion_outputs = self.model.generate(
                    completion_input_ids,
                    **completion_kwargs
                )
            
            # Decode the completion
            full_completion = self.tokenizer.decode(completion_outputs[0], skip_special_tokens=True)
            
            # Extract only the new part (after the original response)
            original_length = len(full_prompt_with_response)
            if len(full_completion) > original_length:
                additional_text = full_completion[original_length:].strip()
                
                # Find the first sentence ending in the additional text
                completion_end = -1
                for i, char in enumerate(additional_text):
                    if char in sentence_endings:
                        completion_end = i + 1
                        break
                
                if completion_end > 0:
                    # Add the completion up to the sentence ending
                    sentence_completion = additional_text[:completion_end]
                    completed_response = response + sentence_completion
                    logger.debug(f"Completed sentence with: '{sentence_completion}'")
                    return completed_response
                else:
                    # If no sentence ending found in short completion, add a period
                    if len(additional_text.strip()) > 0:
                        # Only add text if it seems like a reasonable completion
                        words_in_addition = additional_text.strip().split()
                        if len(words_in_addition) <= 5:  # Only short completions
                            completed_response = response + " " + additional_text.strip() + "."
                            logger.debug(f"Completed and added period: '{additional_text.strip()}'")
                            return completed_response
                    
                    # Fallback: just add period
                    logger.debug("No good completion found, adding period")
                    return response.rstrip() + "."
            else:
                # Completion didn't add anything useful, add a period
                logger.debug("Completion didn't extend text, adding period")
                return response.rstrip() + "."
                
        except Exception as e:
            logger.warning(f"Error during sentence completion: {e}")
            # Fallback: just add a period if response doesn't end with punctuation
            if response.rstrip() and response.rstrip()[-1] not in sentence_endings:
                return response.rstrip() + "."
            return response
    
    def _reconstruct_prompt_with_response(self, original_input_ids: torch.Tensor, response: str) -> str:
        """Reconstruct the full prompt with the generated response for continuation.
        
        Args:
            original_input_ids: Original input token IDs
            response: Generated response so far
            
        Returns:
            Full text for continuation
        """
        try:
            # Decode original prompt
            original_prompt = self.tokenizer.decode(original_input_ids[0], skip_special_tokens=True)
            # Combine with response
            return original_prompt + response
        except Exception as e:
            logger.warning(f"Error reconstructing prompt: {e}")
            # Fallback: just return response (will be less accurate but won't crash)
            return response
