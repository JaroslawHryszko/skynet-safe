"""Communication interface module."""

import logging
import time
from typing import Dict, List, Any, Optional

from src.modules.communication.handlers import get_message_handler

logger = logging.getLogger(__name__)


class CommunicationInterface:
    """Class for managing communication with users."""

    def __init__(self, config: Dict[str, Any]):
        """Initialization of the communication interface.
        
        Args:
            config: Configuration containing the communication platform, check interval, etc.
        """
        self.config = config
        self.platform = config["platform"]
        self.check_interval = config["check_interval"]
        self.response_delay = config.get("response_delay", 0.5)
        
        logger.info(f"Initializing communication interface for platform {self.platform}...")
        
        # Getting the appropriate handler for the platform
        try:
            self.handler = get_message_handler(self.platform, config)
            logger.info(f"Communication interface for platform {self.platform} initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing communication interface: {e}")
            raise
    
    def receive_messages(self) -> List[Dict[str, Any]]:
        """Retrieving new messages from the communication platform.
        
        Returns:
            List of new messages in the format [{"sender": str, "content": str, "timestamp": int}]
        """
        try:
            messages = self.handler.get_new_messages()
            if messages and len(messages) > 0:
                logger.info(f"Received {len(messages)} new messages")
            return messages
        except Exception as e:
            logger.error(f"Error receiving messages: {e}")
            return []
    
    def send_message(self, recipient: str, content: str) -> bool:
        """Sending a message to a recipient.
        
        Args:
            recipient: Recipient identifier
            content: Message content
            
        Returns:
            True if sending succeeded, False otherwise
        """
        try:
            # Short pause before responding to simulate thinking time
            if self.response_delay > 0:
                time.sleep(self.response_delay)
                
            success = self.handler.send_message(recipient, content)
            if success:
                logger.info(f"Message sent to {recipient}")
            else:
                logger.warning(f"Failed to send message to {recipient}")
            return success
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def send_system_message(self, content: str, message_type: str = "INFO") -> bool:
        """Sends system message to the configured platform.
        
        Args:
            content: System message content
            message_type: Type of message (INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            True if sending succeeded, False otherwise
        """
        try:
            # Format system message with type indicator
            formatted_message = f"🤖 [{message_type}] {content}"
            
            # Get default recipient based on platform
            default_recipient = self._get_default_recipient()
            if not default_recipient:
                logger.warning("No default recipient configured for system messages")
                return False
            
            success = self.handler.send_message(default_recipient, formatted_message)
            if success:
                logger.info(f"System message ({message_type}) sent successfully")
            else:
                logger.warning(f"Failed to send system message ({message_type})")
            return success
        except Exception as e:
            logger.error(f"Error sending system message: {e}")
            return False
    
    def _get_default_recipient(self) -> Optional[str]:
        """Get default recipient for system messages based on platform.
        
        Returns:
            Default recipient identifier or None if not configured
        """
        if self.platform == "console":
            return "user"  # Console always sends to user
        elif self.platform == "telegram":
            # Try different config keys for Telegram chat ID
            chat_id = (self.config.get("telegram_test_chat_id") or 
                      self.config.get("telegram_chat_id") or
                      self.config.get("chat_id"))
            if not chat_id:
                logger.warning("No Telegram chat ID configured for system messages")
            return chat_id
        elif self.platform == "signal":
            phone = (self.config.get("signal_phone_number") or 
                    self.config.get("phone_number"))
            if not phone:
                logger.warning("No Signal phone number configured for system messages")
            return phone
        else:
            logger.warning(f"Unknown platform for system messages: {self.platform}")
            return None
    
    def close(self) -> None:
        """Closing the connection and cleaning up resources."""
        try:
            self.handler.close()
            logger.info(f"Communication interface for platform {self.platform} has been closed")
        except Exception as e:
            logger.error(f"Error closing communication interface: {e}")
