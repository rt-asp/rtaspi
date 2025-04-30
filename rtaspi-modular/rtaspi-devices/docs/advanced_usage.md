# Advanced Usage Guide

This guide covers advanced usage scenarios and features of the RTASPI Devices module.

## Custom Device Types

### Creating Custom Device Classes

Extend the base Device class for custom functionality:

```python
from rtaspi_devices.base import Device
from typing import Dict, Any

class CustomDevice(Device):
    def __init__(self, device_id: str, name: str, custom_param: str):
        super().__init__(device_id, name, "custom")
        self.custom_param = custom_param
        self.custom_state = {}

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        result.update({
            "custom_param": self.custom_param,
            "custom_state": self.custom_state
        })
        return result

    async def initialize(self) -> bool:
        # Custom initialization logic
        return True

    async def cleanup(self) -> None:
        # Custom cleanup logic
        pass
```

### Custom Device Manager

Implement a custom device manager:

```python
from rtaspi_devices.base import DeviceManager
from typing import Dict, Any

class CustomDeviceManager(DeviceManager):
    def __init__(self, config: Dict[str, Any], mcp_broker: Any):
        super().__init__(config, mcp_broker)
        self.custom_config = config.get("custom", {})

    def _get_client_id(self) -> str:
        return "custom_device_manager"

    def _scan_devices(self) -> None:
        # Custom device discovery logic
        devices = self._discover_devices()
        for device in devices:
            self.devices[device.device_id] = device

    def _subscribe_to_events(self) -> None:
        self.mcp_client.subscribe("custom/events/#", self._handle_event)

    async def _handle_event(self, topic: str, payload: Dict[str, Any]) -> None:
        # Custom event handling logic
        pass
```

## Advanced Protocol Integration

### Custom Protocol Implementation

Create custom protocol handlers:

```python
from rtaspi_devices.protocols import Protocol
from typing import Optional, Dict, Any

class CustomProtocol(Protocol):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connection = None

    async def connect(self) -> bool:
        try:
            # Custom connection logic
            self.connection = await self._establish_connection()
            return True
        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    async def disconnect(self) -> bool:
        if self.connection:
            await self.connection.close()
            self.connection = None
        return True

    async def send_command(self, command: str) -> Optional[Dict[str, Any]]:
        if not self.connection:
            raise ConnectionError("Not connected")
        
        try:
            response = await self.connection.execute(command)
            return self._parse_response(response)
        except Exception as e:
            self.logger.error(f"Command failed: {e}")
            return None
```

## Advanced Stream Processing

### Custom Stream Pipeline

Implement custom stream processing:

```python
from rtaspi_devices.streaming import StreamPipeline
from typing import Any, Optional

class CustomPipeline(StreamPipeline):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.processors = []

    async def initialize(self) -> bool:
        # Setup processing components
        self.processors = [
            self._create_processor(cfg)
            for cfg in self.config.get("processors", [])
        ]
        return True

    async def process_frame(self, frame: Any) -> Optional[Any]:
        result = frame
        for processor in self.processors:
            result = await processor.process(result)
            if result is None:
                break
        return result

    def _create_processor(self, config: Dict[str, Any]) -> Any:
        processor_type = config["type"]
        if processor_type == "filter":
            return FilterProcessor(config)
        elif processor_type == "transform":
            return TransformProcessor(config)
        else:
            raise ValueError(f"Unknown processor type: {processor_type}")
```

## Advanced Event Handling

### Custom Event Processors

Create specialized event handlers:

```python
from rtaspi_devices.events import EventProcessor
from typing import Dict, Any, Callable

class CustomEventProcessor(EventProcessor):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, event_type: str, handler: Callable) -> None:
        self.handlers[event_type] = handler

    async def process_event(self, event: Dict[str, Any]) -> None:
        event_type = event.get("type")
        if event_type in self.handlers:
            try:
                await self.handlers[event_type](event)
            except Exception as e:
                self.logger.error(f"Event handling failed: {e}")
```

## Integration Patterns

### Device Federation

Manage devices across multiple systems:

```python
from rtaspi_devices import DeviceFederation
from typing import List, Dict, Any

class DeviceFederation:
    def __init__(self, config: Dict[str, Any]):
        self.managers = []
        self.device_index = {}

    async def add_manager(self, manager: DeviceManager) -> None:
        self.managers.append(manager)
        await manager.start()
        self._update_index(manager)

    def _update_index(self, manager: DeviceManager) -> None:
        devices = manager.get_devices()
        for device_id, device in devices.items():
            self.device_index[device_id] = {
                "device": device,
                "manager": manager
            }

    async def get_device(self, device_id: str) -> Optional[Device]:
        if device_id in self.device_index:
            return self.device_index[device_id]["device"]
        return None
```

### Load Balancing

Distribute device management across systems:

```python
from rtaspi_devices import LoadBalancer
from typing import List, Dict, Any

class LoadBalancer:
    def __init__(self, config: Dict[str, Any]):
        self.nodes = []
        self.allocation = {}

    def add_node(self, node: DeviceManager) -> None:
        self.nodes.append({
            "manager": node,
            "load": 0
        })

    def allocate_device(self, device: Device) -> DeviceManager:
        # Find least loaded node
        node = min(self.nodes, key=lambda x: x["load"])
        node["load"] += 1
        self.allocation[device.device_id] = node["manager"]
        return node["manager"]

    def rebalance(self) -> None:
        # Redistribute devices if needed
        pass
```

## Advanced Security

### Custom Authentication

Implement custom authentication:

```python
from rtaspi_devices.security import Authenticator
from typing import Optional, Dict, Any

class CustomAuthenticator(Authenticator):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.auth_provider = self._setup_provider(config)

    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[str]:
        try:
            token = await self.auth_provider.verify(credentials)
            return token
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return None

    async def validate_token(self, token: str) -> bool:
        return await self.auth_provider.validate(token)
```

### Encryption Handler

Custom encryption implementation:

```python
from rtaspi_devices.security import Encryptor
from typing import Dict, Any

class CustomEncryptor(Encryptor):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cipher = self._create_cipher(config)

    def encrypt(self, data: bytes) -> bytes:
        return self.cipher.encrypt(data)

    def decrypt(self, data: bytes) -> bytes:
        return self.cipher.decrypt(data)
```

## Performance Optimization

### Custom Cache Implementation

Implement device-specific caching:

```python
from rtaspi_devices.cache import Cache
from typing import Any, Optional

class DeviceCache(Cache):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cache_size = config.get("cache_size", 1000)
        self.cache = {}

    async def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            return self.cache[key]
        return None

    async def set(self, key: str, value: Any) -> None:
        if len(self.cache) >= self.cache_size:
            self._evict()
        self.cache[key] = value

    def _evict(self) -> None:
        # Implement cache eviction strategy
        pass
```

## Testing and Monitoring

### Custom Device Monitor

Implement specialized monitoring:

```python
from rtaspi_devices.monitoring import Monitor
from typing import Dict, Any

class DeviceMonitor(Monitor):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.metrics = {}

    async def collect_metrics(self) -> Dict[str, Any]:
        for device_id, device in self.devices.items():
            self.metrics[device_id] = await self._get_device_metrics(device)
        return self.metrics

    async def _get_device_metrics(self, device: Device) -> Dict[str, Any]:
        return {
            "status": device.status,
            "uptime": device.get_uptime(),
            "error_count": device.get_error_count(),
            "bandwidth": await device.get_bandwidth()
        }
