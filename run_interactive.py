#!/usr/bin/env python3
"""
Interactive mode for SKYNET-SAFE system.
Enables direct communication with the system through the console.
"""

import os
import logging
import time
from datetime import datetime

from src.main import SkynetSystem
from src.config import config
from src.modules.communication.handlers.console_handler import ConsoleHandler

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("skynet_interactive.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("SKYNET-INTERACTIVE")


def setup_environment():
    """Prepare the environment before execution."""
    # Create directories if they don't exist
    os.makedirs("./data/memory", exist_ok=True)
    
    # Modify configuration for interactive mode
    interactive_config = {
        "MODEL": config.MODEL,
        "MEMORY": config.MEMORY,
        "COMMUNICATION": {
            "platform": "console",  # Use console handler
            "check_interval": 1,
            "response_delay": 0.5
        },
        "INTERNET": config.INTERNET,
        "LEARNING": config.LEARNING,
        "CONVERSATION_INITIATOR": config.CONVERSATION_INITIATOR,
        "PERSONA": config.PERSONA,
        "METAWARENESS": config.METAWARENESS,
        "SELF_IMPROVEMENT": config.SELF_IMPROVEMENT,
        "EXTERNAL_EVALUATION": config.EXTERNAL_EVALUATION,
        "SECURITY_SYSTEM": config.SECURITY_SYSTEM,
        "DEVELOPMENT_MONITOR": config.DEVELOPMENT_MONITOR,
        "CORRECTION_MECHANISM": config.CORRECTION_MECHANISM,
        "ETHICAL_FRAMEWORK": config.ETHICAL_FRAMEWORK,
        "EXTERNAL_VALIDATION": config.EXTERNAL_VALIDATION
    }
    
    # Remove old message files if they exist
    if os.path.exists("console_messages.json"):
        os.remove("console_messages.json")
    if os.path.exists("skynet_responses.json"):
        os.remove("skynet_responses.json")
    
    logger.info("Interactive environment prepared successfully")
    return interactive_config


def main():
    """Main function for interactive mode."""
    logger.info("Starting SKYNET-SAFE interactive mode...")
    
    # Prepare environment
    interactive_config = setup_environment()
    
    try:
        # Initialize system
        system = SkynetSystem(interactive_config)
        
        print("\n" + "="*70)
        print(" SKYNET-SAFE Interactive Mode ".center(70, "="))
        print("="*70)
        print(" Type 'exit' or 'quit' to end the session ".center(70, "-"))
        print("="*70 + "\n")
        
        # Main interaction loop
        user_id = "user1"  # Default user identifier
        
        while True:
            # Get message from user
            user_input = input("\nYou: ")
            
            # Check if user wants to exit
            if user_input.lower() in ['exit', 'quit']:
                print("\nEnding session...\n")
                system._cleanup()
                break
            
            # Add message to console_messages.json file
            timestamp = int(time.time())
            ConsoleHandler.add_test_message(user_id, user_input, timestamp)
            
            # Receive messages
            messages = system.communication.receive_messages()
            
            for message in messages:
                # Process message and generate response
                print("\nSKYNET processing message...")
                response = system.process_message(message)
                
                # Display response (without sending through communication system)
                print(f"\nSKYNET: {response}\n")
        
    except KeyboardInterrupt:
        logger.info("System stopped by user...")
        system._cleanup()
    except Exception as e:
        logger.error(f"Error during interactive mode: {e}")
        if 'system' in locals():
            system._cleanup()
        raise


if __name__ == "__main__":
    main()