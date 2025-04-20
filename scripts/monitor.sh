#!/bin/bash
# SKYNET-SAFE Monitoring Script
#
# This script checks the health of the SKYNET-SAFE system and sends
# email alerts if issues are detected.

LOG_FILE="/var/log/skynet-safe/skynet.log"
STATUS_FILE="/var/run/skynet-safe/skynet_status.json"
EMAIL="admin@example.com"  # Replace with your email

check_status() {
    if [ ! -f "$STATUS_FILE" ]; then
        echo "Status file not found" | mail -s "SKYNET-SAFE: Status file missing" $EMAIL
        return 1
    fi
    
    STATUS=$(grep -o '"status": "[^"]*"' "$STATUS_FILE" | cut -d'"' -f4)
    if [ "$STATUS" != "running" ]; then
        echo "System is not running (status: $STATUS)" | mail -s "SKYNET-SAFE: System not running" $EMAIL
        return 1
    fi
    
    return 0
}

check_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "Log file not found" | mail -s "SKYNET-SAFE: Log file missing" $EMAIL
        return 1
    fi
    
    # Check for errors in the last 1 hour
    ERROR_COUNT=$(grep -c "ERROR" <(tail -n 1000 "$LOG_FILE") || true)
    if [ $ERROR_COUNT -gt 5 ]; then
        echo "High number of errors detected ($ERROR_COUNT)" | mail -s "SKYNET-SAFE: Errors detected" $EMAIL
        return 1
    fi
    
    return 0
}

check_system() {
    # Check memory usage
    MEM_USAGE=$(free | grep Mem | awk '{print $3/$2 * 100.0}')
    if (( $(echo "$MEM_USAGE > 90" | bc -l) )); then
        echo "High memory usage: ${MEM_USAGE}%" | mail -s "SKYNET-SAFE: High memory usage" $EMAIL
    fi
    
    # Check disk usage
    DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $DISK_USAGE -gt 90 ]; then
        echo "High disk usage: ${DISK_USAGE}%" | mail -s "SKYNET-SAFE: High disk usage" $EMAIL
    fi
    
    # Check GPU usage
    if command -v nvidia-smi &> /dev/null; then
        GPU_USAGE=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | awk '{sum+=$1} END {print sum/NR}')
        if (( $(echo "$GPU_USAGE < 5" | bc -l) )); then
            echo "Low GPU usage: ${GPU_USAGE}%" | mail -s "SKYNET-SAFE: Low GPU utilization" $EMAIL
        fi
    fi
}

# Main monitoring logic
check_status
check_logs
check_system

# Try to restart if not running properly
if ! systemctl is-active --quiet skynet-safe.service; then
    echo "Service not active, attempting restart" | mail -s "SKYNET-SAFE: Service restart attempt" $EMAIL
    systemctl restart skynet-safe.service
fi