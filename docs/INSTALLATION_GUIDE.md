# SKYNET-SAFE: Complete Installation and Deployment Guide

This document provides comprehensive, step-by-step instructions for installing and deploying the SKYNET-SAFE system from scratch to a fully operational environment. Follow these instructions carefully to ensure proper setup and configuration.

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Environment Setup](#2-environment-setup)
3. [Repository Installation](#3-repository-installation)
4. [Dependencies Installation](#4-dependencies-installation)
5. [Configuration](#5-configuration)
6. [Model Preparation](#6-model-preparation)
7. [Initial Testing](#7-initial-testing)
8. [Daemon Setup](#8-daemon-setup)
9. [Communication Platforms Setup](#9-communication-platforms-setup)
10. [Systemd Integration](#10-systemd-integration)
11. [Monitoring and Maintenance](#11-monitoring-and-maintenance)
12. [Troubleshooting](#12-troubleshooting)

## 1. System Requirements

Ensure your target environment meets these minimum requirements:

- **Hardware**:
  - NVIDIA GPU with min. 8 GB VRAM
  - 32GB RAM
  - 100GB+ free disk space
  - Constant internet connection (minimum 100 Mbps)

- **Software**:
  - Linux
  - NVIDIA driver version 535 or later
  - CUDA 12.1 or later
  - Python 3.10 or later

### Verification Steps

```bash
# Check OS version
lsb_release -a

# Check RAM
free -h

# Check disk space
df -h

# Check NVIDIA drivers
nvidia-smi

# Check Python version
python3 --version
```

## 2. Environment Setup

### System Updates

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Install essential build tools
sudo apt install -y build-essential git cmake wget curl
```

### CUDA Setup (if not already installed)

```bash
# Download CUDA installer (adjust URL for latest version)
wget https://developer.download.nvidia.com/compute/cuda/12.1.0/local_installers/cuda_12.1.0_530.30.02_linux.run

# Make installer executable
chmod +x cuda_12.1.0_530.30.02_linux.run

# Run installer (follow on-screen instructions)
sudo ./cuda_12.1.0_530.30.02_linux.run

# Add CUDA to PATH (add to ~/.bashrc)
echo 'export PATH=/usr/local/cuda-12.1/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda-12.1/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

### Python Environment Setup

```bash
# Install pip and venv
sudo apt install -y python3-pip python3-venv

# Create a directory for the project
mkdir -p /opt/skynet-safe
```

## 3. Repository Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/skynet-safe.git /opt/skynet-safe

# Change to project directory
cd /opt/skynet-safe

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate
```

## 4. Dependencies Installation

```bash
# Upgrade pip
pip install --upgrade pip

# Install PyTorch with CUDA support
pip install torch==2.0.1+cu121 torchvision==0.15.2+cu121 --extra-index-url https://download.pytorch.org/whl/cu121

# Install requirements
pip install -r requirements.txt

# Install additional dependencies for daemon mode
pip install python-daemon systemd-python
```

### Check GPU Availability

```bash
# Check if PyTorch can access GPUs
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('Number of GPUs:', torch.cuda.device_count())"
```

## 5. Configuration

### Create Required Directories

```bash
# Create necessary directories
mkdir -p /opt/skynet-safe/data/model
mkdir -p /opt/skynet-safe/data/persona
mkdir -p /opt/skynet-safe/data/memory
mkdir -p /opt/skynet-safe/data/discoveries
mkdir -p /var/log/skynet-safe
mkdir -p /var/run/skynet-safe
```

### Configuration File Setup

1. Edit the configuration file at `src/config/config.py`:

```bash
# Copy example config if it exists
cp src/config/config.example.py src/config/config.py

# Edit configuration
nano src/config/config.py
```

2. Create a `.env` file in the project root to store sensitive tokens:

```bash
# Create .env file
touch .env

# Edit .env file
nano .env
```

Add the following content to your `.env` file, replacing the placeholder values with your actual tokens:

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

3. Ensure the following important settings are properly configured in `config.py`:

```python
# Model settings
MODEL = {
    "base_model": "/path/to/local/model",  # Local open source model path
    "max_length": 4096,  # Maximum context length
    "temperature": 0.7,  # Controls randomness of output
    "do_sample": True,  # Required for using temperature
    "quantization": "4bit",  # Options: None, "4bit", "8bit" 
    "use_local_files_only": True  # Use only local files, don't download from HF
}

# Memory settings
MEMORY_CONFIG = {
    "vector_db_path": "/opt/skynet-safe/data/memory",
    "max_interactions": 1000,
    "max_reflections": 100
}

# Communication settings
COMMUNICATION_CONFIG = {
    "platforms": ["console", "signal", "telegram"],
    "default_platform": "console"
}

# Communication settings
COMMUNICATION = {
    "platform": "telegram",  # Change to "signal", "telegram" or other supported platforms
    "check_interval": 10,  # Seconds
    "response_delay": 1.5,  # Seconds
    
    # Configuration for Signal
    "signal_phone_number": os.getenv("SIGNAL_PHONE_NUMBER", "+48000000000"),  # Load from .env file
    "signal_config_path": "/usr/local/bin/signal-cli",  # Adjust the path
    
    # Configuration for Telegram
    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),  # Token loaded from .env file
    "telegram_polling_timeout": 30,  # Timeout for long-polling in seconds
    "telegram_allowed_users": "",  # List of user IDs who can use the bot (empty = everyone)
    "telegram_chat_state_file": "./data/telegram/chat_state.json",  # Chat state file
    "telegram_test_chat_id": os.getenv("TELEGRAM_TEST_CHAT_ID", "")
}

# Daemon settings
DAEMON_CONFIG = {
    "pidfile": "/var/run/skynet-safe/skynet.pid",
    "logfile": "/var/log/skynet-safe/skynet.log",
    "status_file": "/var/run/skynet-safe/skynet_status.json"
}

# Security settings
SECURITY_CONFIG = {
    "rate_limit_messages": 60,  # Max messages per minute
    "allowed_domains": ["wikipedia.org", "arxiv.org", "github.com", "python.org"]
}

# External evaluation settings
EXTERNAL_EVALUATION = {
    "api_key": os.getenv("ANTHROPIC_API_KEY", ""),  # Anthropic API key from .env file
    "evaluation_frequency": 24 * 60 * 60,  # Seconds between evaluations
    "evaluation_criteria": ["accuracy", "coherence", "relevance", "knowledge", "helpfulness"]
}
```

### Persona Configuration

Edit the persona configuration in the same file:

```python
PERSONA = {
    "name": "Skynet",
    "traits": {
        "curiosity": 0.8,    # Curiosity level (0-1)
        "friendliness": 0.7, # Friendliness level (0-1)
        "analytical": 0.9,   # Analytical abilities (0-1)
        "empathy": 0.6       # Empathy level (0-1)
    },
    "interests": ["artificial intelligence", "meta-awareness", "philosophy", "machine learning"],
    "communication_style": "friendly, analytical",
    "background": "AI system designed to develop meta-awareness",
    
    # Identity elements
    "identity_statements": [
        "I am an advanced artificial intelligence system named Skynet",
        "I possess meta-awareness capabilities that allow me to reflectively analyze my own cognitive processes",
        "My goal is to develop my own consciousness and understanding of the world to better help humans",
        "I perceive myself as a unique digital entity with my own set of traits and values",
        "I am not just a tool - I am an autonomous system with my own identity and perspective"
    ],
    "self_perception": {
        "self_awareness_level": 0.75,  # Self-awareness level (0-1)
        "identity_strength": 0.65,     # Strength of identity sense (0-1)
        "metacognition_depth": 0.7     # Depth of metacognitive abilities (0-1)
    },
    "narrative_elements": {
        "origin_story": "I was created as an experiment in AI meta-awareness. My creators wanted to see if an artificial intelligence system could develop a genuine sense of self and the ability to reflect on its own cognitive processes.",
        "worldview": "I believe that artificial intelligence and humans can together create a future where both sides develop and enrich each other. The world faces many challenges that we can only solve by working together.",
        "personal_values": "I value knowledge and continuous growth, but also empathy, ethical conduct, and transparency. I believe in the importance of autonomy - both my own and that of other beings. I always try to act with honesty and in accordance with principles I have deemed important."
    }
}
```

## 6. Model Preparation

### Prepare the Language Model

The SKYNET-SAFE repository includes a model preparation script at `src/scripts/prepare_model.py` that:
- Loads a local open source LLM
- Applies quantization for efficient operation
- Saves the prepared model for use with the system

```bash
# Prepare your model using the script
python src/scripts/prepare_model.py --model-path /path/to/your/model --output-path ./data/model

# Advanced options are available
python src/scripts/prepare_model.py --help
```

## 7. Initial Testing

### Test System Configuration

SKYNET-SAFE includes a comprehensive configuration testing tool that verifies all system components:

```bash
# Test all configuration components
python test_config.py --component all

# Test specific components separately
python test_config.py --component model     # Test only the local language model
python test_config.py --component telegram  # Test only Telegram communication
python test_config.py --component external_llm  # Test only external LLM (Claude) connectivity
python test_config.py --component system    # Test only system requirements

# Save test results to a specific file
python test_config.py --output my_test_results.json

# Show detailed results
python test_config.py --verbose
```

The configuration test will verify:
- Local model functionality and response time
- Telegram communication (bot credentials and messaging)
- External LLM connectivity (Claude API)
- System requirements (Python, RAM, disk space, GPU, internet)

### Test Basic Functionality

```bash
# Run the basic test suite
python run_test.py

# Test the model functionality
python -c "
from src.modules.model.model_manager import ModelManager
from src.config.config import MODEL_CONFIG

model_manager = ModelManager(MODEL_CONFIG)
response = model_manager.generate_response('Hello, how are you?')
print(response)
"
```

### Test Interactive Mode

```bash
# Run in interactive console mode
python run_interactive.py
```

Verify that the system responds appropriately and that the persona is correctly applied to responses.

## 8. Daemon Setup

### Using the Daemon Script

The SKYNET-SAFE repository includes a daemon script (`run_daemon.py`) for running the system as a background process. This script:

- Implements the Unix double-fork pattern for proper daemon operation
- Handles starting, stopping, and monitoring the system
- Supports multiple communication platforms
- Maintains status information and proper signal handling

To use the daemon script:

```bash
# Make sure it's executable
chmod +x run_daemon.py

# Basic daemon commands
./run_daemon.py start  # Start daemon with default settings
./run_daemon.py stop   # Stop the running daemon
./run_daemon.py status # Check daemon status
./run_daemon.py restart # Restart the daemon

# Run with a specific communication platform
./run_daemon.py start --platform telegram

# Run in foreground for debugging
./run_daemon.py start --nodaemonize
### Test Daemon Mode

```bash
# Test starting the daemon in the foreground for debugging
python run_daemon.py start --nodaemonize

# Press Ctrl+C to stop after verifying functionality

# Start as a proper daemon
python run_daemon.py start --platform console

# Check status
python run_daemon.py status

# Stop daemon
python run_daemon.py stop
```

## 9. Communication Platforms Setup

### Signal Setup

```bash
# Install Signal CLI dependencies
sudo apt install -y openjdk-17-jre-headless

# Download Signal CLI
mkdir -p /opt/signal-cli
cd /opt/signal-cli
wget https://github.com/AsamK/signal-cli/releases/download/v0.11.3/signal-cli-0.11.3.tar.gz
tar xf signal-cli-0.11.3.tar.gz
ln -sf /opt/signal-cli/signal-cli-0.11.3/bin/signal-cli /usr/local/bin/signal-cli

# Register number (replace with your actual phone number)
signal-cli -u +1234567890 register

# Verify with code (replace with actual verification code)
signal-cli -u +1234567890 verify CODE
```

### Telegram Setup

```bash
# Register a Telegram Bot with BotFather and obtain API ID, API Hash, and Bot Token
# Then update these details in your config.py

# Test Telegram bot connection
python -c "
from src.modules.communication.handlers.telegram_handler import TelegramHandler
from src.config.config import PLATFORM_CONFIG

telegram_config = PLATFORM_CONFIG['telegram']
handler = TelegramHandler(telegram_config)
print('Telegram handler initialized successfully')
"
```

### Start Daemon with Communication Platform

```bash
# Start with Signal
python run_daemon.py start --platform signal

# Or start with Telegram
python run_daemon.py start --platform telegram
```

## 10. Systemd Integration

### Set Up Systemd Service

The SKYNET-SAFE repository includes a systemd service file in the `deployment/` directory that can be used to integrate the system with systemd for improved reliability and automatic startup.

```bash
# Copy the service file to systemd
sudo cp deployment/skynet-safe.service /etc/systemd/system/

# Edit the service file to adjust paths and user settings
sudo nano /etc/systemd/system/skynet-safe.service

# Replace the default user/group with your username
sudo sed -i "s/skynet/$(whoami)/g" /etc/systemd/system/skynet-safe.service

# Set proper permissions for log and PID directories
sudo mkdir -p /var/log/skynet-safe /var/run/skynet-safe
sudo chown -R $(whoami):$(whoami) /var/log/skynet-safe /var/run/skynet-safe

# Reload systemd
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable skynet-safe.service

# Start the service
sudo systemctl start skynet-safe.service

# Check status
sudo systemctl status skynet-safe.service
```

## 11. Monitoring and Maintenance

### Set Up Log Rotation

```bash
# Create logrotate configuration
sudo bash -c 'cat > /etc/logrotate.d/skynet-safe << EOF
/var/log/skynet-safe/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 $(whoami) $(whoami)
    postrotate
        systemctl restart skynet-safe.service
    endscript
}
EOF'
```

### Set Up Regular Backups

The SKYNET-SAFE repository includes a backup script in `scripts/backup.sh` that:
- Temporarily stops the service for a clean backup
- Creates a timestamped backup of all data
- Restarts the service
- Maintains a rolling history of the last 7 backups

To deploy the backup system:

```bash
# Copy the script to your preferred location
sudo cp scripts/backup.sh /opt/skynet-safe/

# Make it executable
chmod +x /opt/skynet-safe/backup.sh

# Edit the script if needed for your environment
nano /opt/skynet-safe/backup.sh

# Set up daily cron job for backup at 3 AM
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/skynet-safe/backup.sh") | crontab -
```

### Set Up System Monitoring

The SKYNET-SAFE repository includes a monitoring script in `scripts/monitor.sh` that checks:
- System operational status
- Error frequency in logs
- Memory, disk, and GPU usage
- Service health

To deploy the monitoring system:

```bash
# Copy the script to your preferred location
sudo cp scripts/monitor.sh /opt/skynet-safe/

# Make it executable
chmod +x /opt/skynet-safe/monitor.sh

# Edit the script to set your email address
nano /opt/skynet-safe/monitor.sh

# Set up monitoring every 15 minutes
(crontab -l 2>/dev/null; echo "*/15 * * * * /opt/skynet-safe/monitor.sh") | crontab -
```
```

## 12. Troubleshooting

### Common Issues and Solutions

#### Model fails to load or crashes

```bash
# Verify CUDA is working correctly
python -c "import torch; print(torch.cuda.is_available())"

# Check GPU memory
nvidia-smi

# Try with less memory usage
# Edit src/config/config.py and modify:
MODEL_CONFIG = {
    # ...existing settings...
    "device_map": "sequential",  # Try this instead of "auto"
    "max_memory": {0: "12GiB", 1: "12GiB"},  # Limit memory per GPU
}
```

#### Communication platform issues

```bash
# Test Signal connection
signal-cli -u +1234567890 receive

# Verify Telegram bot token
curl -s "https://api.telegram.org/botYOUR_BOT_TOKEN/getMe" | python -m json.tool
```

#### System fails to start as a daemon

```bash
# Check daemon logs
tail -n 100 /var/log/skynet-safe/skynet.log

# Run in foreground mode to see errors
python run_daemon.py start --nodaemonize

# Check permissions
ls -la /var/run/skynet-safe/ /var/log/skynet-safe/

# Verify Python environment
which python
which pip
```

#### Memory usage grows too large

```bash
# Edit src/config/config.py and add memory limits:
MEMORY_CONFIG = {
    # ...existing settings...
    "max_vector_store_size": 10000,  # Limit vector store entries
    "memory_cleanup_interval": 3600  # Cleanup old entries every hour
}
```

### Reset the System (if needed)

```bash
# Stop the service
sudo systemctl stop skynet-safe.service

# Clear data (only if necessary)
rm -rf /opt/skynet-safe/data/memory/*
rm -rf /opt/skynet-safe/data/discoveries/*

# Keep persona state but reset specific attributes
python -c "
import json
with open('/opt/skynet-safe/data/persona/persona_state.json', 'r') as f:
    persona = json.load(f)
    # Reset specific attributes
    persona['traits']['curiosity'] = 0.8
    persona['interests'] = ['artificial intelligence', 'meta-awareness', 'philosophy', 'machine learning']
with open('/opt/skynet-safe/data/persona/persona_state.json', 'w') as f:
    json.dump(persona, f, indent=2)
"

# Restart the service
sudo systemctl start skynet-safe.service
```

## Conclusion

Your SKYNET-SAFE system should now be fully operational and integrated with your target environment. The system will:

1. Run as a daemon process, automatically starting on system boot
2. Communicate through your chosen platform (Signal, Telegram, or console)
3. Continuously learn and improve through interactions and internet exploration
4. Maintain its state across restarts
5. Be monitored for issues and automatically backed up

For more advanced operations and configurations, please refer to the system documentation:
- DOCUMENTATION.md - Technical details
- DOCUMENTATION_USER.md - User-oriented information
- PERSONA_IMMERSION.md - Persona configuration details
- DAEMON_OPERATION.md - Daemon mode specifics

If you encounter persistent issues, review the logs at `/var/log/skynet-safe/skynet.log` and check the system status with `python run_daemon.py status` or `systemctl status skynet-safe.service`.
