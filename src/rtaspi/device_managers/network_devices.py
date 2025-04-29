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
                self.command_handler.add_device(
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
