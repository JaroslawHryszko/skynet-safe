"""Message handler for Telegram platform."""

import logging
import time
import os
import requests
import json
from typing import Dict, List, Any, Optional

from src.modules.communication.handlers.base_handler import MessageHandler

logger = logging.getLogger("SKYNET-SAFE.TelegramHandler")


class TelegramHandler(MessageHandler):
    """Message handler for Telegram platform using Telegram Bot API.
    
    Uses Telegram Bot API to communicate with Telegram users.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Telegram handler.
        
        Args:
            config: Configuration for the Telegram handler containing bot_token and other parameters
        """
        super().__init__(config)
        logger.info("Initializing Telegram message handler...")
        
        # Get configuration
        self.bot_token = config.get("telegram_bot_token")
        if not self.bot_token:
            raise ValueError("Missing bot token in Telegram configuration")
            
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.polling_timeout = config.get("telegram_polling_timeout", 30)
        self.allowed_users = config.get("telegram_allowed_users", [])
        self.chat_state_file = config.get("telegram_chat_state_file", "./data/telegram/chat_state.json")
        
        # Create directories if they don't exist
        os.makedirs(os.path.dirname(self.chat_state_file), exist_ok=True)
        
        # Initialize chat state
        self.chats = {}
        self.load_chat_state()
        
        # Last seen update_id
        self.last_update_id = 0
        self.last_update_id_file = os.path.join(os.path.dirname(self.chat_state_file), "last_update_id.txt")
        
        # Try to load last update ID from file
        self._load_last_update_id()
        
        # Check if the bot is working
        try:
            response = requests.get(f"{self.api_url}/getMe")
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get("ok"):
                    bot_name = bot_info["result"].get("username")
                    logger.info(f"Telegram Bot connected successfully: @{bot_name}")
                else:
                    logger.error(f"Error connecting to Telegram API: {bot_info.get('description')}")
                    raise ConnectionError(f"Telegram API error: {bot_info.get('description')}")
            else:
                logger.error(f"Error connecting to Telegram API: {response.status_code}")
                raise ConnectionError(f"Error connecting to Telegram API: {response.status_code}")
        except Exception as e:
            logger.error(f"Error during Telegram bot initialization: {e}")
            raise
        
        logger.info("Telegram message handler initialized successfully")
    
    def get_new_messages(self) -> List[Dict[str, Any]]:
        """Get new messages from Telegram.
        
        Returns:
            List of new messages in format [{"sender": str, "content": str, "timestamp": int}]
        """
        messages = []
        
        try:
            # Get updates from Telegram API
            params = {}
            
            # If we have a last update ID, use it to avoid getting old messages
            if self.last_update_id > 0:
                params["offset"] = self.last_update_id + 1
            else:
                # For first run, we'll use a small limit to avoid loading too many old messages
                params["limit"] = 10
            
            # Add other parameters
            params["timeout"] = self.polling_timeout
            params["allowed_updates"] = ["message"]
            
            response = requests.get(f"{self.api_url}/getUpdates", params=params)
            if response.status_code != 200:
                logger.error(f"Error while getting updates: {response.status_code}")
                return messages
            
            updates = response.json()
            
            if not updates.get("ok"):
                logger.error(f"Telegram API error: {updates.get('description')}")
                return messages
            
            for update in updates.get("result", []):
                update_id = update.get("update_id", 0)
                self.last_update_id = max(self.last_update_id, update_id)
                
                if "message" not in update:
                    continue
                
                message = update["message"]
                
                # Check if message contains text
                if "text" not in message:
                    continue
                
                # Get sender information
                chat_id = str(message.get("chat", {}).get("id", ""))
                user_id = str(message.get("from", {}).get("id", ""))
                username = message.get("from", {}).get("username", "")
                first_name = message.get("from", {}).get("first_name", "")
                last_name = message.get("from", {}).get("last_name", "")
                
                # Check if user is on the allowed list (if the list exists)
                if self.allowed_users and user_id not in self.allowed_users:
                    logger.warning(f"Rejected message from unauthorized user: {user_id} ({username})")
                    continue
                
                # Add user to the list of known chats
                self._add_chat(chat_id, user_id, username, first_name, last_name)
                
                # Add message to the list
                timestamp = message.get("date", int(time.time()))
                content = message.get("text", "")
                
                messages.append({
                    "sender": chat_id,  # We use chat_id as the sender identifier
                    "content": content,
                    "timestamp": timestamp,
                    "metadata": {
                        "user_id": user_id,
                        "username": username,
                        "first_name": first_name,
                        "last_name": last_name
                    }
                })
            
            if messages:
                logger.info(f"Received {len(messages)} new messages from Telegram")
                # Save chat state updates
                self.save_chat_state()
                # Save the last update ID
                self._save_last_update_id()
                
        except Exception as e:
            logger.error(f"Error while getting messages from Telegram: {e}")
        
        return messages
    
    def send_message(self, recipient: str, content: str) -> bool:
        """Send message to recipient via Telegram.
        
        Args:
            recipient: Recipient identifier (chat_id)
            content: Message content
            
        Returns:
            True if sending was successful, False otherwise
        """
        try:
            # Telegram has a message limit around 4096 characters
            max_message_length = 4000  # Safe limit
            
            # If message is longer than the limit, truncate it
            if len(content) > max_message_length:
                # Truncate message to the safe limit
                content = content[:max_message_length]
                logger.info(f"Message truncated to {max_message_length} characters")
            
            # Enhanced security: Sanitize content to prevent potential exploits
            # Remove only non-printable characters (keep Unicode characters like Polish diacritics)
            content = ''.join(char for char in content if ord(char) >= 32 or ord(char) > 127)
            
            # Remove HTML tags using a comprehensive approach
            import re
            content = re.sub(r'<[^>]*>', '', content)  # Remove HTML tags
            
            # We don't escape special characters to preserve Polish diacritics
            
            # Send the message with escaped characters
            return self._send_single_message(recipient, content)
        
        except Exception as e:
            logger.error(f"Error sanitizing or preparing message: {e}")
            return False
            
    def _send_single_message(self, recipient: str, content: str) -> bool:
        """Send message to recipient via Telegram.
        
        Args:
            recipient: Recipient identifier (chat_id)
            content: Message content
            
        Returns:
            True if sending was successful, False otherwise
        """
        try:
            # Prepare data to send
            payload = {
                "chat_id": recipient,
                "text": content
                # Using plain text to preserve Unicode characters including Polish diacritics
            }
            
            # Send message via Telegram API
            response = requests.post(f"{self.api_url}/sendMessage", json=payload)
            
            if response.status_code != 200:
                logger.error(f"Sending message for recipient ID: {recipient}, ERROR: {response.status_code}")
                return False
            
            result = response.json()
            
            if not result.get("ok"):
                logger.error(f"Telegram API error: {result.get('description')}")
                return False
            
            logger.info(f"Message sent via Telegram to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Error while sending message via Telegram: {e}")
            return False
    
    def _add_chat(self, chat_id: str, user_id: str, username: str, first_name: str, last_name: str) -> None:
        """Add or update chat information.
        
        Args:
            chat_id: Chat ID
            user_id: User ID
            username: Username
            first_name: User's first name
            last_name: User's last name
        """
        self.chats[chat_id] = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "last_activity": int(time.time())
        }
    
    def load_chat_state(self) -> None:
        """Load chat state from file."""
        if os.path.exists(self.chat_state_file):
            try:
                with open(self.chat_state_file, 'r') as f:
                    self.chats = json.load(f)
                logger.info(f"Loaded state of {len(self.chats)} chats from {self.chat_state_file}")
            except Exception as e:
                logger.error(f"Error while loading chat state: {e}")
    
    def save_chat_state(self) -> None:
        """Save chat state to file."""
        try:
            with open(self.chat_state_file, 'w') as f:
                json.dump(self.chats, f, indent=2)
            logger.debug(f"Saved state of {len(self.chats)} chats to {self.chat_state_file}")
        except Exception as e:
            logger.error(f"Error while saving chat state: {e}")
    
    def _load_last_update_id(self) -> None:
        """Load last update ID from file."""
        if os.path.exists(self.last_update_id_file):
            try:
                with open(self.last_update_id_file, 'r') as f:
                    self.last_update_id = int(f.read().strip())
                logger.info(f"Loaded last update ID: {self.last_update_id}")
            except Exception as e:
                logger.error(f"Error while loading last update ID: {e}")
    
    def _save_last_update_id(self) -> None:
        """Save last update ID to file."""
        try:
            with open(self.last_update_id_file, 'w') as f:
                f.write(str(self.last_update_id))
            logger.debug(f"Saved last update ID: {self.last_update_id}")
        except Exception as e:
            logger.error(f"Error while saving last update ID: {e}")
    
    def close(self) -> None:
        """Close Telegram connection and cleanup resources."""
        # Save chat state before closing
        self.save_chat_state()
        # Save last update ID
        self._save_last_update_id()
        logger.info("Telegram handler closed")
