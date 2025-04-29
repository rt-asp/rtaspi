"""
rtaspi - Real-Time Annotation and Stream Processing
MCP command handler for local devices
"""

import logging
from typing import Dict, Any, Callable, Awaitable

from ..core.mcp import MCPClient
from .stream_manager import StreamManager
from .utils.device import DeviceStatus

logger = logging.getLogger("CommandHandler")


class LocalDevicesCommandHandler:
    """Handles MCP commands for local devices."""

    def __init__(self, mcp_client: MCPClient, stream_manager: StreamManager):
        """
        Initialize the command handler.

        Args:
            mcp_client (MCPClient): MCP client for communication.
            stream_manager (StreamManager): Stream manager instance.
        """
        self.mcp_client = mcp_client
        self.stream_manager = stream_manager
        self.devices = {
            "video": {},  # device_id -> LocalDevice
            "audio": {},  # device_id -> LocalDevice
        }

    def set_devices(self, devices: Dict[str, Dict[str, Any]]):
        """
        Set the current device list.

        Args:
            devices (Dict[str, Dict[str, Any]]): Dictionary of video and audio devices.
        """
        self.devices = devices

    def _publish_devices_info(self):
        """Publish current device information via MCP."""
        # Convert device objects to dictionaries
        devices_dict = {
            "video": {
                dev_id: dev.to_dict() for dev_id, dev in self.devices["video"].items()
            },
            "audio": {
                dev_id: dev.to_dict() for dev_id, dev in self.devices["audio"].items()
            },
        }

        self.mcp_client.publish("local_devices/devices", devices_dict)

    def _publish_stream_stopped(self, stream_id: str, stream_info: dict):
        """
        Publish stream stopped event.

        Args:
            stream_id (str): ID of the stopped stream.
            stream_info (dict): Information about the stopped stream.
        """
        self.mcp_client.publish(
            "local_devices/stream/stopped",
            {
                "stream_id": stream_id,
                "device_id": stream_info["device_id"],
                "type": stream_info["type"],
            },
        )

    async def handle_command(self, topic: str, message: dict):
        """
        Handle an MCP command.

        Args:
            topic (str): Command topic.
            message (dict): Command message.

        Raises:
            ValueError: If topic format is invalid or command is unknown.
        """
        # Parse topic
        parts = topic.split("/")
        if len(parts) < 3:
            raise ValueError(f"Invalid topic format: {topic}")

        command = parts[2]

        try:
            if command == "scan":
                # Manual device scan request
                logger.info("Received scan devices command")
                self._publish_devices_info()

            elif command == "start_stream":
                # Start stream command
                device_id = message.get("device_id")
                protocol = message.get("protocol", "rtsp")

                if not device_id:
                    raise ValueError(
                        "Missing required device_id parameter for start_stream command"
                    )

                logger.info(
                    f"Received start {protocol} stream command for device {device_id}"
                )

                # Find device
                device = None
                for devices in [self.devices["video"], self.devices["audio"]]:
                    if device_id in devices:
                        device = devices[device_id]
                        break

                if not device:
                    raise ValueError(f"Device not found: {device_id}")

                # Start stream
                url = await self.stream_manager.start_stream(device, protocol=protocol)

                # Publish result
                self.mcp_client.publish(
                    "local_devices/command/result",
                    {
                        "command": "start_stream",
                        "device_id": device_id,
                        "protocol": protocol,
                        "success": True,
                        "url": url,
                    },
                )

            elif command == "stop_stream":
                # Stop stream command
                stream_id = message.get("stream_id")

                if not stream_id:
                    raise ValueError(
                        "Missing required stream_id parameter for stop_stream command"
                    )

                logger.info(f"Received stop stream command for stream {stream_id}")

                # Stop stream
                success = await self.stream_manager.stop_stream(stream_id)

                # Get stream info before it's deleted
                stream_info = self.stream_manager.get_stream_info(stream_id)
                if success and stream_info:
                    self._publish_stream_stopped(stream_id, stream_info)

                # Publish result
                self.mcp_client.publish(
                    "local_devices/command/result",
                    {
                        "command": "stop_stream",
                        "stream_id": stream_id,
                        "success": success,
                    },
                )

            elif command == "get_devices":
                # Get devices command
                logger.info("Received get devices command")
                self._publish_devices_info()

            elif command == "get_streams":
                # Get streams command
                logger.info("Received get streams command")
                self.mcp_client.publish(
                    "local_devices/command/result",
                    {
                        "command": "get_streams",
                        "streams": self.stream_manager.get_streams(),
                    },
                )

            else:
                raise ValueError(f"Unknown command: {command}")

        except Exception as e:
            logger.error(f"Error handling MCP command: {e}")
            # Publish error result
            self.mcp_client.publish(
                "local_devices/command/result",
                {"command": command, "success": False, "error": str(e)},
            )
            raise
