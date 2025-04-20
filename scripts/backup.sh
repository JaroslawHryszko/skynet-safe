#!/bin/bash
# SKYNET-SAFE Backup Script
#
# This script creates regular backups of SKYNET-SAFE data and maintains
# a rolling history of backups.

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/skynet-safe/backups"
mkdir -p $BACKUP_DIR

# Stop service briefly for clean backup
systemctl stop skynet-safe.service

# Backup data
tar -czf $BACKUP_DIR/skynet_data_$TIMESTAMP.tar.gz /opt/skynet-safe/data

# Restart service
systemctl start skynet-safe.service

# Clean old backups (keep last 7)
ls -t $BACKUP_DIR/skynet_data_*.tar.gz | tail -n +8 | xargs -r rm