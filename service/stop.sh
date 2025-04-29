#!/bin/bash

# Stop script for stopping rtaspi service manually
# This script ensures a clean shutdown of the service

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if service is running
PID_FILE="$PROJECT_DIR/rtaspi.pid"
if [ ! -f "$PID_FILE" ]; then
    echo "Service is not running (no PID file)"
    exit 0
fi

PID=$(cat "$PID_FILE")
if ! ps -p "$PID" > /dev/null; then
    echo "Service is not running (stale PID file)"
    rm "$PID_FILE"
    exit 0
fi

# Stop service gracefully
echo "Stopping rtaspi service (PID: $PID)..."
kill -TERM "$PID"

# Wait for service to stop
TIMEOUT=30
while ps -p "$PID" > /dev/null; do
    TIMEOUT=$((TIMEOUT - 1))
    if [ "$TIMEOUT" -le 0 ]; then
        echo "Service did not stop gracefully, forcing..."
        kill -9 "$PID"
        break
    fi
    sleep 1
done

# Remove PID file
rm "$PID_FILE"

echo "Service stopped"

# Clean up any temporary files
LOG_DIR="$PROJECT_DIR/logs"
if [ -f "$LOG_DIR/rtaspi.out" ]; then
    # Archive old output file
    if [ -s "$LOG_DIR/rtaspi.out" ]; then
        mv "$LOG_DIR/rtaspi.out" "$LOG_DIR/rtaspi.out.$(date +%Y%m%d_%H%M%S)"
    else
        rm "$LOG_DIR/rtaspi.out"
    fi
fi

# Rotate log file if it's too large (>100MB)
if [ -f "$LOG_DIR/rtaspi.log" ]; then
    LOG_SIZE=$(stat -f%z "$LOG_DIR/rtaspi.log" 2>/dev/null || stat -c%s "$LOG_DIR/rtaspi.log")
    if [ "$LOG_SIZE" -gt 104857600 ]; then
        mv "$LOG_DIR/rtaspi.log" "$LOG_DIR/rtaspi.log.$(date +%Y%m%d_%H%M%S)"
        touch "$LOG_DIR/rtaspi.log"
    fi
fi
