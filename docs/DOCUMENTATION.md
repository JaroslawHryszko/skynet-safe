# SKYNET-SAFE: Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Key Components](#key-components)
4. [Data Flows](#data-flows)
5. [Installation Guide](#installation-guide)
6. [Configuration](#configuration)
7. [Extending the System](#extending-the-system)
8. [Security Considerations](#security-considerations)
9. [Best Practices](#best-practices)

## Overview

SKYNET-SAFE is a comprehensive artificial intelligence system designed to develop meta-awareness capabilities while maintaining strong safety and ethical guardrails. The system uses local open source language models with 4k token context support to provide intelligent responses, while developing a sophisticated understanding of its own operation through a suite of specialized modules.

The system autonomously explores information, reflects on its interactions, adapts to user needs, and maintains a consistent persona - all while ensuring security, ethical compliance, and continuous improvement.

## System Architecture

SKYNET-SAFE follows a modular architecture with the following layers:

1. **Core Layer** - Essential processing modules including model management, memory, and communication
2. **Adaptive Layer** - Learning and personalization capabilities
3. **Meta-awareness Layer** - Self-reflection and improvement processes
4. **Security Layer** - Safety mechanisms, ethical constraints, and monitoring systems

These layers interact with each other to create a system that can:
- Process and respond to user inputs across multiple communication platforms
- Maintain long-term memory of interactions and knowledge
- Reflect on its own performance and improve over time
- Operate safely within defined ethical boundaries

## Key Components

### Model Management Module
- Manages the local language model (supporting 4k context and instruction following)
- Handles tokenization, context preparation, and response generation
- Optimizes performance through quantization (4-bit for standard deployment)

### Memory Management System
The memory system stores and retrieves information using a vector database (ChromaDB) for semantic search capabilities.

**Key Features:**
- **Comprehensive Interaction Storage**: Stores both user messages and system responses
- **Semantic Search**: Retrieves relevant past interactions based on meaning rather than just keywords
- **Paired Data Storage**: Maintains relationships between questions and answers
- **Reflection Storage**: Keeps track of system's self-reflections separately from interactions

**Data Storage Process:**
1. User messages are stored in the interactions collection with appropriate metadata
2. System responses are stored and linked to the original user messages
3. System reflections are stored in a separate reflections collection
4. All text is converted to vector embeddings for semantic search

**Retrieval Methods:**
- `retrieve_relevant_context()`: Finds semantically similar past interactions
- `retrieve_last_interactions()`: Returns recent interactions with both user messages and system responses paired together
- `retrieve_recent_interactions()`: Alias for backward compatibility

### Communication Interface
- Supports multiple platforms (Console, Signal, Telegram)
- Handles message reception and delivery
- Manages platform-specific formatting and protocols

### Internet Explorer
- Performs autonomous internet searches on relevant topics
- Processes and stores discovered information
- Provides discovery-based learning opportunities

### Learning Manager
- Adapts the model based on interactions
- Manages model checkpoints and training processes
- Evaluates improvements in response quality

### Conversation Initiator
- Autonomously starts conversations based on discoveries
- Manages conversation timing and frequency
- Selects topics of interest from a configured list

### Persona Manager
- Maintains a consistent identity for the system
- Adapts persona traits based on interactions
- Persists persona state across system restarts

### Meta-awareness Components
- **Meta-awareness Manager**: Reflects on interactions and system operation
- **Self-Improvement Manager**: Experiments with improvements based on reflections
- **External Evaluation Manager**: Uses external validation to assess system quality

### Security Components
- **Security System Manager**: Enforces security policies and monitors for violations
- **Development Monitor**: Tracks development of the system for concerning patterns
- **Correction Mechanism**: Corrects potentially problematic responses
- **External Validation**: Uses external systems to validate operations
- **Ethical Framework**: Applies ethical constraints to all responses

## Data Flows

### Basic Interaction Flow
1. User sends a message through a communication platform
2. System validates and sanitizes input
3. Memory system provides relevant context from past interactions
4. Model generates a response with persona and ethical considerations
5. Both the user message and system response are stored in memory
6. Response is delivered to the user

### Self-Reflection Flow
1. After a configured number of interactions, system triggers reflection
2. Memory system retrieves recent interactions (paired questions and answers)
3. Model analyzes its own performance and generates reflection
4. Reflection is stored in memory for future reference
5. Self-improvement experiments are designed based on reflections

### Autonomous Discovery Flow
1. System selects topics of interest for exploration
2. Internet Explorer module performs searches
3. Discoveries are processed and stored
4. System may initiate conversations based on discoveries
5. Persona and meta-awareness systems adapt based on discoveries

## Installation Guide

For complete installation instructions, please refer to the [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) file.

## Configuration

SKYNET-SAFE is highly configurable through two main mechanisms:

1. The `src/config/config.py` file for general configuration
2. A `.env` file for sensitive tokens and credentials

### Environment Variables (.env)

Sensitive information like API keys and tokens should be stored in a `.env` file in the project root directory. This file is not committed to version control for security reasons.

Example `.env` file:
```
# SKYNET-SAFE environment variables
# This file contains sensitive tokens and credentials
# Do not commit this file to version control

# Telegram Configuration
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
TELEGRAM_TEST_CHAT_ID="your_test_chat_id"

# External API Keys
ANTHROPIC_API_KEY="your_anthropic_api_key"

# Signal Configuration
SIGNAL_PHONE_NUMBER="+1234567890"
```

### Model Configuration
```python
MODEL = {
    "base_model": "/path/to/local/model",  # Path to local open-source model
    "max_length": 4096,  # Maximum context length (in tokens)
    "temperature": 0.7,  # Generation temperature (higher = more creative)
    "do_sample": True,  # Required for temperature parameter to work
    "quantization": "4bit",  # Quantization level for efficiency (8bit, 4bit, none)
    "use_local_files_only": True  # Use only local files, no downloads
}
```

### Memory Configuration
```python
MEMORY = {
    "vector_db_type": "chroma",  # Vector database type
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",  # Model for generating embeddings
    "memory_path": "./data/memory"  # Path for storing memory data
}
```

### Communication Configuration
```python
COMMUNICATION = {
    "platform": "telegram",  # Communication platform (console, signal, telegram)
    "check_interval": 10,  # Seconds between checking for new messages
    "response_delay": 1.5,  # Seconds to wait before responding
    
    # Platform-specific settings
    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),  # From .env file
    "telegram_allowed_users": "",  # List of allowed user IDs (empty = all)
    "signal_phone_number": os.getenv("SIGNAL_PHONE_NUMBER", ""),  # From .env file
    "signal_config_path": "/path/to/signal/config"
}
```

For more detailed configuration options, see comments in the `config.py` file.

## Extending the System

SKYNET-SAFE is designed for extensibility. Common extension points include:

### Adding a New Communication Platform
1. Create a new handler class in `src/modules/communication/handlers/`
2. Implement the required methods: `initialize()`, `get_new_messages()`, `send_message()`, and `close()`
3. Register the handler in `communication_interface.py`
4. Add platform-specific configuration in `config.py`

### Enhancing Memory Capabilities
1. Extend the `MemoryManager` class in `src/modules/memory/memory_manager.py`
2. Consider adding new collections for specialized data types
3. Implement new retrieval methods as needed
4. Update existing methods to handle new data formats

### Improving Meta-awareness
1. Add new reflection types in `metawareness_manager.py`
2. Implement specialized prompts for different types of analysis
3. Create new integration points between reflection and learning

## Security Considerations

SKYNET-SAFE implements multiple layers of security:

1. **Input Validation**: All inputs are validated and sanitized
2. **Rate Limiting**: Prevents excessive usage
3. **Content Filtering**: Blocks harmful or inappropriate content
4. **Response Verification**: Checks generated responses for safety
5. **Ethical Framework**: Applies ethical constraints to all operations
6. **Development Monitoring**: Tracks system behavior for concerning patterns
7. **External Validation**: Uses external systems to validate operations

## Best Practices

### Memory Management
- Regularly back up the memory directories
- Consider implementing periodic cleaning of old, less relevant interactions
- Monitor vector database size growth over time

### Model Management
- Use the included `prepare_model.py` script to properly set up models
- Consider using 4-bit quantization for optimal performance/quality balance
- Periodically check for model updates or improvements

### 24/7 Operation
- Use the daemon mode for background operation
- For production environments, use the systemd integration
- Set up proper monitoring using the included monitoring scripts
- Configure regular backups using the backup script

### Security
- Regularly review security settings
- Update allowed domains list as needed
- Review security logs for potential issues
- Periodically run external validation tests

For more detailed information on specific components, please refer to the individual documentation files listed in the [README.md](README.md).