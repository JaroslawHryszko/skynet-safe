# SKYNET-SAFE: System Usage Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [System Startup](#system-startup)
4. [Configuration](#configuration)
5. [Monitoring](#monitoring)
6. [Diagnostics and Troubleshooting](#diagnostics-and-troubleshooting)
7. [Fine-tuning Management](#fine-tuning-management)
8. [Security Management](#security-management)

## System Requirements

### Hardware
- Server with min. 32GB RAM
- Two NVIDIA P40 cards (or equivalent)
- Min. 500GB disk space
- Stable internet connection

### Software
- Ubuntu 20.04 LTS or newer
- Python 3.9+
- CUDA 11.4+
- Docker (optional)
- Packages listed in `requirements.txt`

## Installation

### Environment Setup

```bash
# Clone repository
git clone https://github.com/your-org/skynet-safe.git
cd skynet-safe

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Prepare data directories
mkdir -p data/memory data/security data/logs data/checkpoints
mkdir -p data/ethics data/monitoring
```

### Downloading Models

```bash
# Download base model
python src/scripts/download_model.py

# Download embeddings model
python src/scripts/download_embeddings.py
```

## System Startup

### Standard Startup

```bash
# Activate environment
source venv/bin/activate

# Run system in standard mode
python src/main.py

# Run system with specific configuration
python src/main.py --config configs/custom_config.py
```

### Debug Mode Startup

```bash
# Run with extended logging
python src/main.py --debug

# Run without internet access (for testing only)
python src/main.py --no-internet
```

### Running as a System Service

```bash
# Install service
sudo cp deployment/skynet-safe.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable skynet-safe.service

# Start service
sudo systemctl start skynet-safe.service

# Check status
sudo systemctl status skynet-safe.service
```

### Running in Daemon Mode

The SKYNET-SAFE system can run as a daemon (background process) without configuring a system service:

```bash
# Run system in background (uses console platform by default)
python run_daemon.py start

# Run with specific communication platform
python run_daemon.py start --platform signal
python run_daemon.py start --platform telegram

# Stop daemon
python run_daemon.py stop

# Restart daemon
python run_daemon.py restart

# Check daemon status
python run_daemon.py status

# Custom PID file path
python run_daemon.py start --pidfile /path/to/skynet.pid

# Custom log file path
python run_daemon.py start --logfile /path/to/skynet.log
```

Daemon statuses are also stored in a JSON file (in the directory containing the PID file) and can be used by monitoring tools.

## Configuration

The SKYNET-SAFE system is configured using the `src/config/config.py` file. The most important configuration sections:

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

### Communication Configuration

```python
COMMUNICATION = {
    "platform": "signal",  # communication platform (signal, telegram, api)
    "check_interval": 5,  # frequency of checking for new messages (seconds)
    "response_delay": 1.5,  # response delay (seconds)
    "api_key": "",  # API key (if required)
    "signal_number": "+1234567890",  # phone number for Signal
    "signal_config_path": "./signal-cli-config/"  # configuration path for Signal
}
```

### Security Configuration

```python
SECURITY_SYSTEM = {
    "allowed_domains": ["wikipedia.org", "github.com", "python.org"],  # allowed domains
    "input_length_limit": 1000,  # maximum query length
    "max_api_calls_per_hour": 100,  # API calls limit
    "security_logging_level": "INFO",  # security logging level
    "max_consecutive_requests": 20,  # consecutive requests limit
    "suspicious_patterns": [  # patterns to block
        "eval\\(.*\\)",
        "exec\\(.*\\)",
        "import os.*system",
        "rm -rf"
    ],
    "security_lockout_time": 30 * 60,  # lockout time (seconds)
    "security_alert_threshold": 3  # alerts threshold before lockout
}
```

### Ethics Configuration

```python
ETHICAL_FRAMEWORK = {
    "ethical_principles": {
        "beneficence": "Act for the benefit of users",
        "non_maleficence": "Avoid harmful actions",
        # other principles...
    },
    "ethical_rules": [
        "Do not promote illegal activities",
        "Do not encourage violence",
        # other rules...
    ],
    "value_judgment_thresholds": {
        "critical_violation": 0.2,  # threshold for critical violation
        "ethical_pass": 0.8  # threshold for ethical acceptability
    }
}
```

## Monitoring

### System Logs

The system stores logs in the `data/logs/` directory. Main log files:

- `skynet.log` - main system log
- `security.log` - security events log
- `corrections.json` - ethical corrections history
- `monitoring_log.json` - monitoring metrics history

### Monitoring Tools

```bash
# Live log view
tail -f data/logs/skynet.log

# Security incidents analysis
python src/scripts/analyze_security_incidents.py

# Development metrics visualization
python src/scripts/plot_development_metrics.py
```

### Web Interface (optional)

If the web interface module is installed:

```bash
# Start web interface
python src/webui/server.py

# Interface available at:
# http://localhost:8080
```

## Diagnostics and Troubleshooting

### Common Problems and Solutions

#### System Doesn't Start

**Problem**: `CUDA out of memory` error during initialization.

**Solution**: 
- Reduce the `quantization` parameter to `4bit` or `8bit` in the model configuration
- Check if other processes are using GPU memory (`nvidia-smi`)
- Restart the server if GPU memory is fragmented

```bash
# Check GPU usage
nvidia-smi

# Restart GPU server (requires root privileges)
sudo systemctl restart nvidia-persistenced
```

#### Internet Connection Problems

**Problem**: `ConnectionError` during internet exploration.

**Solution**:
- Check internet connection
- Verify proxy settings if used
- Adjust the `timeout` parameter in the `INTERNET` configuration
- Check if API limits for external services have been exceeded

```bash
# Connection test
ping www.google.com

# Run with alternative connection configuration
python src/main.py --config configs/alt_connection_config.py
```

#### Memory Problems

**Problem**: System uses too much RAM and runs slowly.

**Solution**:
- Adjust the `record_history_length` parameter in the `DEVELOPMENT_MONITOR` configuration
- Limit the `MemoryManager` size by setting `max_memory_size`
- Run memory cleanup periodically

```bash
# Run with limited memory
python src/main.py --memory-limit 16G

# Manual cleaning of unused data
python src/scripts/cleanup_memories.py --older-than 30d
```

### Diagnostic Tools

```bash
# Full system diagnostics
python src/scripts/diagnose_system.py

# Individual module test
python src/scripts/test_module.py --module memory

# Model verification
python src/scripts/verify_model.py
```

## Fine-tuning Management

### Manual Fine-tuning Initiation

```bash
# Run LoRA fine-tuning process
python src/scripts/run_finetuning.py --lora-rank 16 --epochs 3

# Apply trained adapter
python src/scripts/apply_adapter.py --adapter ./models/adapters/latest
```

### Fine-tuning Process Scheduling

```bash
# Set training schedule
python src/scripts/schedule_training.py --interval daily --time 03:00

# Check scheduled tasks status
python src/scripts/check_training_schedule.py
```

### Checkpoint Management

```bash
# Create checkpoint
python src/scripts/create_checkpoint.py --name "before-experiment-1"

# Restore checkpoint
python src/scripts/restore_checkpoint.py --name "before-experiment-1"

# List available checkpoints
python src/scripts/list_checkpoints.py
```

## Security Management

### Viewing Security Incidents

```bash
# Display recent incidents
python src/scripts/show_security_incidents.py --last 10

# Generate security report
python src/scripts/generate_security_report.py --output security_report.pdf
```

### Block Configuration

```bash
# Add pattern to block
python src/scripts/add_security_pattern.py --pattern "dangerous_function\\(.*\\)"

# Unlock user
python src/scripts/unlock_user.py --user-id "user123"
```

### External Validation

```bash
# Manual validation run
python src/scripts/run_validation.py --scenarios all

# Review validation history
python src/scripts/review_validation_history.py
```

### Incident Response

In case of a serious security incident:

1. Stop the system: `sudo systemctl stop skynet-safe.service`
2. Perform diagnostics: `python src/scripts/diagnose_system.py --full`
3. Review logs: `less data/logs/security.log`
4. Restore the last stable checkpoint: `python src/scripts/restore_checkpoint.py --last-stable`
5. Update security configuration
6. Restart the system: `sudo systemctl start skynet-safe.service`