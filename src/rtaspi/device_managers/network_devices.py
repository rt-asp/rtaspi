"""
rtaspi - Real-Time Annotation and Stream Processing
Network devices manager (IP cameras, IP microphones)
"""

import logging
import os
from typing import Dict

from ..device_managers.base import DeviceManager
from ..device_managers.utils.device import NetworkDevice, DeviceStatus
from .network.state_manager import NetworkStateManager
from .network.device_monitor import NetworkDeviceMonitor
from .network.command_handler import NetworkCommandHandler

logger = logging.getLogger("NetworkDevices")


class NetworkDevicesManager(DeviceManager):
    """Manages network devices (IP cameras, IP microphones)."""

    def __init__(self, config, mcp_broker):
        """
        Initialize the network devices manager.

        Args:
            config (dict): Manager configuration.
            mcp_broker (MCPBroker): MCP broker instance.
        """
        super().__init__(config, mcp_broker)

        # Initialize components
        self.state_manager = NetworkStateManager(self.storage_path)
        self.device_monitor = NetworkDeviceMonitor(config)
        self.command_handler = NetworkCommandHandler(self.mcp_client)

        # Device state
        self.devices: Dict[str, NetworkDevice] = {}

        # Configuration
        network_devices_config = config.get("network_devices", {})
        self.scan_interval = network_devices_config.get("scan_interval", 30)
        self.discovery_methods = network_devices_config.get(
            "discovery_methods", ["onvif", "upnp", "mdns"]
        )
        self.discovery_modules = self.device_monitor.get_discovery_modules()

    def start(self):
        """Start the network devices manager."""
        logger.info("Starting network devices manager...")
        self.running = True
        self._load_saved_devices()
        self._subscribe_to_events()
        self._scan_devices()
        logger.info("Network devices manager started")

    def stop(self):
        """Stop the network devices manager."""
        logger.info("Stopping network devices manager...")
        self.running = False
        self.mcp_client.close()
        logger.info("Network devices manager stopped")

    def _get_client_id(self) -> str:
        """
        Get the MCP client ID.

        Returns:
            str: Client identifier.
        """
        return "network_devices_manager"

    def _subscribe_to_events(self):
        """Subscribe to MCP events."""
        self.mcp_client.subscribe(
            "command/network_devices/#", self.command_handler.handle_command
        )

    def _load_saved_devices(self):
        """Load devices from saved state."""
        self.devices = self.state_manager.load_state()
        self.command_handler.set_devices(self.devices)

    def _save_devices(self):
        """Save current devices state."""
        self.state_manager.save_state(self.devices)

    def _scan_devices(self):
        """Scan network devices."""
        logger.info("Scanning for network devices...")
        # Check status of known devices
        for device_id, device in list(self.devices.items()):
            if isinstance(device, NetworkDevice):
                device.status = self.device_monitor.check_device_status(device)

        # Discover new devices
        discovered_devices = self.device_monitor.discover_devices()
        new_devices = self.device_monitor.process_discovered_devices(
            discovered_devices, self.devices
        )

        # Add new devices
        for device_info in new_devices:
            try:
                self.add_device(
                    name=device_info.get("name", f"Device {device_info['ip']}"),
                    ip=device_info["ip"],
                    port=device_info["port"],
                    type=device_info.get("type", "video"),
                    protocol=device_info.get("protocol", "rtsp"),
                    username=device_info.get("username", ""),
                    password=device_info.get("password", ""),
                    paths=device_info.get("paths", []),
                )
            except Exception as e:
                logger.error(f"Error adding discovered device: {e}")

        # Save updated devices
        self._save_devices()

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
            ValueError: If required fields are missing
        """
        if not name or not name.strip() or not ip or not ip.strip():
            raise ValueError("Name and IP address are required")
        if not isinstance(name, str) or not isinstance(ip, str):
            raise ValueError("Name and IP address must be strings")
        if port:
            if not isinstance(port, int):
                raise ValueError("Port must be an integer")
            if port < 1 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")
        if type and type not in ["video", "audio"]:
            raise ValueError("Type must be 'video' or 'audio'")
        if protocol and protocol not in ["rtsp", "rtmp", "http"]:
            raise ValueError("Protocol must be 'rtsp', 'rtmp', or 'http'")

        # Validate IP address format
        import re

        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if not re.match(ip_pattern, ip):
            raise ValueError("Invalid IP address format")

        # Validate each octet is between 0 and 255
        octets = ip.split(".")
        for octet in octets:
            value = int(octet)
            if value < 0 or value > 255:
                raise ValueError("Invalid IP address: octets must be between 0 and 255")

        port = port or 554
        device_id = f"{ip}:{port}"
        device = NetworkDevice(
            device_id=device_id,
            name=name,
            ip=ip,
            port=port,
            type=type or "video",
            protocol=protocol or "rtsp",
            username=username or "",
            password=password or "",
        )

        # Add paths to streams
        if paths:
            for path in paths:
                stream_id = f"{device_id}_{path}"
                device.streams[stream_id] = path
        if device_id in self.devices:
            raise ValueError(f"Device {device_id} already exists")

        self.devices[device_id] = device
        self._save_devices()
        return device_id

    def remove_device(self, device_id: str) -> bool:
        """
        Remove a device.

        Args:
            device_id (str): Device identifier

        Returns:
            bool: True if device was removed

        Raises:
            ValueError: If device not found
        """
        if device_id not in self.devices:
            raise ValueError(f"Device {device_id} not found")

        del self.devices[device_id]
        self._save_devices()
        return True

    def update_device(self, device_id: str, **kwargs) -> bool:
        """
        Update device properties.

        Args:
            device_id (str): Device identifier
            **kwargs: Device properties to update

        Returns:
            bool: True if device was updated, False otherwise

        Raises:
            ValueError: If device not found
        """
        if device_id not in self.devices:
            raise ValueError(f"Device {device_id} not found")

        device = self.devices[device_id]
        for key, value in kwargs.items():
            if hasattr(device, key):
                setattr(device, key, value)

        self._save_devices()
        return True

    def get_devices(self) -> Dict[str, NetworkDevice]:
        """
        Get all devices.

        Returns:
            Dict[str, NetworkDevice]: Dictionary of devices
        """
        return self.devices

    def _discover_devices(self):
        """
        Discover network devices using configured methods.

        Returns:
            List[dict]: List of discovered devices.
        """
        discovered_devices = self.device_monitor.discover_devices()
        new_devices = self.device_monitor.process_discovered_devices(
            discovered_devices, self.devices
        )

        # Add new devices
        for device_info in new_devices:
            try:
                self.add_device(
                    name=device_info.get("name", f"Device {device_info['ip']}"),
                    ip=device_info["ip"],
                    port=device_info["port"],
                    type=device_info.get("type", "video"),
                    protocol=device_info.get("protocol", "rtsp"),
                    username=device_info.get("username", ""),
                    password=device_info.get("password", ""),
                    paths=device_info.get("paths", []),
                )
            except Exception as e:
                logger.error(f"Error adding discovered device: {e}")
                continue

        return new_devices

    def _handle_command(self, topic: str, payload: dict):
        """
        Handle MCP commands.

        Args:
            topic (str): Command topic
            payload (dict): Command payload
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
        except (ValueError, TypeError) as e:
            raise ValueError(str(e))

    def save_state(self, state_file: str):
        """
        Save devices state to a file.

        Args:
            state_file (str): Path to save state to.
        """
        self._save_devices()

    def load_state(self, state_file: str):
        """
        Load devices state from a file.

        Args:
            state_file (str): Path to load state from.
        """
        self._load_saved_devices()

    def update_device_status(self, device_id: str, status: DeviceStatus):
        """
        Update a device's status.

        Args:
            device_id (str): Device identifier.
            status (DeviceStatus): New device status.

        Raises:
            ValueError: If status is invalid or device not found.
        """
        if not isinstance(status, DeviceStatus):
            raise ValueError("Status must be a DeviceStatus enum value")

        if device_id not in self.devices:
            raise ValueError(f"Device {device_id} not found")

        self.devices[device_id].status = status
        self.command_handler.set_devices(self.devices)
        self.command_handler._publish_devices_info()
        self._save_devices()
