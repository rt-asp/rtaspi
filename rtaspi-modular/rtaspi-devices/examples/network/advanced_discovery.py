"""
Advanced network device discovery example.

This example demonstrates:
1. Custom protocol handlers
2. Advanced filtering
3. Device capabilities detection
4. State persistence
5. Custom discovery strategies
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from rtaspi_devices import DeviceManager
from rtaspi_devices.discovery import DiscoveryService, ProtocolHandler
from rtaspi_devices.events import EventSystem
from rtaspi_devices.network import NetworkDevice

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomProtocolHandler(ProtocolHandler):
    """Custom protocol handler for demonstration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.known_devices = {}

    async def discover(self, ip: str, port: int) -> Optional[Dict[str, Any]]:
        """
        Custom discovery logic.
        
        Args:
            ip: IP address to scan
            port: Port to scan
            
        Returns:
            Optional[Dict[str, Any]]: Device information if discovered
        """
        try:
            # Example: Custom handshake protocol
            device_info = await self._handshake(ip, port)
            if device_info:
                return {
                    "id": f"custom_{ip}_{port}",
                    "name": device_info.get("name", "Unknown Device"),
                    "type": device_info.get("type", "custom"),
                    "protocol": "custom",
                    "ip": ip,
                    "port": port,
                    "capabilities": device_info.get("capabilities", {})
                }
        except Exception as e:
            logger.debug(f"Discovery failed for {ip}:{port} - {e}")
        return None

    async def _handshake(self, ip: str, port: int) -> Optional[Dict[str, Any]]:
        """
        Simulate custom device handshake.
        
        In a real implementation, this would perform the actual protocol-specific
        communication with the device.
        """
        # Simulate finding different types of devices
        if port == 8000:
            return {
                "name": "Custom Camera",
                "type": "video",
                "capabilities": {
                    "resolution": ["1280x720", "1920x1080"],
                    "formats": ["h264", "mjpeg"],
                    "features": ["ptz", "night_vision"]
                }
            }
        elif port == 8001:
            return {
                "name": "Custom Microphone",
                "type": "audio",
                "capabilities": {
                    "formats": ["pcm", "aac"],
                    "channels": 2,
                    "sample_rate": 44100
                }
            }
        return None

class AdvancedDiscoveryService(DiscoveryService):
    """Extended discovery service with advanced features."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.device_filters = []
        self.discovery_strategies = []

    def add_filter(self, filter_func):
        """Add device filter."""
        self.device_filters.append(filter_func)

    def add_strategy(self, strategy):
        """Add discovery strategy."""
        self.discovery_strategies.append(strategy)

    async def scan(self) -> List[Dict[str, Any]]:
        """
        Enhanced scanning with filters and strategies.
        """
        devices = []

        # Apply discovery strategies
        for strategy in self.discovery_strategies:
            try:
                strategy_devices = await strategy.discover()
                devices.extend(strategy_devices)
            except Exception as e:
                logger.error(f"Strategy failed: {e}")

        # Apply filters
        for filter_func in self.device_filters:
            devices = [d for d in devices if filter_func(d)]

        return devices

async def main():
    # Create configuration
    config = {
        "system": {
            "storage_path": "storage/devices",
            "log_level": "INFO"
        },
        "devices": {
            "network": {
                "enabled": True,
                "discovery": {
                    "enabled": True,
                    "scan_ranges": [
                        "192.168.1.0/24",
                        "10.0.0.0/24"
                    ],
                    "protocols": [
                        "rtsp",
                        "onvif",
                        "custom"  # Our custom protocol
                    ],
                    "ports": {
                        "custom": [8000, 8001]  # Ports for custom protocol
                    },
                    "scan_interval": 30,
                    "timeout": 5,
                    "parallel_scans": 10,
                    "persistence": {
                        "enabled": True,
                        "file": "discovered_devices.json"
                    }
                }
            }
        }
    }

    # Create event system
    events = EventSystem()

    # Create discovery service
    discovery = AdvancedDiscoveryService(config["devices"]["network"]["discovery"])

    # Register custom protocol handler
    discovery.register_protocol_handler("custom", CustomProtocolHandler({}))

    # Add device filters
    discovery.add_filter(
        lambda d: d["type"] in ["video", "audio"]  # Only audio/video devices
    )
    discovery.add_filter(
        lambda d: any(  # Must support required formats
            fmt in d.get("capabilities", {}).get("formats", [])
            for fmt in ["h264", "aac"]
        )
    )

    # Create device manager
    manager = DeviceManager(config, events=events)

    try:
        # Start device management
        await manager.start()
        logger.info("Device manager started")

        # Initial discovery
        logger.info("Starting advanced device discovery...")
        discovered = await discovery.scan()
        
        # Process discovered devices
        for device_info in discovered:
            try:
                # Create appropriate device instance
                if device_info["type"] == "video":
                    device = NetworkDevice(
                        device_id=device_info["id"],
                        name=device_info["name"],
                        type=device_info["type"],
                        ip=device_info["ip"],
                        port=device_info["port"],
                        protocol=device_info["protocol"]
                    )
                    
                    # Configure device based on capabilities
                    if "capabilities" in device_info:
                        caps = device_info["capabilities"]
                        if "resolution" in caps:
                            device.supported_resolutions = caps["resolution"]
                        if "formats" in caps:
                            device.supported_formats = caps["formats"]
                    
                    # Add device to manager
                    await manager.add_device(device)
                    logger.info(f"Added device: {device.name}")
                    
                    # Example: Start stream if device supports h264
                    if "h264" in device.supported_formats:
                        stream = await manager.start_stream(
                            device_id=device.device_id,
                            format="h264",
                            resolution="1280x720"
                        )
                        logger.info(f"Started stream: {stream['id']}")
                
            except Exception as e:
                logger.error(f"Failed to process device: {e}")

        # Monitor devices
        logger.info("Monitoring devices (press Ctrl+C to stop)...")
        while True:
            devices = manager.get_devices()
            
            # Group devices by type and capability
            device_stats = {}
            for device in devices.values():
                device_type = device.type
                if device_type not in device_stats:
                    device_stats[device_type] = {
                        "total": 0,
                        "streaming": 0,
                        "formats": set()
                    }
                
                stats = device_stats[device_type]
                stats["total"] += 1
                stats["formats"].update(device.supported_formats)
                
                if device.device_id in manager.get_streams():
                    stats["streaming"] += 1
            
            # Log statistics
            logger.info("=" * 50)
            logger.info("Device Statistics:")
            for device_type, stats in device_stats.items():
                logger.info(f"\n{device_type.upper()}:")
                logger.info(f"  Total: {stats['total']}")
                logger.info(f"  Streaming: {stats['streaming']}")
                logger.info(f"  Formats: {', '.join(stats['formats'])}")
            logger.info("=" * 50)
            
            await asyncio.sleep(30)

    except KeyboardInterrupt:
        logger.info("Stopping...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Clean up
        await manager.stop()
        logger.info("Device manager stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
