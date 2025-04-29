# Development Examples

This directory contains example code demonstrating various features and integration patterns of RTASPI.

## Files

### basic_examples.py
Basic examples showing core RTASPI functionality:
- Streaming from USB webcam using RTSP
- Connecting to IP camera and streaming via WebRTC
- Recording audio from microphone using RTMP

### advanced_examples.py
Advanced examples demonstrating complex features:
- Motion detection pipeline with object detection
- Multi-camera setup with different configurations
- Video processing pipeline with effects
- Audio processing pipeline with filters

### integration_examples.py
Integration examples showing how to integrate RTASPI with other systems:
- REST API client implementation
- WebSocket API integration
- Web application integration example

## Usage

### Basic Examples
```python
# Run all basic examples
python basic_examples.py

# Or import and use specific examples
from basic_examples import webcam_stream_example
stream = webcam_stream_example()
```

### Advanced Examples
```python
# Run all advanced examples
python advanced_examples.py

# Or import and use specific examples
from advanced_examples import motion_detection_pipeline
pipeline = motion_detection_pipeline()
```

### Integration Examples
```python
# Run all integration examples
python integration_examples.py

# Or use the REST API client
from integration_examples import RTASPIClient
client = RTASPIClient('http://localhost:8081', 'your-token')
devices = client.list_devices()
```

## Requirements

- RTASPI library installed
- Python 3.8 or newer
- Required Python packages:
  - websockets
  - requests
  - asyncio

## Configuration

Make sure you have RTASPI properly configured before running the examples. You can use the default configuration or create your own:

```yaml
# rtaspi.config.yaml
system:
  storage_path: "~/.local/share/rtaspi"
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
```

## Best Practices

1. **Error Handling**
   - All examples include proper error handling
   - Use try/except blocks for robust error management
   - Clean up resources in finally blocks

2. **Resource Management**
   - Always clean up streams and pipelines when done
   - Use context managers where appropriate
   - Monitor system resources

3. **Security**
   - Use authentication tokens for API access
   - Secure WebSocket connections
   - Handle sensitive data properly

4. **Performance**
   - Configure appropriate video quality settings
   - Monitor CPU and memory usage
   - Use efficient streaming protocols

## Contributing

Feel free to contribute additional examples or improvements:

1. Fork the repository
2. Create your feature branch
3. Add or modify examples
4. Update documentation
5. Submit a pull request

## License

These examples are licensed under the same terms as the RTASPI project.
