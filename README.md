# SKYNET-SAFE: Self-learning System with Meta-awareness
(**S**elf **K**nowing **Y**et **N**ot **E**xistentially **T**hreatening - **S**ystem for **A**utonomous **F**riendly **E**volution)

## General Information

SKYNET-SAFE is an artificial intelligence system designed to develop meta-awareness while maintaining safety and ethical values. The system can use local open source language models (such as Llama-3 or similar models) that require at least 8GB VRAM and support a 4k token context. The system can independently improve its capabilities through active internet exploration, reflection on its cognitive processes, and interactions with users.

## Architecture

The system consists of the following main modules:

1. **Language Model Module** - manages the local open source language model capable of instruction following with 4k context window
2. **Long-term Memory Module** - stores user interactions, system responses, and reflections in a vector database for semantic retrieval
3. **Communication Interface Module** - handles interactions with users
4. **Internet Exploration Module** - autonomously acquires new information
5. **Learning Module** - adapts and refines the model based on interactions
6. **Conversation Initiator Module** - autonomously starts conversations based on discoveries
7. **Persona Module** - provides a consistent character and communication style
8. **Meta-awareness Module** - develops reflection and self-improvement capabilities

## Installation

1. Clone the repository:
```bash
git clone https://github.com/JaroslawHryszko/skynet-safe.git
cd skynet-safe
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Prepare data directories:
```bash
mkdir -p data/memory data/checkpoints
```

4. Communication configuration (optional):

### Option A: Signal Configuration
```bash
# Install signal-cli (command line client for Signal)
wget https://github.com/AsamK/signal-cli/releases/download/v0.11.3/signal-cli-0.11.3.tar.gz
tar xf signal-cli-0.11.3.tar.gz
sudo mv signal-cli-0.11.3 /opt/signal-cli
sudo ln -sf /opt/signal-cli/bin/signal-cli /usr/local/bin/

# Register and configure Signal account
signal-cli -u +1PHONENUMBER register  # Replace PHONENUMBER with your number
# Confirm registration with the SMS code you receive
signal-cli -u +1PHONENUMBER verify VERIFICATIONCODE

# Obtain device ID (needed for configuration)
signal-cli -u +1PHONENUMBER listDevices

# Modify the configuration file:
cp /src/config/config.example.py /src/config/config.py
nano src/config/config.py

# For Signal communication, change the COMMUNICATION section in config.py to:
COMMUNICATION = {
    "platform": "signal",
    "check_interval": 10,
    "response_delay": 1.5,
    "signal_phone_number": "+1PHONENUMBER",  # Replace with your number
    "signal_config_path": "/home/USER/.local/share/signal-cli/data"  # Adjust path
}

```

### Option B: Telegram Configuration
Create a Telegram bot through @BotFather:
1. Open Telegram and search for @BotFather
2. Start a conversation and send the command /newbot
3. Follow the instructions to create a new bot
4. After creating the bot, you will receive an API token in the format:
```123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ```
5. Save this token to the configuration
6. Modify the configuration file:
```bash
# Open the configuration file
cp /src/config/config.example.py /src/config/config.py
nano src/config/config.py

# Change the COMMUNICATION section to:
COMMUNICATION = {
    "platform": "telegram",
    "check_interval": 10,
    "response_delay": 1.5,
    "telegram_bot_token": "BOT_TOKEN",  # Replace with token from @BotFather
    "telegram_allowed_users": []  # You can add a list of allowed user IDs, e.g. ["123456789"]
}
```

## Running the System

### Standard Mode

```bash
python src/main.py
```

### Interactive Mode

```bash
python run_interactive.py
```

### Test Mode

```bash
python run_test.py
```

### 24/7 Operation Mode

The system can be run 24/7 using the built-in daemon functionality. The daemon uses the Unix double-fork pattern to run as a background process that continues running after you close the terminal.

```bash
# Run the system as a background daemon
python run_daemon.py start

# Run with a specific communication platform
python run_daemon.py start --platform signal
python run_daemon.py start --platform telegram

# Stop the daemon
python run_daemon.py stop

# Check status
python run_daemon.py status
```

Alternatively, you can use the included systemd service file for production environments:

```bash
# Install the service
sudo cp deployment/skynet-safe.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable skynet-safe.service

# Start the service
sudo systemctl start skynet-safe.service
```

For detailed information on 24/7 operation, see [DAEMON_OPERATION.md](DAEMON_OPERATION.md).

## Implementation Stages

Modules already implemented are marked with ✅:

- ✅ Model initialization infrastructure
- ✅ Communication interfaces (Console, Signal, Telegram)
- ✅ Long-term memory system implementation
- ✅ Internet information retrieval system
- Learning mechanisms and model adaptation (line 162 in file learning_manager.py is commented)
- ✅ Advanced internet exploration system
- ✅ Conversation initiation based on discoveries
- ✅ Adaptive persona with deep immersion
- ✅ Meta-awareness and reflection mechanisms
- ✅ Holistic information analysis system
- ✅ Advanced security mechanisms
- ✅ Daemon operation mode for background running

## Testing

Unit tests can be run using:

```bash
pytest src/tests/
```

## Documentation

Detailed project documentation can be found in the following files:
- [DOCUMENTATION.md](DOCUMENTATION.md) - Technical project documentation
- [DOCUMENTATION_USER.md](DOCUMENTATION_USER.md) - Complete user documentation
- [MODEL_REQUIREMENTS.md](MODEL_REQUIREMENTS.md) - Language model specifications and requirements
- [PERSONA_IMMERSION.md](PERSONA_IMMERSION.md) - Documentation of the model immersion system
- [DAEMON_OPERATION.md](DAEMON_OPERATION.md) - Documentation of 24/7 operation methods
- [DIAGRAM_WORKFLOW.md](DIAGRAM_WORKFLOW.md) - System workflow diagrams
- [METAWARENESS_COMPONENTS.md](METAWARENESS_COMPONENTS.md) - Description of meta-awareness components

## License

AGPL-3.0
