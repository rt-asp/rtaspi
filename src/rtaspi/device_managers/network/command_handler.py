"""
rtaspi - Real-Time Annotation and Stream Processing
Network device command handler
"""

import logging
import uuid
from typing import Dict, Optional

from ...core.mcp import MCPClient
from ...device_managers.utils.device import NetworkDevice, DeviceStatus

logger = logging.getLogger("NetworkCommandHandler")


class NetworkCommandHandler:
    """Handles MCP commands for network devices."""

    def __init__(self, mcp_client: MCPClient):
        """
        Initialize the command handler.

        Args:
            mcp_client (MCPClient): MCP client for communication.
        """
        self.mcp_client = mcp_client
        self.devices: Dict[str, NetworkDevice] = {}

    def set_devices(self, devices: Dict[str, NetworkDevice]):
        """
        Set the current device list.

        Args:
            devices (Dict[str, NetworkDevice]): Dictionary of devices.
        """
        self.devices = devices

    def _publish_devices_info(self):
        """Publish current device information via MCP."""
        devices_dict = {
            device_id: device.to_dict()
            for device_id, device in self.devices.items()
            if isinstance(device, NetworkDevice)
        }
        self.mcp_client.publish("network_devices/devices", devices_dict)

    def _publish_stream_stopped(self, stream_id: str, stream_info: dict):
        """
        Publish stream stopped event.

        Args:
            stream_id (str): ID of the stopped stream.
            stream_info (dict): Information about the stopped stream.
        """
        self.mcp_client.publish(
            "network_devices/stream/stopped",
            {"stream_id": stream_id, "device_id": stream_info["device_id"]},
        )

    async def handle_command(self, topic: str, payload: dict):
        """
        Handle an MCP command.

        Args:
            topic (str): Command topic.
            payload (dict): Command message.

        Raises:
            ValueError: When command is invalid or required parameters are missing.
        """
        # Parse command from topic
        parts = topic.split("/")
        if len(parts) < 3:
            raise ValueError(f"Invalid command topic format: {topic}")

        command = parts[2]

        try:
            if command == "add":
                # Validate required fields
                if not all(key in payload for key in ["name", "ip", "port"]):
                    raise ValueError("Missing required fields for add command")

                # Add new device
                device_id = self.add_device(
                    name=payload["name"],
                    ip=payload["ip"],
                    port=payload["port"],
                    username=payload.get("username", ""),
                    password=payload.get("password", ""),
                    type=payload.get("type", "video"),
                    protocol=payload.get("protocol", "rtsp"),
                    paths=payload.get("paths", []),
                )

                self.mcp_client.publish(
                    "network_devices/command/result",
                    {"command": "add", "success": True, "device_id": device_id},
                )

            elif command == "remove":
                # Validate required fields
                if "device_id" not in payload:
                    raise ValueError("Missing device_id for remove command")

                # Remove device
                success = self.remove_device(payload["device_id"])
                self.mcp_client.publish(
                    "network_devices/command/result",
                    {
                        "command": "remove",
                        "success": success,
                        "device_id": payload["device_id"],
                    },
                )

            elif command == "update":
                # Validate required fields
                if "device_id" not in payload:
                    raise ValueError("Missing device_id for update command")

                # Update device
                device_id = payload.pop("device_id")
                success = self.update_device(device_id, **payload)
                self.mcp_client.publish(
                    "network_devices/command/result",
                    {"command": "update", "success": success, "device_id": device_id},
                )

            elif command == "scan":
                # Manual device scan request
                self._publish_devices_info()
                self.mcp_client.publish(
                    "network_devices/command/result",
                    {"command": "scan", "success": True},
                )

            else:
                raise ValueError(f"Unknown command: {command}")

        except Exception as e:
            logger.error(f"Error handling command: {e}")
            self.mcp_client.publish(
                "network_devices/command/result",
                {"command": command, "success": False, "error": str(e)},
            )
            raise

    def add_device(
        self,
        name: str,
        ip: str,
        port: int,
        username: str = "",
        password: str = "",
        type: str = "video",
        protocol: str = "rtsp",
        paths: Optional[list] = None,
    ) -> str:
        """
        Add a new network device.

        Args:
            name (str): Device name.
            ip (str): Device IP address.
            port (int): Device port.
            username (str, optional): Authentication username.
            password (str, optional): Authentication password.
            type (str, optional): Device type ('video' or 'audio').
            protocol (str, optional): Protocol ('rtsp', 'rtmp', 'http').
            paths (list, optional): List of stream paths.

        Returns:
            str: ID of the added device.

        Raises:
            ValueError: If parameters are invalid or device already exists.
        """
        # Create device ID
        device_id = str(uuid.uuid4())

        # Create network device object
        device = NetworkDevice(
            device_id=device_id,
            name=name,
            type=type,
            ip=ip,
            port=port,
            username=username,
            password=password,
            protocol=protocol,
        )
        device.status = DeviceStatus.UNKNOWN

        # Add stream paths
        if paths:
            for i, path in enumerate(paths):
                stream_id = f"{device_id}_{i}"
                device.streams[stream_id] = f"{device.get_base_url()}/{path}"

        # Add device to list
        self.devices[device_id] = device

        # Publish device added event
        self.mcp_client.publish("network_devices/device/added", device.to_dict())

        logger.info(f"Added network device: {name} ({ip}:{port})")
        return device_id

    def remove_device(self, device_id: str) -> bool:
        """
        Remove a network device.

        Args:
            device_id (str): Device identifier.

        Returns:
            bool: True if device was removed, False otherwise.
        """
        if device_id not in self.devices:
            logger.warning(f"Attempt to remove non-existent device: {device_id}")
            return False

        # Remove device
        del self.devices[device_id]

        # Publish device removed event
        self.mcp_client.publish(
            "network_devices/device/removed", {"device_id": device_id}
        )

        logger.info(f"Removed network device: {device_id}")
        return True

    def update_device(self, device_id: str, **kwargs) -> bool:
        """
        Update a network device's properties.

        Args:
            device_id (str): Device identifier.
            **kwargs: Device properties to update.

        Returns:
            bool: True if update was successful, False otherwise.

        Raises:
            ValueError: If device_id doesn't exist or invalid properties provided.
        """
        if device_id not in self.devices:
            logger.warning(f"Attempt to update non-existent device: {device_id}")
            return False

        device = self.devices[device_id]

        # Validate port if provided
        if "port" in kwargs:
            port = kwargs["port"]
            if not isinstance(port, int) or port < 1 or port > 65535:
                raise ValueError("Invalid port number")

        # Validate type if provided
        if "type" in kwargs:
            if kwargs["type"] not in ["video", "audio"]:
                raise ValueError("Type must be 'video' or 'audio'")

        # Validate protocol if provided
        if "protocol" in kwargs:
            if kwargs["protocol"] not in ["rtsp", "rtmp", "http"]:
                raise ValueError("Protocol must be 'rtsp', 'rtmp', or 'http'")

        # Update device properties
        for key, value in kwargs.items():
            if hasattr(device, key):
                setattr(device, key, value)

        # Publish update event
        self.mcp_client.publish(
            "network_devices/device/updated",
            {"device_id": device_id, "updates": kwargs},
        )

        logger.info(f"Updated network device {device_id}")
        return True
