
# [RTASPI - Real-Time Annotation and Stream Processing Interface](http://rt-asp.github.io/rtaspi/) [<span style='font-size:20px;'>&#x270D;</span>](git@github.com:rt-asp/rtaspi/edit/main/docs/README.md)

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

 [<span style='font-size:20px;'>&#x270D;</span>](git@github.com:rt-asp/rtaspi/edit/main/docs/TREE.md)
## Struktura projektu

```
.
├── CHANGELOG.md
├── changelog.py
├── config.yaml
├── CONTRIBUTING.md
├── debug_imports.py
├── dist
│   ├── rtaspi-0.1.23-py3-none-any.whl
│   └── rtaspi-0.1.23.tar.gz
├── docs
│   ├── API.md
│   ├── CLI.md
│   ├── CONCEPTS.md
│   ├── CONFIGURATION.md
│   ├── INSTALL.md
│   ├── POST
│   │   ├── DE
│   │   ├── EN
│   │   └── PL
│   │       └── 1.md
│   ├── PROJECTS_LOCAL.md
│   ├── PROJECTS.md
│   ├── README.md
│   └── TREE.md
├── DONE.md
├── examples
├── fedora
│   └── python.sh
├── flatedit.txt
├── git.sh
├── install
│   ├── pyaudio2.py
│   ├── pyaudio2.sh
│   ├── pyaudio3.sh
│   ├── pyaudiodiag.py
│   ├── pyaudio.py
│   ├── pyaudio.sh
│   ├── pyautogui.md
│   ├── pyautogui.py
│   ├── README.md
│   ├── SPACY.md
│   ├── spacy.sh
│   └── windows.ps1
├── LICENSE
├── Makefile
├── MANIFEST.in
├── __pycache__
│   ├── __init__.cpython-311.pyc
│   ├── __init__.cpython-312.pyc
│   └── test_imports.cpython-312-pytest-8.3.5.pyc
├── pyproject.toml
├── pyproject.toml.bak
├── README.md
├── requirements.txt
├── rtaspi.config.yaml
├── rtaspi.devices.yaml
├── rtaspi.pipeline.yaml
├── rtaspi.secrets.yaml
├── rtaspi.streams.yaml
├── scripts
│   ├── configure_hardware.sh
│   ├── install_models.sh
│   ├── optimize_rpi.sh
│   ├── publish.sh
│   ├── setup_service.sh
│   └── upgrade.sh
├── service
│   ├── start.sh
│   └── stop.sh
├── setup.cfg
├── setup.py
├── src
│   ├── rtaspi
│   │   ├── api
│   │   │   ├── devices.py
│   │   │   ├── __init__.py
│   │   │   ├── pipelines.py
│   │   │   ├── server.py
│   │   │   └── streams.py
│   │   ├── cli
│   │   │   ├── commands
│   │   │   ├── completion
│   │   │   ├── __init__.py
│   │   │   └── shell.py
│   │   ├── config
│   │   │   └── __init__.py
│   │   ├── constants
│   │   │   ├── devices.py
│   │   │   ├── filters.py
│   │   │   ├── __init__.py
│   │   │   ├── outputs.py
│   │   │   └── protocols.py
│   │   ├── core
│   │   │   ├── config.py
│   │   │   ├── __init__.py
│   │   │   ├── logging.py
│   │   │   ├── mcp.py
│   │   │   ├── __pycache__
│   │   │   └── utils.py
│   │   ├── device_managers
│   │   │   ├── base.py
│   │   │   ├── __init__.py
│   │   │   ├── local_devices.py
│   │   │   ├── network_devices.py
│   │   │   ├── __pycache__
│   │   │   └── utils
│   │   ├── dsl
│   │   │   ├── executor.py
│   │   │   ├── __init__.py
│   │   │   ├── lexer.py
│   │   │   └── parser.py
│   │   ├── __init__.py
│   │   ├── __init__.py.bak
│   │   ├── __main__.py
│   │   ├── main.py
│   │   ├── processing
│   │   │   ├── audio
│   │   │   ├── __init__.py
│   │   │   ├── pipeline_executor.py
│   │   │   └── video
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-312.pyc
│   │   │   ├── __main__.cpython-312.pyc
│   │   │   ├── main.cpython-312.pyc
│   │   │   └── _version.cpython-312.pyc
│   │   ├── quick
│   │   │   ├── camera.py
│   │   │   ├── __init__.py
│   │   │   ├── microphone.py
│   │   │   └── utils.py
│   │   ├── schemas
│   │   │   ├── device.py
│   │   │   ├── __init__.py
│   │   │   ├── pipeline.py
│   │   │   └── stream.py
│   │   ├── streaming
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   ├── rtmp.py
│   │   │   ├── rtsp.py
│   │   │   ├── utils.py
│   │   │   └── webrtc.py
│   │   ├── _version.py
│   │   ├── _version.py.bak
│   │   └── web
│   │       ├── acme.py
│   │       ├── api.py
│   │       ├── __init__.py
│   │       ├── interface.py
│   │       └── server.py
│   └── rtaspi.egg-info
│       ├── dependency_links.txt
│       ├── entry_points.txt
│       ├── PKG-INFO
│       ├── requires.txt
│       ├── SOURCES.txt
│       └── top_level.txt
├── test_imports.py
├── tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── test_discovery.py
│   ├── test_local_devices.py
│   ├── test_network_devices.py
│   └── test_streaming.py
├── TODO.md
├── TODO.txt
├── update
│   ├── duplicated.py
│   ├── duplicated.sh
│   ├── pip.sh
│   ├── requirements.py
│   ├── requirements.sh
│   └── versions.py

├── version
│   ├── project.py
│   ├── README.md
│   ├── setup.py
│   └── src.py
└── version.sh

```

 [<span style='font-size:20px;'>&#x270D;</span>](git@github.com:rt-asp/rtaspi/edit/main/docs/INSTALL.md)
## Uruchomienie

1. Uruchom główny skrypt:
```bash
python main.py
```

2. Opcjonalnie, możesz podać ścieżkę do pliku konfiguracyjnego:
```bash
python main.py -c /sciezka/do/config.yaml
```

## Protokół komunikacyjny MCP

System używa wewnętrznego protokołu komunikacyjnego MCP (Module Communication Protocol) do wymiany informacji między modułami. Protokół opiera się na wzorcu publikuj/subskrybuj (pub/sub), gdzie moduły mogą publikować wiadomości na określone tematy i subskrybować tematy, aby otrzymywać wiadomości.

### Przykładowe tematy MCP:

- `local_devices/devices` - Informacje o wykrytych lokalnych urządzeniach
- `local_devices/stream/started` - Informacja o uruchomieniu strumienia z lokalnego urządzenia
- `network_devices/devices` - Informacje o wykrytych urządzeniach sieciowych
- `command/local_devices/scan` - Komenda do skanowania lokalnych urządzeń
- `command/network_devices/add_device` - Komenda do dodania zdalnego urządzenia

## Używanie API

System udostępnia API do zarządzania urządzeniami i strumieniami. Poniżej znajdują się przykłady użycia API w kodzie Python:

```python
from core.mcp import MCPBroker, MCPClient

# Utwórz klienta MCP
broker = MCPBroker()
client = MCPClient(broker, client_id="my_client")

# Subskrybuj tematy
client.subscribe("local_devices/devices", handler=handle_devices)
client.subscribe("local_devices/stream/started", handler=handle_stream_started)

# Wysyłaj komendy
client.publish("command/local_devices/scan", {})

# Uruchom strumień z urządzenia
client.publish("command/local_devices/start_stream", {
    "device_id": "video:/dev/video0",
    "protocol": "rtsp"
})

# Dodaj zdalne urządzenie
client.publish("command/network_devices/add_device", {
    "name": "Kamera IP",
    "ip": "192.168.1.100",
    "port": 554,
    "username": "admin",
    "password": "admin",
    "type": "video",
    "protocol": "rtsp",
    "paths": ["cam/realmonitor"]
})
```

## Testy

Uruchomienie testów jednostkowych:
```bash
pytest -v tests/
```

## Licencja

Ten projekt jest udostępniany na licencji Apache 2. Zobacz plik LICENSE, aby uzyskać więcej informacji.

## Autorzy

- Zespół rtaspi

## Współpraca

Zachęcamy do współpracy przy rozwoju projektu. Zapraszamy do zgłaszania problemów (issues) i propozycji zmian (pull requests).

---
+ Modular Documentation made possible by the [FlatEdit](http://www.flatedit.com) project.
