"""Script for running SKYNET-SAFE system in test mode."""

import os
import time
import logging
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.modules.communication.handlers.console_handler import ConsoleHandler
from src.main import SkynetSystem
from src.config import config

# Logger configuration
log_dir = os.getenv("LOG_DIR", "./logs")
log_file_path = os.path.join(log_dir, "skynet_test.log")

# Ensure log directory exists
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
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
        "SYSTEM_SETTINGS": config.SYSTEM_SETTINGS,
        "MODEL": config.MODEL,
        "MEMORY": config.MEMORY,
        "COMMUNICATION": {
            "platform": "console",  # Use console handler for tests
            "check_interval": 2,
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
        
        # Display status of security and ethics systems
        security_status = []
        if not test_config["SYSTEM_SETTINGS"].get("enable_security_system", True):
            security_status.append("SecuritySystemManager: DISABLED")
        if not test_config["SYSTEM_SETTINGS"].get("enable_ethical_framework", True):
            security_status.append("EthicalFrameworkManager: DISABLED")
        if not test_config["SYSTEM_SETTINGS"].get("enable_development_monitor", True):
            security_status.append("DevelopmentMonitorManager: DISABLED")
        if not test_config["SYSTEM_SETTINGS"].get("enable_external_validation", True):
            security_status.append("ExternalValidationManager: DISABLED")
            
        if security_status:
            logger.warning("Security/Ethics Components Disabled:")
            for status in security_status:
                logger.warning(f"- {status}")
        
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
