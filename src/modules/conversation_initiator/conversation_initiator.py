"""Module for initiating conversations with users."""

import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger("SKYNET-SAFE.ConversationInitiator")

class ConversationInitiator:
    """Class responsible for initiating conversations with users."""

    def __init__(self, config: Dict[str, Any]):
        """Initialization of the conversation initiator with configuration.
        
        Args:
            config: Configuration for the conversation initiator containing parameters such as
                   min_time_between_initiations, init_probability, topics_of_interest, etc.
        """
        self.config = config
        self.min_time_between_initiations = config.get("min_time_between_initiations", 3600)  # seconds
        self.init_probability = config.get("init_probability", 0.3)
        self.topics_of_interest = config.get("topics_of_interest", ["AI", "meta-awareness", "machine learning"])
        self.max_daily_initiations = config.get("max_daily_initiations", 5)
        
        # History of initiated conversations (timestamps)
        self.initiated_conversations = []
        
        logger.info(f"Conversation initiator initialized with {self.init_probability=}, topics: {self.topics_of_interest}")

    def should_initiate_conversation(self) -> bool:
        """Checks if a conversation should be initiated.
        
        Returns:
            True if the system should initiate a conversation, False otherwise
        """
        # Random factor - initiation probability
        if random.random() > self.init_probability:
            logger.debug("Initiation probability threshold not reached")
            return False
        
        # Check if the minimum time since last initiation has passed
        current_time = datetime.now()
        if self.initiated_conversations:
            last_initiation = max(self.initiated_conversations)
            time_since_last = (current_time - last_initiation).total_seconds()
            
            if time_since_last < self.min_time_between_initiations:
                logger.debug(f"Too early for a new initiation, only {time_since_last} seconds have passed")
                return False
        
        # Check if we haven't exceeded the daily initiation limit
        today = current_time.date()
        today_initiations = sum(1 for ts in self.initiated_conversations 
                               if ts.date() == today)
        
        if today_initiations >= self.max_daily_initiations:
            logger.debug(f"Daily initiation limit exceeded: {today_initiations}/{self.max_daily_initiations}")
            return False
        
        logger.info("Conditions for conversation initiation have been met")
        return True

    def get_topic_for_initiation(self, discoveries: List[Dict[str, Any]]) -> Union[str, Dict[str, Any]]:
        """Selects a topic for conversation initiation.
        
        Args:
            discoveries: List of discoveries from the internet module
            
        Returns:
            Conversation topic (string or dictionary with discovery)
        """
        if discoveries:
            # If we have discoveries, randomly choose one of them
            logger.info(f"Selecting topic from {len(discoveries)} available discoveries")
            return random.choice(discoveries)
        else:
            # If we don't have discoveries, randomly choose one of the topics of interest
            logger.info("No discoveries, selecting topic from predefined interests")
            return random.choice(self.topics_of_interest)

    def generate_initiation_message(self, model_manager: Any, topic: Union[str, Dict[str, Any]]) -> str:
        """Generates a message to initiate conversation.
        
        Args:
            model_manager: ModelManager instance for generating responses
            topic: Conversation topic (string or dictionary with discovery)
            
        Returns:
            Generated initiation message
        """
        if isinstance(topic, dict):
            # If we have a full discovery, use its content
            topic_content = topic.get("content", "")
            topic_name = topic.get("topic", "")
            system_prompt = (
                f"You are tasked with creating a natural conversation starter about '{topic_name}'. "
                f"Based on this information: '{topic_content}'. "
                f"Generate only a short, natural opening message that will interest the user in this topic. "
                f"Don't mention that you 'found information', but naturally refer to this topic. "
                f"Respond with ONLY the message, no explanations or additional text."
            )
        else:
            # If we only have a topic name
            system_prompt = (
                f"You are tasked with creating a natural conversation starter about '{topic}'. "
                f"Generate only a short, natural opening message that will interest the user in this topic. "
                f"Respond with ONLY the message, no explanations or additional text."
            )
        
        # Import MODEL_PROMPT to maintain base persona identity
        from src.config.config import MODEL_PROMPT
        
        # Use the model's internal prompt formatting with system/user/assistant tokens
        # Include MODEL_PROMPT so model knows it's Lira, then add specific task instructions
        formatted_prompt = f"<|begin_of_text|><|system|>\n{MODEL_PROMPT}\n\n{system_prompt}\n<|user|>\nGenerate the conversation starter message now.\n<|assistant|>\n"
        
        logger.info(f"Generating initiation message for topic: {topic}")
        
        # Directly use the tokenizer and model to get clean output - bypass persona system entirely
        input_ids = model_manager.tokenizer.encode(formatted_prompt, return_tensors="pt").to(model_manager.model.device)
        
        # Generate response with same parameters as model_manager from config
        gen_kwargs = {
            "temperature": model_manager.config.get('temperature', 0.7),
            "do_sample": model_manager.config.get('do_sample', True),
            "max_new_tokens": model_manager.config.get('max_new_tokens', 150),
            "min_length": model_manager.config.get('min_length', 10),
            "pad_token_id": model_manager.tokenizer.eos_token_id,
            "repetition_penalty": model_manager.config.get('repetition_penalty', 1.2),
            "no_repeat_ngram_size": model_manager.config.get('no_repeat_ngram_size', 3)
        }
        
        import torch
        with torch.no_grad():
            outputs = model_manager.model.generate(input_ids, **gen_kwargs)
        
        # Decode and extract only the assistant response
        generated_text = model_manager.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the part after <|assistant|>
        if "<|assistant|>" in generated_text:
            message = generated_text.split("<|assistant|>")[-1].strip()
        else:
            # Fallback - remove the original prompt
            message = generated_text[len(formatted_prompt):].strip()
        
        # Clean up any remaining artifacts
        message = message.replace("<|end_of_text|>", "").strip()
        
        return message if message else "Cześć! Mam dla Ciebie ciekawą informację."

    def initiate_conversation(self, model_manager: Any, communication_interface: Any, 
                              discoveries: List[Dict[str, Any]], recipients: List[str]) -> bool:
        """Initiates conversation with users.
        
        Args:
            model_manager: ModelManager instance for generating responses
            communication_interface: Communication interface for sending messages
            discoveries: List of discoveries from the internet module
            recipients: List of recipient identifiers
            
        Returns:
            True if the conversation was initiated, False otherwise
        """
        # Check if we should initiate a conversation
        if not self.should_initiate_conversation():
            return False
        
        # Select a topic
        topic = self.get_topic_for_initiation(discoveries)
        
        # Generate a message
        message = self.generate_initiation_message(model_manager, topic)
        
        # Send the message to all recipients
        success = False
        for recipient in recipients:
            logger.info(f"Initiating conversation with {recipient} on topic: {topic}")
            # Send the message through all available communication channels
            result = communication_interface.send_message(recipient, message)
            if result:
                success = True
        
        # Record the initiation time only if the message was sent successfully
        if success:
            self.initiated_conversations.append(datetime.now())
            return True
        
        return False