# RTASPI - Real-Time Annotation and Stream Processing Interface

## Project Structure

The RTASPI project is organized into modular components:

```
rtaspi-modular/
├── pyproject.toml         # Main project configuration
├── setup.py              # Installation configuration
├── rtaspi-core/          # Core system functionality
├── rtaspi-devices/       # Device management
├── rtaspi-streaming/     # Streaming capabilities
├── rtaspi-processing/    # Media processing
├── rtaspi-web/          # Web interface
├── rtaspi-cli/          # Command-line interface
└── rtaspi-integration/   # External integrations
```

## Modules

### rtaspi-core
Core system functionality including:
- Configuration management
- Logging system
- Message broker
- Utility functions
- Core abstractions and interfaces

### rtaspi-devices
Device management capabilities:
- Local device discovery and control
- Network device management
- Protocol implementations
- Device state management
- Scanner implementations

### rtaspi-streaming
Streaming functionality:
- RTSP protocol support
- RTMP streaming
- WebRTC implementation
- Stream management
- Output handlers

### rtaspi-processing
Media processing features:
- Video filters and effects
- Audio processing
- Object detection
- Speech recognition
- Pipeline execution

### rtaspi-web
Web interface components:
- REST API endpoints
- WebSocket handlers
- Web UI
- Server implementation
- HTTPS support

### rtaspi-cli
Command-line interface:
- Device management commands
- Stream control
- Pipeline management
- Configuration tools
- Shell completion

### rtaspi-integration
External system integration:
- Automation rules engine
- Event triggers
- Action handlers
- MQTT support
- Home Assistant integration

## Development

### Setup
1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
3. Initialize submodules:
   ```bash
   git submodule update --init --recursive
   ```

### Module Development
Each module follows these conventions:
- Clear separation of concerns
- Well-defined interfaces
- Comprehensive testing
- Documentation
- Type hints

### Testing
Run tests for all modules:
```bash
pytest
```

Run tests for specific module:
```bash
pytest tests/test_<module_name>
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License
MIT License - see LICENSE file for details
