# Basic Examples

This directory contains basic examples demonstrating core RTASPI functionality.

## Examples

### 1. Camera Stream (`camera_stream.py`)
Simple example showing how to:
- Start a camera stream
- Apply basic video filters
- Stream to RTSP server
- Save to file

### 2. Microphone Recording (`microphone_recording.py`)
Basic example demonstrating:
- Microphone capture
- Audio filtering
- Recording to file
- Real-time audio processing

### 3. Device Discovery (`device_discovery.py`)
Shows how to:
- Scan for available devices
- Filter devices by type
- Get device capabilities
- Configure devices

## Running the Examples

1. Install RTASPI:
```bash
pip install rtaspi
```

2. Run an example:
```bash
python camera_stream.py
# or
python microphone_recording.py
# or
python device_discovery.py
```

## Configuration

Each example can be configured through:
- Command line arguments
- Configuration file
- Environment variables

See the individual example files for specific configuration options.

## Requirements

- Python 3.8+
- OpenCV (for camera examples)
- PyAudio (for audio examples)
- Additional requirements listed in each example

## Troubleshooting

Common issues and solutions:

1. Device Access
   - Ensure proper permissions
   - Check device connections
   - Verify drivers are installed

2. Performance
   - Adjust buffer sizes
   - Lower resolution/quality if needed
   - Check system resources

3. Streaming
   - Verify network connectivity
   - Check port availability
   - Ensure proper protocol support
