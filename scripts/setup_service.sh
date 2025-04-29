#!/bin/bash

# Setup script for installing rtaspi as a system service
# This script creates and enables a systemd service for rtaspi

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Get installation directory
INSTALL_DIR=$(python3 -c "import rtaspi; print(rtaspi.__path__[0])")
if [ $? -ne 0 ]; then
    echo "rtaspi package not found"
    exit 1
fi

# Create service user
echo "Creating service user..."
useradd -r -s /bin/false rtaspi || true

# Create config directory
echo "Creating config directory..."
mkdir -p /etc/rtaspi
chown rtaspi:rtaspi /etc/rtaspi

# Create log directory
echo "Creating log directory..."
mkdir -p /var/log/rtaspi
chown rtaspi:rtaspi /var/log/rtaspi

# Create systemd service file
echo "Creating systemd service..."
cat > /etc/systemd/system/rtaspi.service << EOL
[Unit]
Description=RT-ASP Audio/Video Stream Processing
After=network.target

[Service]
Type=simple
User=rtaspi
Group=rtaspi
ExecStart=/usr/local/bin/rtaspi server start
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1
Environment=RTASPI_CONFIG_DIR=/etc/rtaspi
Environment=RTASPI_LOG_DIR=/var/log/rtaspi

[Install]
WantedBy=multi-user.target
EOL

# Create default config files
echo "Creating default config files..."

# Main config
cat > /etc/rtaspi/config.yaml << EOL
server:
  host: localhost
  port: 8080
  workers: 4
  ssl: false

logging:
  level: INFO
  format: "%(asctime)s [%(levelname)s] %(message)s"
  file: /var/log/rtaspi/rtaspi.log
EOL

# Devices config
cat > /etc/rtaspi/devices.yaml << EOL
devices:
  # Example device configurations
  # webcam:
  #   type: USB_CAMERA
  #   enabled: true
  #   settings:
  #     resolution: 1280x720
  #     framerate: 30
EOL

# Streams config
cat > /etc/rtaspi/streams.yaml << EOL
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

# Pipelines config
cat > /etc/rtaspi/pipelines.yaml << EOL
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

# Set permissions
chown -R rtaspi:rtaspi /etc/rtaspi
chmod 644 /etc/rtaspi/*.yaml

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable and start service
echo "Enabling and starting service..."
systemctl enable rtaspi
systemctl start rtaspi

echo "Service setup complete!"
echo "Check status with: systemctl status rtaspi"
echo "View logs with: journalctl -u rtaspi"
