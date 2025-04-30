"""
Network device manager implementation.
"""

import logging
import os
import re
import time
from typing import Dict, Any, List, Optional

from rtaspi_core.mcp import MCPClient
from ..base.manager import DeviceManager
from .device import NetworkDevice
from ..base.device import DeviceStatus

logger = logging.getLogger("rtaspi.devices.network")


class NetworkDeviceManager(DeviceManager):
    """Manages network devices (IP cameras, IP microphones)."""

    def __init__(self, config: Dict[str, Any], mcp_broker: Any):
        """
        Initialize the network devices manager.

        Args:
            config (Dict[str, Any]): Manager configuration.
            mcp_broker (Any): MCP broker instance.
        """
        super().__init__(config, mcp_broker)

        # Configuration
        network_config = config.get("network_devices", {})
        self.scan_interval = network_config.get("scan_interval", None)  # Use base class default if not specified
        self.discovery_methods = network_config.get(
            "discovery_methods", ["onvif", "upnp", "mdns"]
        )

        # Initialize device storage
        self.devices: Dict[str, NetworkDevice] = {}

    def _get_client_id(self) -> str:
        """
        Get MCP client identifier.

        Returns:
            str: Client identifier.
        """
        return "network_devices_manager"

    def _subscribe_to_events(self) -> None:
        """Subscribe to MCP events."""
        self.mcp_broker.subscribe(
            "command/network_devices/#", self._handle_command
        )

    def _scan_devices(self) -> None:
        """Scan for network devices."""
        logger.info("Scanning for network devices...")

        # Check status of known devices
        for device_id, device in list(self.devices.items()):
            try:
                # Update device status through monitoring
                new_status = self._check_device_status(device)
                if device.status != new_status:
                    device.status = new_status
                    self._publish_device_status(device_id, new_status)
            except Exception as e:
                logger.error(f"Error checking device {device_id} status: {e}")

        # Discover new devices
        try:
            discovered_devices = self._discover_devices()
            for device_info in discovered_devices:
                try:
                    self.add_device(
                        name=device_info.get("name", f"Device {device_info['ip']}"),
                        ip=device_info["ip"],
                        port=device_info.get("port", 554),
                        type=device_info.get("type", "video"),
                        protocol=device_info.get("protocol", "rtsp"),
                        username=device_info.get("username", ""),
                        password=device_info.get("password", ""),
                        paths=device_info.get("paths", []),
                    )
                except Exception as e:
                    logger.error(f"Error adding discovered device: {e}")
        except Exception as e:
            logger.error(f"Error during device discovery: {e}")

        # Save current state
        self._save_devices()

    def _check_device_status(self, device: NetworkDevice) -> DeviceStatus:
        """
        Check device status.

        Args:
            device (NetworkDevice): Device to check.

        Returns:
            DeviceStatus: Current device status.
        """
        # TODO: Implement actual status checking logic
        return DeviceStatus.ONLINE

    def _discover_devices(self) -> List[Dict[str, Any]]:
        """
        Discover network devices using configured methods.

        Returns:
            List[Dict[str, Any]]: List of discovered devices.
        """
        discovered = []
        for method in self.discovery_methods:
            try:
                # TODO: Implement discovery methods
                pass
            except Exception as e:
                logger.error(f"Error during {method} discovery: {e}")
        return discovered

    def add_device(
        self,
        name: str,
        ip: str,
        port: int = None,
        type: str = None,
        protocol: str = None,
        username: str = None,
        password: str = None,
        paths: list = None,
    ) -> str:
        """
        Add a new network device.

        Args:
            name (str): Device name
            ip (str): Device IP address
            port (int, optional): Device port
            type (str, optional): Device type (video/audio)
            protocol (str, optional): Device protocol (rtsp/rtmp)
            username (str, optional): Authentication username
            password (str, optional): Authentication password
            paths (list, optional): List of stream paths

        Returns:
            str: Device ID

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Validate required fields
        if not name or not name.strip() or not ip or not ip.strip():
            raise ValueError("Name and IP address are required")

        # Validate types
        if not isinstance(name, str) or not isinstance(ip, str):
            raise ValueError("Name and IP address must be strings")

        # Validate port
        if port:
            if not isinstance(port, int):
                raise ValueError("Port must be an integer")
            if port < 1 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")
        port = port or 554  # Default to RTSP port

        # Validate type and protocol
        if type and type not in ["video", "audio"]:
            raise ValueError("Type must be 'video' or 'audio'")
        if protocol and protocol not in ["rtsp", "rtmp", "http"]:
            raise ValueError("Protocol must be 'rtsp', 'rtmp', or 'http'")

        # Validate IP address format
        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if not re.match(ip_pattern, ip):
            raise ValueError("Invalid IP address format")

        # Validate IP octets
        octets = ip.split(".")
        for octet in octets:
            value = int(octet)
            if value < 0 or value > 255:
                raise ValueError("Invalid IP address: octets must be between 0 and 255")

        # Create device ID and check for duplicates
        device_id = f"{ip}:{port}"
        if device_id in self.devices:
            raise ValueError(f"Device {device_id} already exists")

        # Create device instance
        device = NetworkDevice(
            device_id=device_id,
            name=name,
            type=type or "video",
            ip=ip,
            port=port,
            protocol=protocol or "rtsp",
            username=username or "",
            password=password or "",
        )

        # Add stream paths
        if paths:
            for path in paths:
                stream_id = f"{device_id}_{path}"
                device.add_stream(stream_id, path)

        # Store device and save state
        self.devices[device_id] = device
        self._save_devices()

        # Publish device added event
        self._publish_device_added(device_id)

        return device_id

    def remove_device(self, device_id: str) -> bool:
        """
        Remove a device.

        Args:
            device_id (str): Device identifier.

        Returns:
            bool: True if device was removed.

        Raises:
            ValueError: If device not found.
        """
        if device_id not in self.devices:
            raise ValueError(f"Device {device_id} not found")

        # Remove device and save state
        del self.devices[device_id]
        self._save_devices()

        # Publish device removed event
        self._publish_device_removed(device_id)

        return True

    def update_device(self, device_id: str, **kwargs) -> bool:
        """
        Update device properties.

        Args:
            device_id (str): Device identifier.
            **kwargs: Device properties to update.

        Returns:
            bool: True if device was updated.

        Raises:
            ValueError: If device not found.
        """
        if device_id not in self.devices:
            raise ValueError(f"Device {device_id} not found")

        device = self.devices[device_id]
        for key, value in kwargs.items():
            if hasattr(device, key):
                setattr(device, key, value)

        self._save_devices()
        self._publish_device_updated(device_id)
        return True

    def get_devices(self) -> Dict[str, NetworkDevice]:
        """
        Get all devices.

        Returns:
            Dict[str, NetworkDevice]: Dictionary of devices.
        """
        return self.devices

    def _handle_command(self, topic: str, payload: dict) -> None:
        """
        Handle MCP commands.

        Args:
            topic (str): Command topic.
            payload (dict): Command payload.
        """
        command = topic.split("/")[-1]

        try:
            if command == "scan":
                self._scan_devices()
            elif command == "add":
                try:
                    self.add_device(**payload)
                except (ValueError, TypeError) as e:
                    raise ValueError(str(e))
            elif command == "update":
                device_id = payload.pop("device_id")
                self.update_device(device_id, **payload)
            elif command == "remove":
                device_id = payload.get("device_id")
                if not device_id:
                    raise ValueError("Device ID is required")
                self.remove_device(device_id)
            else:
                raise ValueError(f"Unknown command: {command}")
        except Exception as e:
            logger.error(f"Error handling command {command}: {e}")
            raise

    def _publish_device_added(self, device_id: str) -> None:
        """
        Publish device added event.

        Args:
            device_id (str): Device identifier.
        """
        device = self.devices[device_id]
        self.mcp_broker.publish(
            f"event/network_devices/added/{device_id}",
            device.to_dict()
        )

    def _publish_device_removed(self, device_id: str) -> None:
        """
        Publish device removed event.

        Args:
            device_id (str): Device identifier.
        """
        self.mcp_broker.publish(
            f"event/network_devices/removed/{device_id}",
            {"device_id": device_id}
        )

    def _publish_device_updated(self, device_id: str) -> None:
        """
        Publish device updated event.

        Args:
            device_id (str): Device identifier.
        """
        device = self.devices[device_id]
        self.mcp_broker.publish(
            f"event/network_devices/updated/{device_id}",
            device.to_dict()
        )

    def _publish_device_status(self, device_id: str, status: DeviceStatus) -> None:
        """
        Publish device status event.

        Args:
            device_id (str): Device identifier.
            status (DeviceStatus): Device status.
        """
        self.mcp_broker.publish(
            f"event/network_devices/status/{device_id}",
            {"device_id": device_id, "status": status.name.lower()}
        )

    def _get_scan_interval(self) -> int:
        """
        Get scanning interval in seconds.

        Returns:
            int: Scanning interval in seconds.
        """
        if self.scan_interval is None:
            return super()._get_scan_interval()
        return self.scan_interval

    @property
    def scan_interval(self) -> Optional[int]:
        """Get scan interval."""
        return self.config.get("network_devices", {}).get("scan_interval")

    @scan_interval.setter
    def scan_interval(self, value: Optional[int]) -> None:
        """Set scan interval."""
        if "network_devices" not in self.config:
            self.config["network_devices"] = {}
        self.config["network_devices"]["scan_interval"] = value

    def _publish_devices_info(self) -> None:
        """Publish device information."""
        devices_info = {
            device_id: device.to_dict()
            for device_id, device in self.devices.items()
        }
        self.mcp_broker.publish(
            "event/network_devices/info",
            {"devices": devices_info}
        )

    def _publish_stream_stopped(self, stream_id: str, stream_info: Dict[str, Any]) -> None:
        """
        Publish stream stop information.

        Args:
            stream_id (str): Stream identifier.
            stream_info (Dict[str, Any]): Stream information.
        """
        self.mcp_broker.publish(
            f"event/network_devices/stream/stopped/{stream_id}",
            {
                "stream_id": stream_id,
                "device_id": stream_info.get("device_id"),
                "timestamp": time.time()
            }
        )

    def _save_devices(self) -> None:
        """Save current devices state."""
        devices_data = {
            device_id: device.to_dict()
            for device_id, device in self.devices.items()
        }
        state_file = os.path.join(self.storage_path, "network_devices.json")
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w") as f:
            import json
            json.dump(devices_data, f, indent=2)

    def _load_saved_devices(self) -> None:
        """Load devices from saved state."""
        state_file = os.path.join(self.storage_path, "network_devices.json")
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                import json
                devices_data = json.load(f)

            for device_id, device_data in devices_data.items():
                try:
                    device = NetworkDevice(
                        device_id=device_data["id"],
                        name=device_data["name"],
                        type=device_data["type"],
                        ip=device_data["ip"],
                        port=device_data["port"],
                        protocol=device_data["protocol"],
                        username="",  # Don't load sensitive data
                        password="",  # Don't load sensitive data
                    )
                    device.status = DeviceStatus[device_data["status"].upper()]
                    device.streams = device_data.get("streams", {})
                    self.devices[device_id] = device
                except Exception as e:
                    logger.error(f"Error loading device {device_id}: {e}")
