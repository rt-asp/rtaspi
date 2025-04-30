# RTASPI Devices Module

The RTASPI Devices module provides a comprehensive framework for managing various types of audio/video devices, including:

- Local devices (cameras, microphones)
- Network devices (IP cameras, network audio devices)
- Remote desktop devices (VNC, RDP)
- Industrial devices (Modbus, OPC UA)
- Intercom systems
- VoIP devices

## Key Features

- Unified device management interface
- Automatic device discovery
- Stream management
- Event handling
- State persistence
- Protocol abstraction
- Security features

## Quick Start

```python
from rtaspi_devices import DeviceManager
from rtaspi_devices.network import NetworkDevice

# Create a device manager
manager = DeviceManager(config={
    "system": {
        "storage_path": "storage"
    }
})

# Add a network device
device = NetworkDevice(
    device_id="cam1",
    name="Front Camera",
    type="video",
    ip="192.168.1.100",
    port=554,
    protocol="rtsp"
)

# Start device management
manager.start()

# Get device status
status = device.get_status()
print(f"Device status: {status}")
```

## Module Structure

```
rtaspi_devices/
├── base/           # Base classes and interfaces
├── local/          # Local device management
├── network/        # Network device management
├── discovery/      # Device discovery mechanisms
└── protocols/      # Protocol implementations
```

## Installation

```bash
pip install rtaspi-devices
```

## Documentation

- [Architecture Overview](architecture.md)
- [Component Details](components.md)
- [Configuration Guide](configuration.md)
- [Advanced Usage](advanced_usage.md)

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing to this module.

## License

This module is part of the RTASPI project and is licensed under the same terms.
