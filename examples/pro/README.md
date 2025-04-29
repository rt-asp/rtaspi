# Professional Examples

This directory contains advanced examples demonstrating professional-level usage of the rtaspi library. These examples showcase complex integrations and real-world applications.

## Examples Overview

### 1. Advanced Camera Stream
**File:** `advanced_camera_stream.py`

Demonstrates sophisticated video processing capabilities:
- High-resolution camera streaming with H.264 encoding
- Real-time motion detection with configurable sensitivity
- Multiple video filters (denoising, sharpening, contrast)
- Zone-based motion analysis
- Multiple output streams (RTMP and RTSP)

### 2. Device Automation
**File:** `device_automation.py`

Shows complex device integration and automation:
- Integration with multiple device types (intercom, alarm, SIP phone)
- Rule-based automation system
- MQTT and Home Assistant integration
- Business hours-based conditional actions
- Multi-channel notifications

### 3. Industrial Integration
**File:** `industrial_integration.py`

Illustrates industrial protocol integration:
- OPC UA communication with PLCs
- Modbus communication with sensors
- Real-time data monitoring and logging
- Alert system with configurable thresholds
- MQTT-based data publishing
- Compressed data storage with retention policy

### 4. Security System
**File:** `security_system.py`

Demonstrates a complete security solution:
- Multi-camera surveillance system
- Integration with multiple alarm panels (DSC, Honeywell)
- Motion detection with zone-based analysis
- WebRTC-based secure video streaming
- Automated security responses
- Business hours awareness
- Event logging and notification system

## Usage

Each example can be run independently. Before running, ensure you have:

1. Installed the rtaspi library and its dependencies
2. Configured any necessary hardware (cameras, industrial equipment, etc.)
3. Updated configuration parameters (IP addresses, credentials, etc.)

To run an example:

```bash
python3 examples/pro/[example_file].py
```

## Requirements

- Python 3.7+
- rtaspi library
- Additional dependencies as required by specific examples:
  - OpenCV for video processing
  - OPC UA client library
  - Modbus client library
  - MQTT client
  - WebRTC libraries

## Notes

- These examples are intended for professional use and demonstrate advanced integration scenarios
- Security credentials in the examples should be replaced with proper secure values
- Some features may require specific hardware or network configurations
- Error handling and logging are implemented for production-grade reliability
