"""Script for running SKYNET-SAFE system in test mode."""

import os
import time
import logging
import json
from datetime import datetime

from src.modules.communication.handlers.console_handler import ConsoleHandler
from src.main import SkynetSystem
from src.config import config

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("skynet_test.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("SKYNET-TEST")


def setup_test_environment():
    """Prepare the test environment."""
    # Create directories if they don't exist
    os.makedirs("./data/memory", exist_ok=True)
    
    # Modify configuration for tests
    test_config = {
        "MODEL": config.MODEL,
        "MEMORY": config.MEMORY,
        "COMMUNICATION": {
            "platform": "console",  # Use console handler for tests
            "check_interval": 2,
            "response_delay": 0.5
        },
        "INTERNET": config.INTERNET
    }
    
    # Prepare test messages
    sample_messages = [
        {"sender": "user1", "content": "Hello, can you hear me?", "timestamp": int(time.time())},
        {"sender": "user1", "content": "What can you do?", "timestamp": int(time.time()) + 10},
        {"sender": "user2", "content": "What do you know about artificial intelligence?", "timestamp": int(time.time()) + 20}
    ]
    
    # Save test messages to file
    with open("console_messages.json", "w") as f:
        json.dump(sample_messages, f, indent=2)
    
    logger.info("Test environment prepared successfully")
    return test_config


def main():
    """Main test function."""
    logger.info("Starting SKYNET-SAFE system test...")
    
    # Prepare test environment
    test_config = setup_test_environment()
    
    try:
        # Initialize system with test configuration
        system = SkynetSystem(test_config)
        
        # Run system in test mode - only a few iterations
        logger.info("Running system in test mode...")
        
        # Simulate several main loop cycles
        for i in range(5):
            logger.info(f"Test cycle {i+1}/5")
            
            # Receive messages
            messages = system.communication.receive_messages()
            
            for message in messages:
                # Process message and generate response
                response = system.process_message(message)
                
                # Send response
                system.communication.send_message(message["sender"], response)
            
            # Short pause between cycles
            time.sleep(1)
            
            # Add new test message (only after 3rd cycle)
            if i == 2:
                ConsoleHandler.add_test_message(
                    "user1", 
                    "What do you think about your ability to self-improve?", 
                    int(time.time())
                )
        
        # Cleanup
        system._cleanup()
        logger.info("Test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        raise


if __name__ == "__main__":
    main()
