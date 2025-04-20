# SKYNET-SAFE Configuration Testing

This document describes the configuration testing functionality included in the SKYNET-SAFE system, which allows for verification of all critical system components.

## Overview

The configuration testing system provides a way to verify that all critical components are properly configured and operational before deploying the full system. It tests:

1. **Local Language Model**: Verifies that the local model can be loaded and generates responses
2. **Telegram Communication**: Tests the Telegram bot credentials and messaging capabilities
3. **External LLM Connectivity**: Verifies that the system can connect to Claude API for evaluations
4. **System Requirements**: Checks that the hardware and software meet minimum requirements

## Usage

The configuration testing system can be used in two ways:

### Standalone Testing Script

Run the `test_config.py` script to test individual components or all components at once:

```bash
# Test all components
python test_config.py --component all

# Test specific components
python test_config.py --component model
python test_config.py --component telegram
python test_config.py --component external_llm
python test_config.py --component system

# Save results to a specific file
python test_config.py --output my_test_results.json

# Show detailed results
python test_config.py --verbose

# Suppress all output except errors
python test_config.py --quiet
```

### Programmatic API

The configuration testing functionality can also be used programmatically within your code:

```python
from src.main import SkynetSystem
from src.config import config

# Create system config
system_config = {
    "MODEL": config.MODEL_CONFIG,
    "MEMORY": config.MEMORY_CONFIG,
    # ... other configuration sections ...
}

# Initialize system
skynet = SkynetSystem(system_config)

# Test all components
results = skynet.test_configuration(component="all", save_output=True)

# Test specific component
model_results = skynet.test_configuration(component="model")
```

## Test Results

The testing system generates detailed results in both human-readable and machine-readable formats:

1. **Console Output**: A summary of test results is printed to the console
2. **Log File**: Detailed test information is written to `config_test.log`
3. **JSON Results**: Full test results are saved to a JSON file (by default `config_test_results.json`)

Example test results summary:

```
SKYNET-SAFE Configuration Test Results:

1. System Requirements: SUCCESS
   System meets all requirements
   - Python: v3.10.12 (OK)
   - RAM: 32.0 GB (OK)
   - Free Disk: 156.2 GB (OK)
   - GPU: 2 GPU(s): NVIDIA P40 (24.0 GB), NVIDIA P40 (24.0 GB) (OK)
   - Internet: Connected

2. Local Model: SUCCESS
   Model responded successfully in 1.35 seconds
   - Response time: 1.35 seconds
   - Sample response: "I'm working correctly! As an AI assistant, I'm r..."

3. Telegram: SUCCESS
   Telegram fully operational - credentials verified and test message sent
   - Bot: @skynet_safe_bot (SKYNET-SAFE)
   - Test message: Successfully sent

4. External LLM: SUCCESS
   External LLM responded successfully in 2.78 seconds
   - Response time: 2.78 seconds
   - Sample response: "This is a confirmation message from Claude. The c..."

OVERALL RESULT: ALL TESTS PASSED
```

## Configuration Requirements

For the tests to pass successfully, you need to ensure proper configuration in the `src/config/config.py` file:

### Local Model Testing

Requires valid model configuration:

```python
MODEL_CONFIG = {
    "model_id": "microsoft/phi-3-mini-4k-instruct",  # or path to local model
    "model_path": "/path/to/model/directory",
    "quantization": "4bit"  # Optional
}
```

### Telegram Testing

Requires the following in configuration:

```python
COMMUNICATION_CONFIG = {
    "platforms": ["console", "telegram"],  # Must include "telegram"
    # ...other settings...
}

PLATFORM_CONFIG = {
    "telegram": {
        "api_id": "YOUR_API_ID",
        "api_hash": "YOUR_API_HASH",
        "bot_token": "YOUR_BOT_TOKEN",
        "test_chat_id": 123456789  # Optional, for full message testing
    }
}
```

### External LLM Testing

Requires Claude API configuration:

```python
EXTERNAL_EVALUATION_CONFIG = {
    "api_key": "YOUR_CLAUDE_API_KEY",
    # ...other settings...
}
```

## Troubleshooting

If tests fail, check the following:

### Local Model Issues

- Ensure the model path is correct and the model files exist
- Check if you have enough GPU memory for the model
- Try using quantization (`"quantization": "4bit"`) for large models
- Verify CUDA is installed and functioning correctly

### Telegram Issues

- Verify API ID, API Hash, and Bot Token are correct
- Ensure the bot is active on Telegram
- Check that your Internet connection allows Telegram API access
- If only getting "credentials verified" but message test fails, verify the test_chat_id

### External LLM (Claude) Issues

- Verify your API key is valid and has not expired
- Check your internet connection
- Ensure you have proper credits/quota on your Claude account

### System Requirement Issues

- If GPU is not detected, check NVIDIA drivers and CUDA installation
- For RAM or disk space issues, consider freeing up resources
- Ensure Python version is 3.9 or higher

## Extending the Tests

The configuration testing system is designed to be extensible. To add new tests:

1. Extend the `ConfigTester` class in `src/utils/config_tester.py`
2. Add new test methods following the pattern of existing tests
3. Update the command-line interface in `test_config.py`
4. Update the `test_configuration()` method in `SkynetSystem` class