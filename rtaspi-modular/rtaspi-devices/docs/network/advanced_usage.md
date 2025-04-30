# Advanced Network Device Usage

This document covers advanced usage scenarios and features of the network device module.

## Custom Discovery Methods

You can extend device discovery by implementing custom discovery methods:

```python
from rtaspi_devices.network import NetworkDeviceMonitor
from typing import List, Dict, Any

class CustomDeviceMonitor(NetworkDeviceMonitor):
    def __init__(self, config):
        super().__init__(config)
        self.discovery_methods.append("custom")

    def _discover_custom_devices(self) -> List[Dict[str, Any]]:
        """Custom device discovery implementation."""
        devices = []
        # Implement custom discovery logic
        # Example: Scan specific IP ranges
        for ip in self._scan_ip_range("192.168.1.0/24"):
            if self._check_device(ip):
                devices.append({
                    "name": f"Device {ip}",
                    "ip": ip,
                    "port": 554,
                    "type": "video",
                    "protocol": "rtsp"
                })
        return devices

    def discover_devices(self) -> List[Dict[str, Any]]:
        """Override to add custom discovery method."""
        devices = super().discover_devices()
        if "custom" in self.discovery_methods:
            try:
                custom_devices = self._discover_custom_devices()
                devices.extend(custom_devices)
            except Exception as e:
                logger.error(f"Custom discovery error: {e}")
        return devices
```

## Device Filtering

Implement device filtering to control which devices are added:

```python
from rtaspi_devices.network import NetworkDeviceManager
from typing import Dict, Any

class FilteredDeviceManager(NetworkDeviceManager):
    def __init__(self, config, mcp_broker):
        super().__init__(config, mcp_broker)
        self.allowed_ips = config.get("allowed_ips", [])
        self.allowed_types = config.get("allowed_types", ["video", "audio"])

    def _filter_device(self, device_info: Dict[str, Any]) -> bool:
        """Filter devices based on criteria."""
        if self.allowed_ips and device_info["ip"] not in self.allowed_ips:
            return False
        if device_info["type"] not in self.allowed_types:
            return False
        return True

    def add_device(self, **kwargs) -> str:
        """Override to add filtering."""
        if not self._filter_device(kwargs):
            raise ValueError("Device not allowed by filter")
        return super().add_device(**kwargs)
```

## Stream Configuration

Configure stream settings for different protocols:

```python
from rtaspi_devices.network import NetworkDevice
from typing import Dict, Any, Optional

class StreamConfiguredDevice(NetworkDevice):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream_configs: Dict[str, Dict[str, Any]] = {}

    def add_stream_config(
        self,
        stream_id: str,
        resolution: str = "1920x1080",
        framerate: int = 30,
        bitrate: str = "2M",
        audio: bool = True
    ) -> None:
        """Add stream configuration."""
        self.stream_configs[stream_id] = {
            "resolution": resolution,
            "framerate": framerate,
            "bitrate": bitrate,
            "audio": audio
        }

    def get_stream_url(self, stream_id: str) -> Optional[str]:
        """Get configured stream URL."""
        base_url = super().get_stream_url(stream_id)
        if not base_url:
            return None

        config = self.stream_configs.get(stream_id, {})
        if not config:
            return base_url

        # Add configuration parameters to URL
        params = []
        if "resolution" in config:
            params.append(f"resolution={config['resolution']}")
        if "framerate" in config:
            params.append(f"framerate={config['framerate']}")
        if "bitrate" in config:
            params.append(f"bitrate={config['bitrate']}")
        if "audio" in config:
            params.append(f"audio={int(config['audio'])}")

        if params:
            return f"{base_url}?{'&'.join(params)}"
        return base_url
```

## Event Handling

Implement advanced event handling:

```python
import asyncio
from rtaspi_devices.network import NetworkDeviceManager
from typing import Dict, Any, Callable

class EventDrivenManager(NetworkDeviceManager):
    def __init__(self, config, mcp_broker):
        super().__init__(config, mcp_broker)
        self.event_handlers: Dict[str, List[Callable]] = {
            "device_added": [],
            "device_removed": [],
            "device_updated": [],
            "status_changed": []
        }

    def add_event_handler(self, event: str, handler: Callable) -> None:
        """Add event handler."""
        if event not in self.event_handlers:
            raise ValueError(f"Unknown event: {event}")
        self.event_handlers[event].append(handler)

    async def _handle_event(self, event: str, data: Dict[str, Any]) -> None:
        """Handle event asynchronously."""
        handlers = self.event_handlers.get(event, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

    def _publish_device_added(self, device_id: str) -> None:
        """Override to add custom event handling."""
        super()._publish_device_added(device_id)
        device = self.devices[device_id]
        asyncio.create_task(
            self._handle_event("device_added", device.to_dict())
        )
```

## State Persistence

Implement advanced state persistence:

```python
import json
import sqlite3
from rtaspi_devices.network import NetworkDeviceManager
from typing import Dict, Any

class PersistentManager(NetworkDeviceManager):
    def __init__(self, config, mcp_broker):
        super().__init__(config, mcp_broker)
        self.db_path = os.path.join(self.storage_path, "devices.db")
        self._init_db()

    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    device_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    last_seen INTEGER NOT NULL
                )
            """)

    def _save_devices(self) -> None:
        """Override to use SQLite."""
        current_time = int(time.time())
        with sqlite3.connect(self.db_path) as conn:
            for device_id, device in self.devices.items():
                data = json.dumps(device.to_dict())
                conn.execute(
                    """
                    INSERT OR REPLACE INTO devices
                    (device_id, data, last_seen)
                    VALUES (?, ?, ?)
                    """,
                    (device_id, data, current_time)
                )

    def _load_saved_devices(self) -> None:
        """Override to use SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            for row in conn.execute("SELECT device_id, data FROM devices"):
                try:
                    device_id, data = row
                    device_data = json.loads(data)
                    device = NetworkDevice(
                        device_id=device_data["id"],
                        name=device_data["name"],
                        type=device_data["type"],
                        ip=device_data["ip"],
                        port=device_data["port"],
                        protocol=device_data["protocol"]
                    )
                    device.status = DeviceStatus[
                        device_data["status"].upper()
                    ]
                    device.streams = device_data.get("streams", {})
                    self.devices[device_id] = device
                except Exception as e:
                    logger.error(f"Error loading device {device_id}: {e}")
```

## Integration with External Systems

Example of integrating with external monitoring systems:

```python
from rtaspi_devices.network import NetworkDeviceManager
import requests
from typing import Dict, Any

class MonitoredManager(NetworkDeviceManager):
    def __init__(self, config, mcp_broker):
        super().__init__(config, mcp_broker)
        self.monitoring_url = config.get("monitoring_url")
        self.monitoring_token = config.get("monitoring_token")

    def _report_status(self, device_id: str, status: str) -> None:
        """Report device status to external system."""
        if not self.monitoring_url:
            return

        try:
            requests.post(
                f"{self.monitoring_url}/device/status",
                json={
                    "device_id": device_id,
                    "status": status
                },
                headers={
                    "Authorization": f"Bearer {self.monitoring_token}"
                }
            )
        except Exception as e:
            logger.error(f"Error reporting status: {e}")

    def _publish_device_status(self, device_id: str, status: DeviceStatus) -> None:
        """Override to add external reporting."""
        super()._publish_device_status(device_id, status)
        self._report_status(device_id, status.name.lower())
```

## Performance Optimization

Example of optimizing device scanning:

```python
from rtaspi_devices.network import NetworkDeviceMonitor
import asyncio
from typing import List, Dict, Any

class OptimizedMonitor(NetworkDeviceMonitor):
    def __init__(self, config):
        super().__init__(config)
        self.max_concurrent = config.get("max_concurrent_scans", 10)

    async def _check_device_async(self, ip: str, port: int) -> bool:
        """Asynchronous device check."""
        try:
            _, writer = await asyncio.open_connection(ip, port)
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False

    async def _scan_network_async(self, network: str) -> List[Dict[str, Any]]:
        """Scan network asynchronously."""
        devices = []
        sem = asyncio.Semaphore(self.max_concurrent)
        tasks = []

        async def check_ip(ip: str):
            async with sem:
                if await self._check_device_async(ip, 554):
                    devices.append({
                        "ip": ip,
                        "port": 554,
                        "type": "video",
                        "protocol": "rtsp"
                    })

        for ip in self._generate_ips(network):
            tasks.append(asyncio.create_task(check_ip(ip)))

        await asyncio.gather(*tasks)
        return devices

    def discover_devices(self) -> List[Dict[str, Any]]:
        """Override to use async scanning."""
        networks = ["192.168.1.0/24", "10.0.0.0/24"]
        all_devices = []

        for network in networks:
            devices = asyncio.run(self._scan_network_async(network))
            all_devices.extend(devices)

        return all_devices
```

## Security Considerations

1. **Credential Management**
   - Use environment variables or secure storage
   - Encrypt sensitive data
   - Implement credential rotation

2. **Network Security**
   - Validate device certificates
   - Use secure protocols
   - Implement access control

3. **Input Validation**
   - Validate all device parameters
   - Sanitize URLs and paths
   - Check protocol security

4. **Error Handling**
   - Implement proper error recovery
   - Log security events
   - Handle timeout scenarios

5. **Access Control**
   - Implement device permissions
   - Control stream access
   - Monitor usage patterns
