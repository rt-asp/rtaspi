# [RTASPI - Real-Time Annotation and Stream Processing Interface](http://rt-asp.github.io/rtaspi/)

RTASPI is a powerful system for detecting, managing, and streaming from local and remote audio/video devices. It enables easy sharing of camera and microphone streams through various protocols (RTSP, RTMP, WebRTC) while providing real-time processing capabilities.

## Features

- **Device Management**
  - Automatic detection of local video (cameras) and audio (microphones) devices
  - Network device discovery (IP cameras, IP microphones) via ONVIF, UPnP, and mDNS
  - Unified device management interface

- **Streaming Capabilities**
  - Stream local devices via RTSP, RTMP, and WebRTC
  - Proxy streams from remote devices
  - Real-time stream transcoding
  - Multi-protocol support

- **Processing Features**
  - Real-time video filtering and effects
  - Audio processing and filters
  - Speech recognition capabilities
  - Object detection and tracking

- **Integration & Control**
  - RESTful API for remote control
  - Command-line interface (CLI)
  - Web interface for management
  - Module Communication Protocol (MCP) for inter-module communication

## Documentation

- [Installation Guide](INSTALL.md) - Detailed installation instructions
- [Core Concepts](CONCEPTS.md) - Understanding RTASPI's architecture and key concepts
- [Configuration Guide](CONFIGURATION.md) - How to configure RTASPI
- [API Reference](API.md) - REST API documentation
- [CLI Guide](CLI.md) - Command-line interface usage
- [Development Guide](DEVELOPMENT.md) - Contributing to RTASPI
- [Examples](EXAMPLES.md) - Usage examples and tutorials

## System Requirements

- Python 3.8 or newer
- FFmpeg 4.0 or newer
- GStreamer 1.14 or newer (for WebRTC)
- NGINX with RTMP module (for RTMP)

### System Dependencies

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install ffmpeg gstreamer1.0-tools gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly nginx libnginx-mod-rtmp v4l-utils
```

#### macOS:
```bash
brew install ffmpeg gstreamer gst-plugins-base gst-plugins-good \
    gst-plugins-bad gst-plugins-ugly nginx
```

#### Windows:
Download and install:
- [FFmpeg](https://ffmpeg.org/download.html)
- [GStreamer](https://gstreamer.freedesktop.org/download/)
- [NGINX with RTMP module](https://github.com/illuspas/nginx-rtmp-win32)

## Quick Start

1. Install RTASPI:
```bash
pip install rtaspi
```

2. Create a configuration file (rtaspi.config.yaml):
```yaml
system:
  storage_path: 'storage'
  log_level: 'INFO'

local_devices:
  enable_video: true
  enable_audio: true
  auto_start: false
```

3. Start RTASPI:
```bash
rtaspi start
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](../LICENSE) file for details.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.
