# Security Examples

This directory contains examples demonstrating RTASPI's security and monitoring features.

## Examples

### 1. Motion Detection (`motion_detection.py`)
Demonstrates:
- Real-time motion detection
- Zone-based monitoring
- Alert generation
- Recording triggers

### 2. Alarm Integration (`alarm_integration.py`)
Shows how to:
- Connect to alarm systems
- Monitor sensors
- Handle events
- Trigger responses

### 3. Behavior Analysis (`behavior_analysis.py`)
Features:
- Pattern recognition
- Anomaly detection
- Activity logging
- Alert generation

### 4. Access Control (`access_control.py`)
Implements:
- Card reader integration
- Face recognition
- Authorization management
- Access logging

## Configuration Files

### `behavior_config.yaml`
```yaml
zones:
  - name: entrance
    coordinates: [100, 100, 300, 300]
    sensitivity: 0.8
  - name: restricted
    coordinates: [400, 200, 600, 400]
    sensitivity: 0.9

patterns:
  - name: loitering
    duration: 60
    zone: entrance
  - name: unauthorized_access
    zone: restricted
    time_range: [18:00, 06:00]
```

### `alarms_config.yaml`
```yaml
system:
  type: dsc
  port: /dev/ttyUSB0
  baudrate: 9600

zones:
  - id: 1
    name: front_door
    type: entry
  - id: 2
    name: motion_sensor
    type: motion

notifications:
  - type: email
    recipient: security@example.com
  - type: sms
    number: "+1234567890"
```

## Requirements

- RTASPI with security extensions
- OpenCV with CUDA support (recommended)
- TensorFlow/PyTorch for ML features
- Additional hardware-specific dependencies

## Usage

1. Configure security features:
```bash
# Copy and edit configuration files
cp behavior_config.yaml.example behavior_config.yaml
cp alarms_config.yaml.example alarms_config.yaml
```

2. Run examples:
```bash
# Motion detection
python motion_detection.py --camera 0 --config behavior_config.yaml

# Alarm system
python alarm_integration.py --config alarms_config.yaml

# Behavior analysis
python behavior_analysis.py --source rtsp://camera/stream

# Access control
python access_control.py --reader /dev/ttyACM0
```

## Hardware Support

### Supported Systems
- DSC PowerSeries
- Honeywell Vista
- Generic alarm panels
- RFID/NFC readers
- IP cameras

### Integration Methods
- Serial connection
- Network protocols
- USB interfaces
- GPIO (Raspberry Pi)

## Features

### Motion Detection
- Multi-zone monitoring
- Sensitivity adjustment
- False positive reduction
- Schedule-based activation

### Behavior Analysis
- Person tracking
- Object detection
- Path analysis
- Time-based patterns

### Access Control
- Multi-factor authentication
- Schedule management
- Visitor tracking
- Emergency protocols

## Alert System

Supports multiple notification methods:
- Email alerts
- SMS notifications
- Mobile push notifications
- Integration with monitoring services

## Best Practices

1. Camera Placement
   - Cover critical areas
   - Avoid blind spots
   - Consider lighting conditions
   - Maintain proper angles

2. System Configuration
   - Regular testing
   - Backup settings
   - Document changes
   - Monitor performance

3. Security Measures
   - Encrypt communications
   - Secure credentials
   - Regular updates
   - Access control

## Troubleshooting

Common issues and solutions:

1. Detection Issues
   - Adjust sensitivity
   - Check lighting
   - Verify camera position
   - Update ML models

2. Integration Problems
   - Verify connections
   - Check permissions
   - Test communication
   - Update firmware

3. Performance
   - Optimize resolution
   - Adjust processing load
   - Monitor resource usage
   - Consider hardware acceleration

## Support

For security-related issues:
- Check documentation
- Join security channel on Discord
- Submit detailed bug reports
- Follow security advisories
