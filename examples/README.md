# RTASPI Examples

This directory contains example code demonstrating various features of RTASPI.

## Directory Structure

### Basic Examples (`basic/`)
- `camera_stream.py` - Basic camera streaming with filters and RTSP output
- `microphone_recording.py` - Audio recording with processing capabilities
- `device_discovery.py` - Device scanning and management

### Device Management (`devices/`)
- Network device integration
- Industrial protocol support (Modbus, OPC UA)
- Remote desktop and VNC examples
- Security system integration

### Embedded Systems (`embedded/`)
- Raspberry Pi optimization
- Jetson Nano configuration
- Hardware-specific examples

### Pipeline Processing (`pipelines/`)
- Video processing pipelines
- Audio filtering chains
- Motion detection
- Object tracking

### Speech Processing (`speech/`)
- Speech recognition
- Text-to-speech
- Real-time translation
- Voice commands

### Web Interface (`webserver/`)
- HTTPS server setup
- Matrix view implementation
- REST API examples
- WebRTC streaming

### Industrial Integration (`industrial/`)
- Modbus device control
- OPC UA communication
- Industrial protocol examples

### Security Features (`security/`)
- Motion detection
- Alarm system integration
- Behavior analysis
- Access control

## Running the Examples

1. Install RTASPI and dependencies:
```bash
pip install rtaspi
pip install -r requirements.txt
```

2. Navigate to example directory:
```bash
cd examples/basic  # or any other category
```

3. Run an example:
```bash
python camera_stream.py --help
python microphone_recording.py --help
python device_discovery.py --help
```

## Example Categories

### Basic Usage
Simple examples demonstrating core functionality:
- Device discovery and management
- Stream capture and processing
- Basic filtering and effects

### Advanced Features
Complex examples showing advanced capabilities:
- Multi-device synchronization
- Custom processing pipelines
- Network integration
- Security features

### Integration Examples
Examples of integrating with other systems:
- Industrial protocols
- Security systems
- Home automation
- Cloud services

## Configuration

Each example can be configured through:
- Command line arguments
- Configuration files
- Environment variables

See individual example directories for specific configuration options.

## Requirements

### Basic Examples
- Python 3.8+
- OpenCV
- PyAudio
- Basic RTASPI dependencies

### Advanced Examples
- Additional libraries (see requirements.txt)
- Specific hardware (where applicable)
- Network connectivity (for remote features)

## Contributing

To contribute new examples:

1. Create a new directory for your example category
2. Include a README.md with:
   - Purpose and features
   - Requirements
   - Usage instructions
   - Configuration options
3. Add Python scripts with comprehensive comments
4. Update this main README.md

## Support

For help with examples:
- Check the [documentation](../docs)
- Join our [Discord community](https://discord.gg/rtaspi)
- Open an [issue](https://github.com/rtaspi/rtaspi/issues)

## License

All examples are licensed under the same terms as the RTASPI project.
See [LICENSE](../LICENSE) for details.
