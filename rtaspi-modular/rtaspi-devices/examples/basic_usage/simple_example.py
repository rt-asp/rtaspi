"""
Basic example demonstrating core device management functionality.
"""

import asyncio
from rtaspi_devices import DeviceManager
from rtaspi_devices.network import NetworkDevice

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
                    "scan_ranges": ["192.168.1.0/24"]
                }
            }
        }
    }

    # Create device manager
    manager = DeviceManager(config)

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
    await manager.start()

    try:
        # Wait for device to be discovered
        await asyncio.sleep(5)

        # Get device status
        status = device.get_status()
        print(f"Device status: {status}")

        # Start a stream
        stream = await manager.start_stream(
            device_id="cam1",
            format="h264",
            resolution="1280x720"
        )
        print(f"Stream started: {stream}")

        # Keep running for a while
        await asyncio.sleep(30)

        # Stop the stream
        await manager.stop_stream(stream["id"])
        print("Stream stopped")

    finally:
        # Clean up
        await manager.stop()

if __name__ == "__main__":
    asyncio.run(main())
