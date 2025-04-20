# SKYNET-SAFE: 24/7 Operation Guide

## Introduction

SKYNET-SAFE offers two complementary approaches for 24/7 operation:

1. **Daemon Mode**: Built-in functionality to run the system as a background process
2. **System Service**: Integration with systemd for enhanced reliability on servers

Both options achieve the same goal of running the system continuously, but they serve different use cases based on your environment and requirements.

## Daemon Mode

The built-in daemon mode uses the UNIX "double-fork" pattern to create a detached background process that:
1. Continues running after terminal closure
2. Creates a new session (setsid)
3. Redirects standard input/output 
4. Manages its own process state
5. Writes a PID file for tracking

## Launch methods

### Basic launch

```bash
# Launch the system as a daemon (uses console platform by default)
python run_daemon.py start
```

### Launch with specific communication platform

```bash
# Launch with Signal platform
python run_daemon.py start --platform signal

# Launch with Telegram platform
python run_daemon.py start --platform telegram

# Launch with console platform (for testing)
python run_daemon.py start --platform console
```

### Launch with custom paths

```bash
# Custom PID file path
python run_daemon.py start --pidfile /var/run/skynet-safe/skynet.pid

# Custom log file path
python run_daemon.py start --logfile /var/log/skynet-safe/skynet.log

# Combination of options
python run_daemon.py start --platform signal --pidfile /var/run/skynet.pid --logfile /var/log/skynet.log
```

## Daemon management

### Stopping the daemon

```bash
python run_daemon.py stop
```

### Restarting the daemon

```bash
python run_daemon.py restart
```

### Checking daemon status

```bash
python run_daemon.py status
```

## Monitoring and logs

### Log structure

The system in daemon mode generates logs in a specified file (default `/var/log/skynet-safe/skynet.log`). Logs contain:
- Timestamps
- Logging level (INFO, WARNING, ERROR)
- Module name
- Detailed event description

### JSON status file

The daemon creates a JSON status file (in the same directory as the PID file), which contains:
- Process status (running, stopped, error)
- Start/stop time
- Process identifier (PID)
- Communication platform used
- Error details (if any occurred)

Example status file:
```json
{
  "status": "running",
  "start_time": "2025-04-19T15:55:12.345678",
  "pid": 12345,
  "platform": "signal"
}
```

### Activity monitoring

To monitor daemon activity, you can:

```bash
# Live log tracking
tail -f /var/log/skynet-safe/skynet.log

# Check process status
ps aux | grep skynet

# Check resources used by the process
top -p $(cat /tmp/skynet-safe/skynet.pid)
```

## Signal handling

The daemon handles the following signals:
- SIGTERM - initiates proper system shutdown
- SIGINT - initiates proper system shutdown

When receiving a signal, the system:
1. Saves its state to the status file
2. Calls the cleanup procedure (_cleanup) in SkynetSystem
3. Closes files and resources
4. Terminates the process

## Troubleshooting

### Common problems and solutions

1. **Daemon doesn't start**
   - Check logs: `cat /var/log/skynet-safe/skynet.log`
   - Check if the directory for the PID file exists and has appropriate permissions
   - Check if the port is not occupied by another process (if using API)

2. **Daemon starts but doesn't work properly**
   - Check status file: `cat /tmp/skynet-safe/skynet_status.json`
   - Check error logs in the log file

3. **Daemon doesn't respond to stop commands**
   - Check if the process PID is correct: `cat /tmp/skynet-safe/skynet.pid`
   - Check if the process with this PID exists: `ps -p $(cat /tmp/skynet-safe/skynet.pid)`
   - As a last resort: `kill -9 $(cat /tmp/skynet-safe/skynet.pid)`

### Debugging the daemon

To run the daemon in a more diagnostic mode:

```bash
# Run with redirected standard outputs (not as a full daemon)
python run_daemon.py start --nodaemonize

# Run with higher logging level
LOGLEVEL=DEBUG python run_daemon.py start
```

## System Service Integration

For production environments, integrating with your system's service manager (e.g., systemd on most Linux distributions) provides additional reliability benefits:

- **Automatic startup** after system reboots
- **Process supervision** with automatic restarts if the process fails
- **Dependency management** (e.g., waiting for network availability)
- **Standard logging** integration with system journals

### Systemd Integration

The SKYNET-SAFE project includes a ready-to-use systemd service file in the `deployment/` directory.

To set up the system service:

1. **Copy the service file to systemd directory**:
   ```bash
   sudo cp deployment/skynet-safe.service /etc/systemd/system/
   ```

2. **Edit the service file** to match your environment:
   ```bash
   sudo nano /etc/systemd/system/skynet-safe.service
   ```
   
   Ensure the User, Group, and paths match your installation.

3. **Enable and start the service**:
   ```bash
   # Reload systemd configuration
   sudo systemctl daemon-reload
   
   # Enable automatic startup at boot
   sudo systemctl enable skynet-safe.service
   
   # Start the service
   sudo systemctl start skynet-safe.service
   
   # Verify it's running
   sudo systemctl status skynet-safe.service
   ```

### Service vs. Daemon: When to Use Each

- **Use Daemon Mode** when:
  - You don't have root/admin access to the system
  - You need a temporary 24/7 operation
  - You're in a development or testing environment

- **Use System Service** when:
  - You're on a production server
  - You need automatic startup after system reboots
  - You want integration with standard system administration tools
  - High reliability is required

## Best practices

1. **Security**
   - Run the daemon as a dedicated user with limited permissions
   - Store PID files and logs in appropriate directories (/var/run, /var/log)
   - Set restrictive access permissions to configuration files

2. **Monitoring**
   - Configure notifications for process failures
   - Regularly check logs for errors
   - Consider using monitoring tools like Prometheus/Grafana

3. **Data backup**
   - Regularly back up data from the data/ directory
   - Keep copies of configuration files