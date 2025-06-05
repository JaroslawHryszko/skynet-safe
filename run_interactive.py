#!/usr/bin/env python3
"""
Interactive mode for SKYNET-SAFE system.
Enables direct communication with the system through the console.
"""

import os
import logging
import time
import argparse
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.main import SkynetSystem
from src.config import config
from src.modules.communication.handlers.console_handler import ConsoleHandler

# Parse command line arguments
parser = argparse.ArgumentParser(description='SKYNET-SAFE Interactive Mode')
parser.add_argument('-v', '--verbose', action='store_true', 
                    help='Enable verbose logging output to console')
args = parser.parse_args()

# Logger configuration
log_dir = os.getenv("LOG_DIR", "./logs")
log_file_path = os.path.join(log_dir, "skynet_interactive.log")

# Ensure log directory exists
os.makedirs(log_dir, exist_ok=True)

# Configure logging based on verbose flag
if args.verbose:
    # Verbose mode: show logs on console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()
        ]
    )
else:
    # Quiet mode: only log to file, not console
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path)
        ]
    )
    # Disable all console output from all loggers
    logging.getLogger().handlers = [logging.FileHandler(log_file_path)]
    # Set all existing loggers to only use file handler
    for name in logging.Logger.manager.loggerDict:
        logger_obj = logging.getLogger(name)
        logger_obj.handlers = [logging.FileHandler(log_file_path)]
        logger_obj.propagate = False
    
    # Completely suppress all stdout except for our controlled output
    class QuietStdout:
        def __init__(self):
            self.original_stdout = sys.stdout
            
        def write(self, text):
            # Only allow our controlled output (response)
            pass
            
        def flush(self):
            pass
            
        def restore_for_input(self):
            sys.stdout = self.original_stdout
            
        def suppress_again(self):
            sys.stdout = self
    
    # Store original stdout for input and response output
    original_stdout = sys.stdout
    quiet_stdout = QuietStdout()

logger = logging.getLogger("SKYNET-INTERACTIVE")


def setup_environment():
    """Prepare the environment before execution."""
    # Create directories if they don't exist
    os.makedirs("./data/memory", exist_ok=True)
    
    # Modify configuration for interactive mode
    interactive_config = {
        "SYSTEM_SETTINGS": config.SYSTEM_SETTINGS,
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
    
    # Suppress stdout in quiet mode
    if not args.verbose:
        sys.stdout = quiet_stdout
    
    try:
        # Initialize system
        system = SkynetSystem(interactive_config)
        
        # Restore stdout for our controlled output
        if not args.verbose:
            sys.stdout = original_stdout
        
        if args.verbose:
            print("\n" + "="*70)
            print(" SKYNET-SAFE Interactive Mode ".center(70, "="))
            print("="*70)
            print(" Type 'exit' or 'quit' to end the session ".center(70, "-"))
            print(" Use -v or --verbose for detailed logging ".center(70, "-"))
            print("="*70)
        
        # Main interaction loop
        user_id = "user"  # Default user identifier
        
        while True:
            # Get message from user
            user_input = input("You: " if args.verbose else "")
            
            # Check if user wants to exit
            if user_input.lower() in ['exit', 'quit']:
                if args.verbose:
                    print("\nEnding session...\n")
                system._cleanup()
                break
            
            # Add message to console_messages.json file
            timestamp = int(time.time())
            ConsoleHandler.add_test_message(user_id, user_input, timestamp)
            
            # Receive messages
            messages = system.communication.receive_messages()
            
            for message in messages:
                # Suppress stdout during processing in quiet mode
                if not args.verbose:
                    sys.stdout = quiet_stdout
                
                # Process message and generate response
                if args.verbose:
                    print("\nSKYNET processing message...")
                response = system.process_message(message)
                
                # Store response in memory (same as in main.py daemon mode)
                system.memory.store_response(response, message)
                
                # Restore stdout and display response
                if not args.verbose:
                    sys.stdout = original_stdout
                
                # Display response (without sending through communication system)
                if args.verbose:
                    print(f"\n{response}\n")
                else:
                    print(response)
        
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
