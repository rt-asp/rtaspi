# Installation Guide

This guide covers the installation and initial setup of RTASPI.

## System Requirements

- Python 3.8 or newer
- FFmpeg 4.0 or newer
- GStreamer 1.14 or newer (for WebRTC support)
- NGINX with RTMP module (for RTMP support)

## Dependencies Installation

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y \
    python3 python3-pip python3-venv \
    ffmpeg \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    nginx \
    libnginx-mod-rtmp \
    v4l-utils

# Install additional development libraries
sudo apt install -y \
    build-essential \
    python3-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev
```

### macOS (using Homebrew)

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.10
brew install ffmpeg
brew install gstreamer
brew install gst-plugins-base
brew install gst-plugins-good
brew install gst-plugins-bad
brew install gst-plugins-ugly
brew install nginx
```

### Windows

1. Install Python 3.8 or newer from [python.org](https://www.python.org/downloads/)

2. Install FFmpeg:
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Add to system PATH

3. Install GStreamer:
   - Download from [gstreamer.freedesktop.org](https://gstreamer.freedesktop.org/download/)
   - Select Complete installation
   - Add to system PATH

4. Install NGINX with RTMP module:
   - Download from [nginx-rtmp-win32](https://github.com/illuspas/nginx-rtmp-win32)

## RTASPI Installation

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 2. Install RTASPI

```bash
# Install from PyPI
pip install rtaspi

# Or install from source
git clone https://github.com/rt-asp/rtaspi.git
cd rtaspi
pip install -e .
```

### 3. Configuration

1. Create configuration directory:
```bash
# Linux/macOS
mkdir -p ~/.config/rtaspi

# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path "$env:APPDATA\rtaspi"
```

2. Create basic configuration:
```yaml
# config.yaml
system:
  storage_path: "~/.local/share/rtaspi"  # Windows: %LOCALAPPDATA%\rtaspi
  log_level: "INFO"

local_devices:
  enable_video: true
  enable_audio: true
  auto_start: false

streaming:
  rtsp:
    port_start: 8554
  rtmp:
    port_start: 1935
  webrtc:
    port_start: 8080
    stun_server: "stun:stun.l.google.com:19302"
```

### 4. System Service Setup (Linux)

1. Create service file:
```bash
sudo tee /etc/systemd/system/rtaspi.service << 'EOF'
[Unit]
Description=RTASPI Service
After=network.target

[Service]
Type=simple
User=rtaspi
Environment=RTASPI_CONFIG=/etc/rtaspi/config.yaml
ExecStart=/usr/local/bin/rtaspi start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

2. Create system user and directories:
```bash
# Create system user
sudo useradd -r rtaspi

# Create configuration directories
sudo mkdir -p /etc/rtaspi /var/lib/rtaspi
sudo chown -R rtaspi:rtaspi /etc/rtaspi /var/lib/rtaspi
```

3. Enable and start service:
```bash
sudo systemctl enable rtaspi
sudo systemctl start rtaspi
```

### 5. Verify Installation

1. Check RTASPI version:
```bash
rtaspi --version
```

2. List available devices:
```bash
rtaspi devices list
```

3. Check system status:
```bash
rtaspi status
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
```bash
# Check Python version
python --version

# Check FFmpeg installation
ffmpeg -version

# Check GStreamer installation
gst-launch-1.0 --version
```

2. **Permission Issues**
```bash
# Add user to video group (Linux)
sudo usermod -a -G video $USER

# Check device permissions
ls -l /dev/video*
```

3. **Port Conflicts**
```bash
# Check if ports are in use
sudo netstat -tulpn | grep "8554\|1935\|8080"
```

### Debug Mode

Enable debug logging for troubleshooting:

```yaml
# config.yaml
system:
  log_level: "DEBUG"
  debug_mode: true
```

### Log Files

Check logs for detailed information:

```bash
# System service logs
sudo journalctl -u rtaspi

# Application logs
tail -f ~/.local/share/rtaspi/logs/rtaspi.log
```

## Next Steps

- Read the [Configuration Guide](CONFIGURATION.md) for detailed configuration options
- Check the [Examples](EXAMPLES.md) for common usage scenarios
- Explore the [API Reference](API.md) for programmatic control
- See the [CLI Guide](CLI.md) for command-line usage
