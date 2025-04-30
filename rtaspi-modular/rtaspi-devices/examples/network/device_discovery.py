"""
Example demonstrating network device discovery functionality.

This example shows how to:
1. Configure network discovery
2. Scan for devices
3. Handle discovered devices
4. Monitor device status
"""

import asyncio
import logging
from rtaspi_devices import DeviceManager
from rtaspi_devices.discovery import DiscoveryService
from rtaspi_devices.events import EventSystem

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Event handlers
async def handle_device_discovered(device_info):
    """Handle device discovery events."""
    logger.info("=" * 50)
    logger.info("New device discovered:")
    logger.info(f"ID: {device_info['id']}")
    logger.info(f"Name: {device_info['name']}")
    logger.info(f"Type: {device_info['type']}")
    logger.info(f"Protocol: {device_info.get('protocol', 'unknown')}")
    logger.info(f"IP: {device_info.get('ip', 'unknown')}")
    logger.info(f"Port: {device_info.get('port', 'unknown')}")
    logger.info(f"Status: {device_info['status']}")
    
    # Log capabilities if available
    if 'capabilities' in device_info:
        logger.info("Capabilities:")
        for cap, value in device_info['capabilities'].items():
            logger.info(f"  {cap}: {value}")
    logger.info("=" * 50)

async def handle_device_status(device_id, status):
    """Handle device status changes."""
    logger.info(f"Device {device_id} status changed to: {status}")

async def handle_device_error(device_id, error):
    """Handle device errors."""
    logger.error(f"Device {device_id} error: {error}")

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
                        "192.168.1.0/24",  # Local network
                        "10.0.0.0/24"      # Additional network
                    ],
                    "protocols": [
                        "rtsp",    # IP cameras
                        "onvif",   # ONVIF devices
                        "http",    # Web cameras
                        "mdns"     # mDNS/Bonjour devices
                    ],
                    "scan_interval": 30,  # Scan every 30 seconds
                    "timeout": 5,         # 5 second timeout per device
                    "parallel_scans": 10  # Scan 10 devices in parallel
                }
            }
        }
    }

    # Create event system
    events = EventSystem()

    # Register event handlers
    events.on("device.discovered", handle_device_discovered)
    events.on("device.status", handle_device_status)
    events.on("device.error", handle_device_error)

    # Create discovery service
    discovery = DiscoveryService(config["devices"]["network"]["discovery"])

    # Create device manager
    manager = DeviceManager(config, events=events)

    try:
        # Start device management
        await manager.start()
        logger.info("Device manager started")

        # Initial discovery
        logger.info("Starting initial device discovery...")
        discovered = await discovery.scan()
        logger.info(f"Initial discovery found {len(discovered)} devices")

        # Monitor for new devices
        logger.info("Monitoring for devices (press Ctrl+C to stop)...")
        while True:
            # Get current devices
            devices = manager.get_devices()
            
            # Log device count by type
            device_types = {}
            for device in devices.values():
                device_type = device.type
                device_types[device_type] = device_types.get(device_type, 0) + 1
            
            logger.info("-" * 30)
            logger.info(f"Active devices: {len(devices)}")
            for device_type, count in device_types.items():
                logger.info(f"  {device_type}: {count}")
            logger.info("-" * 30)

            # Wait before next scan
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
