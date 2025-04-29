# Quick Start Guide

This guide will help you get started with RTASPI quickly. We'll cover basic setup and common use cases.

## Installation

```bash
pip install rtaspi
```

## Basic Usage Examples

### 1. Camera Stream

```python
from rtaspi.quick import camera

# Start a camera stream
cam = camera.start_camera()

# Add some video processing
cam.add_filter('brightness', value=1.2)
cam.add_filter('contrast', value=1.1)

# Stream to RTSP
cam.add_output('rtsp', port=8554)

# Start streaming
cam.start()
```

### 2. Microphone Recording

```python
from rtaspi.quick import microphone

# Start microphone recording
mic = microphone.start_microphone()

# Add audio filters
mic.add_filter('noise_reduction')
mic.add_filter('gain', db=10)

# Save to file
mic.add_output('file', path='recording.wav')

# Start recording
mic.start()
```

### 3. Motion Detection

```python
from rtaspi.quick import camera
from rtaspi.processing.video import detection

# Start camera with motion detection
cam = camera.start_camera()
detector = detection.MotionDetector()

# Configure motion detection
detector.sensitivity = 0.8
detector.min_area = 500

# Add detector to camera
cam.add_processor(detector)

# React to motion events
@detector.on_motion
def handle_motion(event):
    print(f"Motion detected at {event.timestamp}")
    print(f"Area: {event.area}, Confidence: {event.confidence}")

# Start camera
cam.start()
```

### 4. Web Interface

```python
from rtaspi.web import interface

# Start web interface
server = interface.WebServer(port=8080)

# Add devices
server.add_device('camera1', type='camera')
server.add_device('mic1', type='microphone')

# Start server
server.start()
```

## Command Line Interface

RTASPI also provides a powerful CLI:

```bash
# List available devices
rtaspi devices list

# Start a camera stream
rtaspi stream start camera0 --output rtsp --port 8554

# Start recording from microphone
rtaspi stream start mic0 --output file --path audio.wav

# Start web interface
rtaspi server start --port 8080
```

## Next Steps

- Read the [Configuration Guide](CONFIGURATION.md) to learn about customizing RTASPI
- Check out [Example Projects](PROJECTS.md) for more complex use cases
- Explore the [API Documentation](API.md) for detailed reference
- Learn about [Device Management](devices/README.md) for advanced device control
- See [Processing Guide](processing/README.md) for audio/video processing options

## Common Issues

### Device Detection

If devices are not detected automatically:

```python
from rtaspi.device_managers import discovery

# Scan for devices
devices = discovery.scan_devices()

# Print found devices
for device in devices:
    print(f"Found: {device.name} ({device.type})")
```

### Performance Optimization

For better performance:

```python
from rtaspi.core import config

# Configure processing options
config.set_config('processing', 'thread_pool_size', 4)
config.set_config('streaming', 'buffer_size', 1024 * 1024)
```

## Getting Help

- Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
- Join our [Discord Community](https://discord.gg/rtaspi)
- Open an issue on [GitHub](https://github.com/rtaspi/rtaspi/issues)
