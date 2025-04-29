#!/bin/bash

# Start script for running rtaspi service manually
# This script is useful for development and debugging

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Create log directory if needed
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# Create config directory if needed
CONFIG_DIR="$PROJECT_DIR/config"
mkdir -p "$CONFIG_DIR"

# Create default config files if they don't exist
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    cat > "$CONFIG_DIR/config.yaml" << EOL
server:
  host: localhost
  port: 8080
  workers: 4
  ssl: false

logging:
  level: DEBUG  # More verbose for development
  format: "%(asctime)s [%(levelname)s] %(message)s"
  file: logs/rtaspi.log
EOL
fi

if [ ! -f "$CONFIG_DIR/devices.yaml" ]; then
    cat > "$CONFIG_DIR/devices.yaml" << EOL
devices:
  # Example device configurations
  # webcam:
  #   type: USB_CAMERA
  #   enabled: true
  #   settings:
  #     resolution: 1280x720
  #     framerate: 30
EOL
fi

if [ ! -f "$CONFIG_DIR/streams.yaml" ]; then
    cat > "$CONFIG_DIR/streams.yaml" << EOL
streams:
  # Example stream configurations
  # webcam_stream:
  #   device: webcam
  #   type: video
  #   enabled: true
  #   outputs:
  #     - type: RTSP
  #       url: rtsp://localhost:8554/webcam
EOL
fi

if [ ! -f "$CONFIG_DIR/pipelines.yaml" ]; then
    cat > "$CONFIG_DIR/pipelines.yaml" << EOL
pipelines:
  # Example pipeline configurations
  # face_detection:
  #   enabled: true
  #   stages:
  #     - name: source
  #       type: VIDEO_SOURCE
  #       device: webcam
  #     - name: detect
  #       type: FACE_DETECTION
  #       inputs: [source]
EOL
fi

# Check if service is already running
PID_FILE="$PROJECT_DIR/rtaspi.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null; then
        echo "Service is already running (PID: $PID)"
        exit 1
    else
        rm "$PID_FILE"
    fi
fi

# Set environment variables
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
export RTASPI_CONFIG_DIR="$CONFIG_DIR"
export RTASPI_LOG_DIR="$LOG_DIR"
export PYTHONUNBUFFERED=1

# Start service
echo "Starting rtaspi service..."
if [ "$1" == "--debug" ]; then
    # Run in foreground for debugging
    python3 -m rtaspi server start --verbose
else
    # Run in background
    nohup python3 -m rtaspi server start > "$LOG_DIR/rtaspi.out" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Service started (PID: $!)"
    echo "Logs available in: $LOG_DIR/rtaspi.log"
    echo "Output available in: $LOG_DIR/rtaspi.out"
fi
