# Network Device Components

This document provides detailed information about the components that make up the network device module.

## NetworkDevice

The `NetworkDevice` class represents a network-based audio/video device such as an IP camera or IP microphone.

### Properties

- `device_id`: Unique device identifier (format: `{ip}:{port}`)
- `name`: Friendly device name
- `type`: Device type ('video' or 'audio')
- `ip`: Device IP address
- `port`: Device port number
- `protocol`: Communication protocol ('rtsp', 'rtmp', or 'http')
- `username`: Authentication username (optional)
- `password`: Authentication password (optional)
- `status`: Current device status (UNKNOWN, ONLINE, OFFLINE)
- `streams`: Dictionary of stream IDs to stream URLs

### Methods

```python
def get_base_url() -> str:
    """Get the base URL for the device (e.g., rtsp://user:pass@192.168.1.100:554)"""

def add_stream(stream_id: str, url: str) -> None:
    """Add a stream URL for this device"""

def remove_stream(stream_id: str) -> None:
    """Remove a stream URL from this device"""

def get_stream_url(stream_id: str) -> Optional[str]:
    """Get URL for a specific stream"""

def to_dict() -> Dict[str, Any]:
    """Convert device to dictionary for serialization"""
```

## NetworkDeviceManager

The `NetworkDeviceManager` class manages the lifecycle of network devices, including discovery, monitoring, and command handling.

### Configuration

```python
config = {
    "network_devices": {
        "scan_interval": 30,  # seconds
        "discovery_methods": ["onvif", "upnp", "mdns"]
    }
}
```

### Methods

```python
def start() -> None:
    """Start the device manager"""

def stop() -> None:
    """Stop the device manager"""

def add_device(name: str, ip: str, **kwargs) -> str:
    """Add a new network device"""

def remove_device(device_id: str) -> bool:
    """Remove a device"""

def update_device(device_id: str, **kwargs) -> bool:
    """Update device properties"""

def get_devices() -> Dict[str, NetworkDevice]:
    """Get all devices"""
```

### Events

The manager publishes events through MCP:

- Device added: `event/network_devices/added/{device_id}`
- Device removed: `event/network_devices/removed/{device_id}`
- Device updated: `event/network_devices/updated/{device_id}`
- Status changed: `event/network_devices/status/{device_id}`

### Commands

The manager handles commands through MCP:

- Scan devices: `command/network_devices/scan`
- Add device: `command/network_devices/add`
- Update device: `command/network_devices/update`
- Remove device: `command/network_devices/remove`

## NetworkDeviceMonitor

The `NetworkDeviceMonitor` class handles device discovery and status monitoring.

### Discovery Methods

1. **ONVIF Discovery**
   - Discovers ONVIF-compliant devices
   - Retrieves device capabilities and stream URLs
   - Supports authentication

2. **UPnP Discovery**
   - Discovers UPnP/DLNA devices
   - Identifies media servers and renderers
   - Retrieves device descriptions

3. **mDNS Discovery**
   - Discovers devices advertising RTSP services
   - Uses zero-configuration networking
   - Works with Bonjour/Avahi

### Methods

```python
def check_device_status(device: NetworkDevice) -> DeviceStatus:
    """Check device status through port connection"""

def discover_devices() -> List[Dict[str, Any]]:
    """Discover devices using configured methods"""

def process_discovered_devices(
    discovered: List[Dict[str, Any]],
    existing: Dict[str, NetworkDevice]
) -> List[Dict[str, Any]]:
    """Process discovered devices and filter existing ones"""
```

## Integration Example

Here's an example showing how the components work together:

```python
from rtaspi_devices.network import NetworkDeviceManager, NetworkDeviceMonitor
from rtaspi_core.mcp import MCPBroker

# Initialize components
config = {
    "network_devices": {
        "scan_interval": 30,
        "discovery_methods": ["onvif", "upnp", "mdns"]
    }
}
mcp_broker = MCPBroker()
manager = NetworkDeviceManager(config, mcp_broker)

# Subscribe to events
def handle_device_added(device_id: str, device_info: dict):
    print(f"Device added: {device_id}")
    print(f"Info: {device_info}")

mcp_broker.subscribe(
    "event/network_devices/added/#",
    handle_device_added
)

# Start manager
manager.start()

# Add device manually
device_id = manager.add_device(
    name="Front Camera",
    ip="192.168.1.100",
    port=554,
    type="video",
    protocol="rtsp"
)

# Get device info
devices = manager.get_devices()
device = devices[device_id]
print(f"Device status: {device.status}")
print(f"Base URL: {device.get_base_url()}")

# Stop manager
manager.stop()
```

## Best Practices

1. **Error Handling**
   - Always check return values from manager methods
   - Handle network timeouts and connection errors
   - Log errors for debugging

2. **Security**
   - Store credentials securely
   - Use HTTPS for web interfaces
   - Validate device certificates

3. **Resource Management**
   - Stop manager when not in use
   - Clean up streams properly
   - Monitor memory usage

4. **Event Handling**
   - Subscribe to relevant events
   - Handle events asynchronously
   - Implement error recovery

5. **Configuration**
   - Use appropriate scan intervals
   - Enable needed discovery methods
   - Configure timeouts properly
