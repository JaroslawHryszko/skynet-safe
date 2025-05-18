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
            prompt = (
                f"I want to start an interesting conversation with a user about '{topic_name}'. "
                f"I found the following information: '{topic_content}'. "
                f"Generate a short, natural opening message that will interest the user in this topic. "
                f"Don't mention that you 'found information', but naturally refer to this topic."
            )
        else:
            # If we only have a topic name
            prompt = (
                f"I want to start an interesting conversation with a user about '{topic}'. "
                f"Generate a short, natural opening message that will interest the user in this topic."
            )
        
        logger.info(f"Generating initiation message for topic: {topic}")
        message = model_manager.generate_response(prompt, "")
        return message

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