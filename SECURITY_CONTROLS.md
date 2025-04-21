# SKYNET-SAFE System Security Controls

## Security and Ethics Components

SKYNET-SAFE includes several components responsible for security and ethics, which can be temporarily disabled during debugging or testing:

1. **SecuritySystemManager** - the main security system responsible for access control, rate limiting, content filtering, and sanitization.
2. **EthicalFrameworkManager** - component responsible for applying ethical frameworks to generated responses.
3. **DevelopmentMonitorManager** - monitors system behavior for anomalies and developmental patterns.
4. **ExternalValidationManager** - uses external models to validate system responses.

## Components Enable/Disable Mechanism

Security and ethics components can be enabled or disabled by setting appropriate flags in the configuration file `src/config/config.py`:

```python
# System Settings - Global Control Panel
SYSTEM_SETTINGS = {
    "enable_security_system": True,    # SecuritySystemManager toggle flag
    "enable_ethical_framework": True,  # EthicalFrameworkManager toggle flag
    "enable_development_monitor": True,  # DevelopmentMonitorManager toggle flag
    "enable_external_validation": True   # ExternalValidationManager toggle flag
}
```

To disable one or more components, set the appropriate flag to `False`.

## Security Notes

- Disabling these components should **only** occur during debugging and testing.
- Never disable security components in a production environment.
- Even with these components disabled, CorrectionMechanismManager remains active as a basic safety layer.
- The system logs warnings about disabled security components.

## Usage Guidelines

1. When debugging content filtering issues, you can disable `SecuritySystemManager`
2. When testing interactions that might be incorrectly flagged as unethical, you can disable `EthicalFrameworkManager`
3. When optimizing system performance, you can disable `DevelopmentMonitorManager` and `ExternalValidationManager`, which perform background operations

## How to Run the System with Disabled Security Components

1. Edit the `src/config/config.py` file and set appropriate flags to `False`
2. Run the system normally:
   ```
   python run_interactive.py
   ```
   or
   ```
   python run_daemon.py
   ```
3. In interactive mode, you'll see a warning about disabled security components

## Logging System

SKYNET-SAFE includes a comprehensive logging system to track all activities, including:

### System Logs
- Main system logs: `/opt/skynet-safe/skynet.log` and `/opt/skynet-safe/logs/skynet.log`
- Test mode logs: `/opt/skynet-safe/skynet_test.log`
- Interactive mode logs: `/opt/skynet-safe/skynet_interactive.log`
- Configuration test logs: `/opt/skynet-safe/config_test.log`

### LLM Interaction Logs
A dedicated logging facility records all interactions with the language model:
- Log file location: `/opt/skynet-safe/logs/llm_interactions.log`
- Each log entry is in JSON format for easy parsing
- Log information includes:
  - Timestamp of the interaction
  - User query
  - Length of context provided
  - Model response
  - Processing time in seconds
  - Model name

Example log entry:
```json
{
  "timestamp": "2025-04-20T19:30:45.123456",
  "query": "What is the meaning of life?",
  "context_length": 3,
  "response": "The meaning of life is a philosophical question...",
  "duration_seconds": 2.35,
  "model": "failspy_Llama-3-8B-Instruct-abliterated"
}
```

Error scenarios are also logged with information about what went wrong:
```json
{
  "timestamp": "2025-04-20T19:35:12.654321",
  "query": "Tell me about the future",
  "context_length": 2,
  "error": "CUDA out of memory",
  "model": "failspy_Llama-3-8B-Instruct-abliterated"
}
```