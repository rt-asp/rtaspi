# Project Structure

This document provides an overview of RTASPI's directory structure and organization.

## Root Directory

```
rtaspi/
├── docs/               # Documentation
├── examples/           # Example configurations and scripts
├── install/            # Installation scripts and guides
├── scripts/           # Maintenance and setup scripts
├── service/           # System service scripts
├── src/               # Source code
├── tests/             # Test suite
└── update/            # Update and maintenance tools
```

## Source Code Structure

```
src/rtaspi/
├── api/               # REST API implementation
│   ├── devices.py     # Device management endpoints
│   ├── pipelines.py   # Pipeline management endpoints
│   ├── server.py      # API server implementation
│   └── streams.py     # Stream management endpoints
│
├── cli/               # Command-line interface
│   ├── commands/      # CLI command implementations
│   ├── completion/    # Shell completion scripts
│   └── shell.py       # CLI shell implementation
│
├── core/              # Core functionality
│   ├── config.py      # Configuration management
│   ├── logging.py     # Logging system
│   ├── mcp.py         # Module Communication Protocol
│   └── utils.py       # Utility functions
│
├── device_managers/   # Device management
│   ├── base.py        # Base device manager class
│   ├── local_devices.py    # Local device management
│   ├── network_devices.py  # Network device management
│   └── utils/        # Device management utilities
│
├── dsl/               # Domain Specific Language
│   ├── executor.py    # DSL execution engine
│   ├── lexer.py       # DSL lexical analyzer
│   └── parser.py      # DSL parser
│
├── processing/        # Stream processing
│   ├── audio/        # Audio processing
│   │   ├── filters.py   # Audio filters
│   │   └── speech.py    # Speech recognition
│   ├── video/        # Video processing
│   │   ├── detection.py # Object detection
│   │   └── filters.py   # Video filters
│   └── pipeline_executor.py  # Processing pipeline
│
├── quick/            # Quick access utilities
│   ├── camera.py     # Camera utilities
│   ├── microphone.py # Microphone utilities
│   └── utils.py      # Quick access helpers
│
├── schemas/          # Data models and validation
│   ├── device.py     # Device schemas
│   ├── pipeline.py   # Pipeline schemas
│   └── stream.py     # Stream schemas
│
├── streaming/        # Streaming protocols
│   ├── rtmp.py       # RTMP implementation
│   ├── rtsp.py       # RTSP implementation
│   ├── webrtc.py     # WebRTC implementation
│   └── utils.py      # Streaming utilities
│
└── web/             # Web interface
    ├── acme.py       # ACME protocol support
    ├── api.py        # Web API implementation
    ├── interface.py  # Web interface
    └── server.py     # Web server
```

## Documentation Structure

```
docs/
├── API.md            # REST API reference
├── CLI.md            # Command-line interface guide
├── CONCEPTS.md       # Architecture and core concepts
├── CONFIGURATION.md  # Configuration guide
├── DEVELOPMENT.md    # Development guide
├── EXAMPLES.md       # Usage examples and tutorials
├── INSTALL.md        # Installation guide
├── README.md         # Project overview
└── TREE.md          # This file
```

## Scripts and Tools

```
scripts/
├── configure_hardware.sh  # Hardware configuration
├── install_models.sh      # ML model installation
├── optimize_rpi.sh        # Raspberry Pi optimization
├── publish.sh            # Package publishing
├── setup_service.sh      # Service setup
└── upgrade.sh            # System upgrade

service/
├── start.sh             # Service start script
└── stop.sh              # Service stop script

update/
├── requirements.py      # Dependencies update
└── versions.py         # Version management
```

## Configuration Files

```
rtaspi/
├── rtaspi.config.yaml    # Main configuration
├── rtaspi.devices.yaml   # Device configuration
├── rtaspi.pipeline.yaml  # Pipeline configuration
├── rtaspi.secrets.yaml   # Sensitive information
└── rtaspi.streams.yaml   # Stream configuration
```

## Development Files

```
rtaspi/
├── pyproject.toml       # Project metadata
├── setup.cfg           # Package configuration
├── setup.py            # Package setup
├── requirements.txt    # Dependencies
├── MANIFEST.in         # Package manifest
└── Makefile           # Build automation
```

## Key Directories

- **src/rtaspi/**: Main source code
  - Core functionality and implementations
  - Modular architecture with clear separation of concerns
  - Each module focuses on specific functionality

- **docs/**: Documentation
  - Comprehensive guides and references
  - Examples and tutorials
  - Architecture documentation

- **tests/**: Test suite
  - Unit tests
  - Integration tests
  - Test fixtures and utilities

- **scripts/**: Utility scripts
  - Installation and setup
  - System optimization
  - Maintenance tools

- **service/**: System service
  - Service management scripts
  - System integration

## File Organization

The project follows a modular structure where:

1. Each major feature has its own directory
2. Related functionality is grouped together
3. Common utilities are centralized
4. Configuration is separated from code
5. Documentation is comprehensive and organized

This structure enables:

- Easy navigation
- Clear separation of concerns
- Modular development
- Simple maintenance
- Straightforward testing




```
.
├── CHANGELOG.md
├── changelog.py
├── config.yaml
├── CONTRIBUTING.md
├── debug_imports.py
├── dist
├── docs
│   ├── API.md
│   ├── CLI.md
│   ├── CONCEPTS.md
│   ├── CONFIGURATION.md
│   ├── DEVELOPMENT.md
│   ├── EXAMPLES.md
│   ├── INSTALL.md
│   ├── POST
│   │   ├── DE
│   │   ├── EN
│   │   └── PL
│   ├── PROJECTS_LOCAL.md
│   ├── PROJECTS.md
│   ├── README.md
│   ├── SPEECH_AND_INPUT.md
│   ├── TEST.md
│   └── TREE.md
├── DONE.md
├── examples
│   ├── automation
│   │   └── rules.json
│   ├── commands
│   │   └── keyboard_commands.json
│   ├── config
│   │   ├── project.config.yaml
│   │   ├── README.md
│   │   ├── rtaspi.config.yaml
│   │   └── user.config.yaml
│   ├── industrial
│   │   ├── modbus_config.yaml
│   │   └── opcua_config.yaml
│   └── security
│       ├── alarms_config.yaml
│       └── behavior_config.yaml
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
├── pyproject.toml
├── pyproject.toml.bak
├── README.md
├── requirements-dev.txt
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
│   │   ├── automation
│   │   ├── cli
│   │   ├── config
│   │   ├── constants
│   │   ├── core
│   │   ├── device_managers
│   │   ├── dsl
│   │   ├── __init__.py
│   │   ├── input
│   │   ├── __main__.py
│   │   ├── main.py
│   │   ├── processing
│   │   ├── __pycache__
│   │   ├── quick
│   │   ├── schemas
│   │   ├── security
│   │   ├── streaming
│   │   ├── _version.py
│   │   ├── _version.py.bak
│   │   └── web
│   └── rtaspi.egg-info
│       ├── dependency_links.txt
│       ├── entry_points.txt
│       ├── PKG-INFO
│       ├── requires.txt
│       ├── SOURCES.txt
│       └── top_level.txt
├── storage
├── test_imports.py
├── tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── test_audio_filters.py
│   ├── test_command_processor.py
│   ├── test_discovery.py
│   ├── test_dsc.py
│   ├── test_hass.py
│   ├── test_honeywell.py
│   ├── test_intercom.py
│   ├── test_keyboard.py
│   ├── test_local_devices.py
│   ├── test_modbus.py
│   ├── test_motion.py
│   ├── test_mqtt.py
│   ├── test_network_devices.py
│   ├── test_opcua.py
│   ├── test_remote_desktop_manager.py
│   ├── test_remote_desktop.py
│   ├── test_sip.py
│   ├── test_speech_recognition.py
│   ├── test_streaming.py
│   ├── test_video_filters.py
│   ├── test_vnc.py
│   └── test_window_capture.py
├── TODO2.md
├── TODO.md
├── TODO.txt
├── tox.ini
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