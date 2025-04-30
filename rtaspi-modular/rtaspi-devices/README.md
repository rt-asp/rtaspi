# RTASPI Devices Module

The RTASPI Devices module provides device management functionality for the RTASPI system. It handles both local devices (like USB cameras and microphones) and network devices (like IP cameras).

## Structure

```
rtaspi_devices/
├── base/               # Base device classes and interfaces
│   ├── __init__.py
│   └── device.py      # Core device abstractions
├── local/             # Local device management
│   ├── __init__.py
│   └── manager.py     # Local device manager implementation
├── network/           # Network device management
│   ├── __init__.py
│   └── manager.py     # Network device manager implementation
├── discovery/         # Device discovery mechanisms
│   ├── __init__.py
│   ├── local.py      # Local device discovery
│   └── network.py    # Network device discovery
└── protocols/         # Protocol implementations
    ├── __init__.py
    └── base.py       # Base protocol interfaces
```

## Features

- Abstract base classes for device representation
- Local device management (USB cameras, microphones)
- Network device management (IP cameras, network audio devices)
- Device discovery mechanisms
- Protocol support (RTSP, RTMP, etc.)
- Serialization support for device configurations

## Usage

### Basic Device Usage

```python
from rtaspi_devices import LocalDevice, NetworkDevice

# Create a local device
camera = LocalDevice(
    device_id="cam1",
    name="USB Webcam",
    type="video",
    system_path="/dev/video0"
)

# Create a network device
ip_camera = NetworkDevice(
    device_id="ipcam1",
    name="IP Camera",
    type="video",
    ip="192.168.1.100",
    port=554,
    protocol="rtsp"
)
```

### Device Management

```python
from rtaspi_devices.local import LocalDeviceManager
from rtaspi_devices.network import NetworkDeviceManager

# Initialize managers
local_manager = LocalDeviceManager()
network_manager = NetworkDeviceManager()

# Discover devices
local_devices = local_manager.discover_devices()
network_devices = network_manager.discover_devices()

# Get device status
status = local_devices[0].status
```

## Development

### Adding New Device Types

1. Create a new class inheriting from `Device`
2. Implement required abstract methods
3. Add type-specific functionality
4. Register with appropriate manager

Example:

```python
from rtaspi_devices import Device

class CustomDevice(Device):
    def __init__(self, device_id: str, name: str, type: str):
        super().__init__(device_id, name, type)
        
    def to_dict(self):
        result = super().to_dict()
        # Add custom fields
        return result
```

## Dependencies

- rtaspi-core: Core RTASPI functionality
- Python 3.9+

## License

This module is part of the RTASPI project and is licensed under the same terms.
