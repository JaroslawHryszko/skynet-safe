"""Language model management module."""

import logging
from typing import Dict, List, Any, Optional

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch

logger = logging.getLogger(__name__)


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
        # Prepare context for the prompt
        prompt = self._prepare_prompt(query, context)
        
        # Encode the prompt
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.model.device)
        
        # Generate response
        try:
            # Set a generation config that doesn't cause infinite loops
            gen_kwargs = {
                "max_length": self.config.get('max_length', 2048),
                "temperature": self.config.get('temperature', 0.7),
                "do_sample": self.config.get('do_sample', True),
                "num_return_sequences": 1,
                "pad_token_id": self.tokenizer.eos_token_id,
                # Add these parameters to prevent infinite loops
                "max_new_tokens": 1024,  # Limit new tokens
                "min_length": 10,        # Ensure some output
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
            
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm sorry, there was a technical problem generating the response."
    
    def _prepare_prompt(self, query: str, context: Optional[List[str]]) -> str:
        """Prepare prompt from query and context.
        
        Args:
            query: User query
            context: Optional context to include
            
        Returns:
            Complete prompt for the model
        """
        # Check if we're using Llama-3 model
        model_name = self.config.get('base_model', '').lower()
        
        if "llama-3" in model_name:
            # Prompt format for Llama-3
            if not context or len(context) == 0:
                # Standard Llama-3 format without context
                return f"<|begin_of_text|><|system|>\nYou are a helpful AI assistant named Lira. Answer the user's query in a helpful and accurate way. Be concise yet informative.\n<|user|>\n{query}\n<|assistant|>\n"
            
            # With context
            context_str = "\n".join([f"- {item}" for item in context])
            return f"<|begin_of_text|><|system|>\nYou are a helpful AI assistant named Lira. Use the following context to answer the user's query.\nContext:\n{context_str}\n<|user|>\n{query}\n<|assistant|>\n"
        else:
            # Default format for other models
            if not context or len(context) == 0:
                # Simple prompt without context
                return f"Question: {query}\n\nAnswer:"
            
            # Prepare context
            context_str = "\n".join([f"- {item}" for item in context])
            return f"Context:\n{context_str}\n\nQuestion: {query}\n\nAnswer:"
    
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
        
        if "llama-3" in model_name:
            # For Llama-3, the response begins after <|assistant|>
            if "<|assistant|>" in generated_text:
                response = generated_text.split("<|assistant|>")[1].strip()
                
                # Remove end marker if present
                if "<|end_of_text|>" in response:
                    response = response.split("<|end_of_text|>")[0].strip()
                
                return response
            else:
                # If we can't find the assistant marker, return everything minus the prompt
                return generated_text[len(prompt):].strip()
        else:
            # Standard response extraction for other models
            # Remove prompt from generated text
            if generated_text.startswith(prompt):
                response = generated_text[len(prompt):].strip()
            else:
                # If for some reason the prompt is not a prefix
                response = generated_text
                
            return response
