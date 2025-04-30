"""
Quick start example demonstrating device discovery and event handling.
"""

import asyncio
import logging
from rtaspi_devices import DeviceManager
from rtaspi_devices.events import EventSystem

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Event handlers
async def handle_device_discovered(device_info):
    """Handle device discovery events."""
    logger.info(f"New device discovered: {device_info['name']} ({device_info['id']})")
    logger.info(f"Type: {device_info['type']}")
    logger.info(f"Status: {device_info['status']}")

async def handle_device_status(device_id, status):
    """Handle device status changes."""
    logger.info(f"Device {device_id} status changed to: {status}")

async def handle_stream_started(stream_info):
    """Handle stream start events."""
    logger.info(f"Stream started: {stream_info['id']}")
    logger.info(f"Device: {stream_info['device_id']}")
    logger.info(f"Format: {stream_info['format']}")

async def main():
    # Create configuration
    config = {
        "system": {
            "storage_path": "storage",
            "log_level": "INFO"
        },
        "devices": {
            "network": {
                "enabled": True,
                "discovery": {
                    "enabled": True,
                    "scan_ranges": ["192.168.1.0/24"],
                    "protocols": ["rtsp", "onvif"]
                }
            },
            "local": {
                "enabled": True,
                "auto_connect": True,
                "drivers": ["v4l2", "alsa"]
            }
        }
    }

    # Create event system
    events = EventSystem()

    # Register event handlers
    events.on("device.discovered", handle_device_discovered)
    events.on("device.status", handle_device_status)
    events.on("stream.started", handle_stream_started)

    # Create device manager
    manager = DeviceManager(config, events=events)

    try:
        # Start device management
        await manager.start()
        logger.info("Device manager started")

        # Wait for devices to be discovered
        logger.info("Scanning for devices...")
        await asyncio.sleep(10)

        # List discovered devices
        devices = manager.get_devices()
        logger.info(f"Found {len(devices)} devices:")
        
        for device_id, device in devices.items():
            logger.info(f"- {device.name} ({device_id})")
            
            # Start stream if it's a video device
            if device.type == "video":
                try:
                    stream = await manager.start_stream(
                        device_id=device_id,
                        format="h264",
                        resolution="1280x720"
                    )
                    logger.info(f"  Started stream: {stream['id']}")
                except Exception as e:
                    logger.error(f"  Failed to start stream: {e}")

        # Keep running to monitor events
        logger.info("Monitoring events (press Ctrl+C to stop)...")
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        # Clean up
        await manager.stop()
        logger.info("Device manager stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
