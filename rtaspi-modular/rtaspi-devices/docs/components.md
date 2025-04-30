# RTASPI Devices Components

This document details the key components of the RTASPI Devices module and their interactions.

## Base Components

### Device Base Classes

#### Device
```python
from rtaspi_devices.base.device import Device

class CustomDevice(Device):
    def __init__(self, device_id: str, name: str, type: str):
        super().__init__(device_id, name, type)
        
    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        # Add custom fields
        return result
```

The base `Device` class provides:
- Unique device identification
- Basic metadata management
- Status tracking
- Serialization support

#### DeviceManager
```python
from rtaspi_devices.base.manager import DeviceManager

class CustomManager(DeviceManager):
    def _get_client_id(self) -> str:
        return "custom_manager"
        
    def _scan_devices(self) -> None:
        # Implement device scanning
        pass
        
    def _subscribe_to_events(self) -> None:
        # Subscribe to relevant MCP events
        pass
```

The base `DeviceManager` class handles:
- Device lifecycle management
- Automatic device scanning
- Event subscription
- Stream management
- State persistence

## Device Types

### Local Devices

For managing physically connected devices:

```python
from rtaspi_devices.local import LocalDevice

device = LocalDevice(
    device_id="cam1",
    name="USB Camera",
    type="video",
    system_path="/dev/video0",
    driver="v4l2"
)
```

Features:
- System device detection
- Driver management
- Format/resolution handling
- Resource management

### Network Devices

For IP-based devices:

```python
from rtaspi_devices.network import NetworkDevice

device = NetworkDevice(
    device_id="ipcam1",
    name="IP Camera",
    type="video",
    ip="192.168.1.100",
    port=554,
    protocol="rtsp"
)
```

Features:
- Network discovery
- Protocol handling
- Stream management
- Authentication
- State persistence

### Industrial Devices

For industrial protocols:

```python
from rtaspi_devices.industrial import ModbusDevice

device = ModbusDevice(
    device_id="plc1",
    name="PLC Controller",
    type="control",
    ip="192.168.1.200",
    port=502
)
```

Features:
- Protocol-specific handling
- Data type conversion
- Error recovery
- State monitoring

### Remote Desktop

For remote desktop connections:

```python
from rtaspi_devices.remote import VNCDevice

device = VNCDevice(
    device_id="desktop1",
    name="Remote Desktop",
    type="screen",
    host="192.168.1.150",
    port=5900
)
```

Features:
- Connection management
- Screen capture
- Input handling
- Session management

## Protocol Handlers

### Base Protocol
```python
from rtaspi_devices.protocols import Protocol

class CustomProtocol(Protocol):
    def connect(self) -> bool:
        # Implement connection logic
        pass
        
    def disconnect(self) -> bool:
        # Implement disconnection logic
        pass
```

Available protocols:
- RTSP/RTMP for streaming
- Modbus/OPC UA for industrial
- VNC/RDP for remote desktop
- Custom protocol support

## Discovery Service

The discovery service provides device detection across different types:

```python
from rtaspi_devices.discovery import DiscoveryService

discovery = DiscoveryService(config={
    "network": {
        "scan_ranges": ["192.168.1.0/24"],
        "protocols": ["rtsp", "onvif"]
    }
})

devices = discovery.scan()
```

Features:
- Network scanning
- Protocol detection
- Device identification
- Capability discovery

## Stream Management

The stream manager handles media streams:

```python
from rtaspi_devices import StreamManager

manager = StreamManager(config={
    "storage_path": "/var/lib/rtaspi/streams",
    "formats": ["h264", "mjpeg"]
})

stream = await manager.start_stream(
    device_id="cam1",
    format="h264",
    resolution="1280x720"
)
```

Features:
- Stream initialization
- Format conversion
- Resource management
- Error handling

## Event System

The event system provides device and stream monitoring:

```python
from rtaspi_devices.events import EventSystem

events = EventSystem()

@events.on("device.connected")
def handle_connection(device_id: str):
    print(f"Device {device_id} connected")

@events.on("stream.started")
def handle_stream(stream_id: str):
    print(f"Stream {stream_id} started")
```

Events:
- Device status changes
- Stream state updates
- Error notifications
- System events

## State Management

The state manager handles persistence:

```python
from rtaspi_devices.state import StateManager

state = StateManager(storage_path="/var/lib/rtaspi/state")

# Save state
state.save({
    "devices": current_devices,
    "streams": active_streams
})

# Load state
saved_state = state.load()
```

Features:
- Configuration storage
- State persistence
- Recovery handling
- Backup/restore

## Utility Components

### Configuration
```python
from rtaspi_devices.utils.config import Config

config = Config.load("config.yaml")
manager = DeviceManager(config)
```

### Logging
```python
from rtaspi_devices.utils.logging import setup_logging

setup_logging(level="INFO", file="devices.log")
```

### Error Handling
```python
from rtaspi_devices.utils.errors import DeviceError

try:
    device.connect()
except DeviceError as e:
    logger.error(f"Connection failed: {e}")
```

## Integration Examples

### Basic Device Management
```python
from rtaspi_devices import DeviceManager
from rtaspi_devices.network import NetworkDevice

# Create manager
manager = DeviceManager(config)

# Add device
device = NetworkDevice(
    device_id="cam1",
    name="IP Camera",
    ip="192.168.1.100"
)

# Start management
manager.start()

# Get device status
status = device.get_status()
```

### Stream Handling
```python
from rtaspi_devices import StreamManager

# Create manager
stream_manager = StreamManager(config)

# Start stream
stream = await stream_manager.start_stream(
    device_id="cam1",
    format="h264"
)

# Monitor stream
@stream.on("data")
def handle_data(frame):
    process_frame(frame)
```

### Event Monitoring
```python
from rtaspi_devices.events import EventSystem

# Setup events
events = EventSystem()

# Monitor devices
@events.on("device.status")
def handle_status(device_id: str, status: str):
    if status == "offline":
        notify_admin(f"Device {device_id} went offline")

# Monitor streams
@events.on("stream.error")
def handle_error(stream_id: str, error: str):
    restart_stream(stream_id)
