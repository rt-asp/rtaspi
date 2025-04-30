"""
Example demonstrating integration between devices and other RTASPI modules.
"""

import asyncio
import logging
from rtaspi_devices import DeviceManager
from rtaspi_devices.network import NetworkDevice
from rtaspi_core.config import RTASPIConfig, create_config_manager
from rtaspi_core.mcp import MCPBroker

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Load core configuration
    config_manager = create_config_manager()
    core_config = config_manager.load("config/core.yaml")

    # Create MCP broker for inter-module communication
    mcp_broker = MCPBroker(core_config.get("mcp", {}))
    await mcp_broker.start()

    # Create device configuration
    device_config = {
        "system": {
            "storage_path": "storage/devices",
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
            }
        },
        "streaming": {
            "formats": ["h264", "mjpeg"],
            "port_range": {
                "start": 8000,
                "end": 9000
            }
        }
    }

    # Create network device manager
    from rtaspi_devices.network import NetworkDeviceManager
    manager = NetworkDeviceManager(device_config, mcp_broker=mcp_broker)

    try:
        # Start device management
        await manager.start()
        logger.info("Device manager started")

        # Create and add a network camera
        camera = NetworkDevice(
            device_id="cam1",
            name="Front Camera",
            type="video",
            ip="192.168.1.100",
            port=554,
            protocol="rtsp"
        )
        
        # Start a video stream
        stream = await manager.start_stream(
            device_id=camera.device_id,
            format="h264",
            resolution="1280x720"
        )
        logger.info(f"Started stream: {stream['id']}")

        # Example: Subscribe to device events
        def handle_device_event(topic, payload):
            logger.info(f"Device event: {topic} - {payload}")

        mcp_broker.subscribe("devices/+/events", handle_device_event)

        # Example: Send device command
        await mcp_broker.publish(
            f"devices/{camera.device_id}/commands",
            {
                "command": "set_parameter",
                "parameter": "brightness",
                "value": 50
            }
        )

        # Example: Get device status through MCP
        response = await mcp_broker.request(
            f"devices/{camera.device_id}/status",
            {}
        )
        logger.info(f"Device status: {response}")

        # Example: Stream processing with pipeline
        pipeline_config = {
            "input": {
                "stream_id": stream["id"],
                "format": "h264"
            },
            "processors": [
                {
                    "type": "motion_detection",
                    "sensitivity": 0.5
                },
                {
                    "type": "object_detection",
                    "model": "yolov3",
                    "confidence": 0.7
                }
            ],
            "output": {
                "format": "mjpeg",
                "port": 8080
            }
        }

        # Start pipeline
        pipeline_id = await mcp_broker.request(
            "pipelines/create",
            pipeline_config
        )
        logger.info(f"Started pipeline: {pipeline_id}")

        # Keep running to monitor events
        logger.info("Monitoring events (press Ctrl+C to stop)...")
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        # Clean up
        await manager.stop()
        await mcp_broker.stop()
        logger.info("Cleanup complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
