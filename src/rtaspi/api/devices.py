"""
Device management API facade.

This module provides a high-level interface for managing audio/video devices,
abstracting away the internal implementation details.
"""

from typing import Optional, Dict, List, Any, Union
import logging

from rtaspi.constants import DeviceType, ProtocolType
from rtaspi.schemas import DeviceConfig, DeviceStatus, DeviceAuth, DeviceConnection
from rtaspi.device_managers import LocalDeviceManager, NetworkDeviceManager


class DeviceAPI:
    """High-level API for device management."""

    def __init__(self):
        """Initialize the device API."""
        self.logger = logging.getLogger(__name__)
        self.local_manager = LocalDeviceManager()
        self.network_manager = NetworkDeviceManager()

    def list_devices(
        self,
        device_type: Optional[Union[DeviceType, str]] = None,
        include_status: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        """List all configured devices.

        Args:
            device_type: Optional filter by device type
            include_status: Whether to include device status information

        Returns:
            Dictionary mapping device names to their configurations
        """
        # Convert string type to enum if needed
        if isinstance(device_type, str):
            device_type = DeviceType[device_type]

        # Get devices from both managers
        devices = {}
        devices.update(self.local_manager.get_devices())
        devices.update(self.network_manager.get_devices())

        # Apply type filter if specified
        if device_type:
            devices = {
                name: config
                for name, config in devices.items()
                if DeviceType[config["type"]] == device_type
            }

        # Add status information if requested
        if include_status:
            for name, config in devices.items():
                if config.get("type") in DeviceType.local_devices():
                    status = self.local_manager.get_device_status(name)
                else:
                    status = self.network_manager.get_device_status(name)
                config["status"] = status.dict()

        return devices

    def get_device(self, name: str) -> Optional[Dict[str, Any]]:
        """Get device configuration by name.

        Args:
            name: Device name

        Returns:
            Device configuration if found, None otherwise
        """
        # Try local devices first
        device = self.local_manager.get_device(name)
        if device:
            return device

        # Try network devices
        device = self.network_manager.get_device(name)
        return device

    def add_device(
        self,
        name: str,
        type: Union[DeviceType, str],
        enabled: bool = True,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a new device.

        Args:
            name: Unique device name
            type: Device type
            enabled: Whether the device is enabled
            host: Hostname/IP for network devices
            port: Port number for network devices
            username: Username for device authentication
            password: Password for device authentication
            settings: Additional device-specific settings
        """
        # Convert string type to enum if needed
        if isinstance(type, str):
            type = DeviceType[type]

        # Create device config
        config = {
            "name": name,
            "type": type.name,
            "enabled": enabled,
        }

        # Add connection details for network devices
        if type.is_network_device():
            if not host:
                raise ValueError("Host is required for network devices")

            connection = {
                "host": host,
                "port": port,
            }

            if username or password:
                connection["auth"] = {
                    "protocol": ProtocolType.BASIC_AUTH.name,
                    "username": username,
                    "password": password,
                }

            config["connection"] = connection

        # Add additional settings
        if settings:
            config["settings"] = settings

        # Validate config
        device_config = DeviceConfig(**config)

        # Add to appropriate manager
        if type.is_network_device():
            self.network_manager.add_device(name, device_config)
        else:
            self.local_manager.add_device(name, device_config)

    def remove_device(self, name: str) -> None:
        """Remove a device.

        Args:
            name: Device name
        """
        # Try local devices first
        if self.local_manager.has_device(name):
            self.local_manager.remove_device(name)
            return

        # Try network devices
        if self.network_manager.has_device(name):
            self.network_manager.remove_device(name)
            return

        raise ValueError(f"Device not found: {name}")

    def update_device(
        self,
        name: str,
        enabled: Optional[bool] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Update device configuration.

        Args:
            name: Device name
            enabled: Whether the device is enabled
            settings: Device-specific settings to update
        """
        # Get existing device
        device = self.get_device(name)
        if not device:
            raise ValueError(f"Device not found: {name}")

        # Update configuration
        if enabled is not None:
            device["enabled"] = enabled
        if settings:
            device["settings"] = {**device.get("settings", {}), **settings}

        # Validate updated config
        device_config = DeviceConfig(**device)

        # Update in appropriate manager
        if DeviceType[device["type"]].is_network_device():
            self.network_manager.update_device(name, device_config)
        else:
            self.local_manager.update_device(name, device_config)

    def get_device_status(self, name: str) -> DeviceStatus:
        """Get device status.

        Args:
            name: Device name

        Returns:
            Current device status
        """
        # Try local devices first
        if self.local_manager.has_device(name):
            return self.local_manager.get_device_status(name)

        # Try network devices
        if self.network_manager.has_device(name):
            return self.network_manager.get_device_status(name)

        raise ValueError(f"Device not found: {name}")

    def scan_device_capabilities(self, name: str) -> Dict[str, Any]:
        """Scan device capabilities.

        Args:
            name: Device name

        Returns:
            Dictionary of device capabilities
        """
        # Try local devices first
        if self.local_manager.has_device(name):
            return self.local_manager.scan_capabilities(name)

        # Try network devices
        if self.network_manager.has_device(name):
            return self.network_manager.scan_capabilities(name)

        raise ValueError(f"Device not found: {name}")

    def discover_devices(
        self, device_type: Optional[Union[DeviceType, str]] = None, timeout: float = 5.0
    ) -> List[Dict[str, Any]]:
        """Discover available devices.

        Args:
            device_type: Optional filter by device type
            timeout: Discovery timeout in seconds

        Returns:
            List of discovered device configurations
        """
        # Convert string type to enum if needed
        if isinstance(device_type, str):
            device_type = DeviceType[device_type]

        discovered = []

        # Discover local devices
        if not device_type or device_type.is_local_device():
            discovered.extend(self.local_manager.discover_devices(timeout))

        # Discover network devices
        if not device_type or device_type.is_network_device():
            discovered.extend(self.network_manager.discover_devices(timeout))

        # Apply type filter if specified
        if device_type:
            discovered = [
                device
                for device in discovered
                if DeviceType[device["type"]] == device_type
            ]

        return discovered
