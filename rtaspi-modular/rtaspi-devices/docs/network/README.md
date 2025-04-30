# Network Device Module

The network device module provides functionality for managing network-based audio/video devices such as IP cameras and IP microphones. It handles device discovery, status monitoring, and management through various protocols including RTSP, RTMP, and HTTP.

## Features

- Device discovery using multiple methods (ONVIF, UPnP, mDNS)
- Automatic status monitoring
- Stream management
- Secure credential handling
- Event-based device state updates
- Persistent device configuration

## Basic Usage

```python
from rtaspi_devices.network import NetworkDeviceManager
from rtaspi_core.mcp import MCPBroker

# Initialize manager
config = {
    "network_devices": {
        "scan_interval": 30,
        "discovery_methods": ["onvif", "upnp", "mdns"]
    }
}
mcp_broker = MCPBroker()
manager = NetworkDeviceManager(config, mcp_broker)

# Start manager
manager.start()

# Add a device
device_id = manager.add_device(
    name="Camera 1",
    ip="192.168.1.100",
    port=554,
    type="video",
    protocol="rtsp",
    username="admin",
    password="password"
)

# Get device info
devices = manager.get_devices()
device = devices[device_id]
print(f"Device status: {device.status}")

# Stop manager
manager.stop()
```

## Configuration

The module accepts the following configuration options:

```yaml
network_devices:
  # Interval between device scans (seconds)
  scan_interval: 30
  
  # Device discovery methods to use
  discovery_methods:
    - onvif  # ONVIF protocol discovery
    - upnp   # UPnP protocol discovery
    - mdns   # mDNS protocol discovery
```

## Components

The module consists of three main components:

1. **NetworkDevice**: Base class for network devices, handling device properties and stream management.
2. **NetworkDeviceManager**: Manages device lifecycle, handles commands, and maintains device state.
3. **NetworkDeviceMonitor**: Handles device discovery and status monitoring.

For detailed component documentation, see [Components](components.md).

## Advanced Usage

The module supports advanced features like:

- Custom discovery methods
- Device filtering
- Stream configuration
- Event handling
- State persistence

For advanced usage examples, see [Advanced Usage](advanced_usage.md).

## Events

The module publishes the following events through MCP:

- `event/network_devices/added/{device_id}`: Device added
- `event/network_devices/removed/{device_id}`: Device removed
- `event/network_devices/updated/{device_id}`: Device updated
- `event/network_devices/status/{device_id}`: Device status changed

## Commands

The module handles the following commands through MCP:

- `command/network_devices/scan`: Scan for devices
- `command/network_devices/add`: Add a device
- `command/network_devices/update`: Update device properties
- `command/network_devices/remove`: Remove a device

## Dependencies

- rtaspi-core: Core functionality and MCP broker
- onvif: ONVIF protocol support (optional)
- upnpy: UPnP protocol support (optional)
- zeroconf: mDNS protocol support (optional)
