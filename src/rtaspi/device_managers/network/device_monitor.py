"""
rtaspi - Real-Time Annotation and Stream Processing
Network device monitor
"""

import logging
import socket
import time
from typing import Dict, List, Optional

from ...device_managers.utils.device import NetworkDevice, DeviceStatus
from ...device_managers.utils.discovery import (
    ONVIFDiscovery,
    UPnPDiscovery,
    MDNSDiscovery,
)

logger = logging.getLogger("NetworkDeviceMonitor")


class NetworkDeviceMonitor:
    """Monitors network devices status and discovers new devices."""

    def __init__(self, config: dict):
        """
        Initialize the device monitor.

        Args:
            config (dict): Configuration dictionary.
        """
        network_devices_config = config.get("network_devices", {})
        self.discovery_enabled = network_devices_config.get("discovery_enabled", True)
        self.discovery_methods = network_devices_config.get(
            "discovery_methods", ["onvif", "upnp", "mdns"]
        )
        self.scan_interval = network_devices_config.get("scan_interval", 60)

        # Initialize discovery modules
        self.discovery_modules = {
            "onvif": ONVIFDiscovery(),
            "upnp": UPnPDiscovery(),
            "mdns": MDNSDiscovery(),
        }

    def check_device_status(self, device: NetworkDevice) -> DeviceStatus:
        """
        Check a network device's status.

        Args:
            device (NetworkDevice): Device to check.

        Returns:
            DeviceStatus: Current status of the device.
        """
        try:
            # Check if enough time has passed since last check
            current_time = time.time()
            if current_time - device.last_check < self.scan_interval / 2:
                return device.status

            device.last_check = current_time

            # Simple port availability test
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((device.ip, device.port))
            sock.close()

            if result != 0:
                return DeviceStatus.OFFLINE

            # Protocol-specific checks
            if device.protocol == "rtsp":
                # RTSP is hard to check without special libraries
                # Use simple socket test
                return DeviceStatus.ONLINE
            elif device.protocol == "http":
                # For HTTP we can use socket test
                return DeviceStatus.ONLINE
            elif device.protocol == "rtmp":
                # RTMP is hard to check, consider online if port is open
                return DeviceStatus.ONLINE
            else:
                # Default to online if port is open
                return DeviceStatus.ONLINE

        except Exception as e:
            logger.warning(f"Error checking device {device.name} status: {e}")
            return DeviceStatus.OFFLINE

    def discover_devices(self) -> List[dict]:
        """
        Discover network devices using configured methods.

        Returns:
            List[dict]: List of discovered device information.
        """
        discovered_devices = []

        if not self.discovery_enabled:
            return discovered_devices

        # Run discovery using each configured method
        for method in self.discovery_methods:
            if method in self.discovery_modules:
                try:
                    logger.info(f"Discovering devices using {method}...")
                    devices = self.discovery_modules[method].discover()
                    discovered_devices.extend(devices)

                except Exception as e:
                    logger.error(f"Error during {method} device discovery: {e}")
                    continue

        return discovered_devices

    def validate_device_info(self, device_info: dict) -> bool:
        """
        Validate discovered device information.

        Args:
            device_info (dict): Device information to validate.

        Returns:
            bool: True if device info is valid, False otherwise.
        """
        # Check required fields
        required_fields = ["ip", "port"]
        if not all(field in device_info for field in required_fields):
            return False

        # Validate IP address format
        try:
            socket.inet_aton(device_info["ip"])
        except socket.error:
            return False

        # Validate port range
        port = device_info.get("port")
        if not isinstance(port, int) or port < 1 or port > 65535:
            return False

        # Validate type if present
        device_type = device_info.get("type")
        if device_type and device_type not in ["video", "audio"]:
            return False

        # Validate protocol if present
        protocol = device_info.get("protocol")
        if protocol and protocol not in ["rtsp", "rtmp", "http"]:
            return False

        return True

    def get_discovery_modules(self) -> Dict:
        """
        Get the discovery modules.

        Returns:
            Dict: Dictionary of discovery modules
        """
        return self.discovery_modules

    def process_discovered_devices(
        self, discovered_devices: List[dict], existing_devices: Dict[str, NetworkDevice]
    ) -> List[dict]:
        """
        Process discovered devices and filter out existing ones.

        Args:
            discovered_devices (List[dict]): List of discovered device information.
            existing_devices (Dict[str, NetworkDevice]): Dictionary of existing devices.

        Returns:
            List[dict]: List of new device information.
        """
        new_devices = []

        for device_info in discovered_devices:
            try:
                # Validate device info
                if not self.validate_device_info(device_info):
                    continue

                # Check if device already exists
                ip = device_info["ip"]
                port = device_info["port"]
                device_exists = False

                for device in existing_devices.values():
                    if device.ip == ip and device.port == port:
                        device_exists = True
                        break

                if not device_exists:
                    new_devices.append(device_info)

            except Exception as e:
                logger.error(f"Error processing discovered device: {e}")
                continue

        return new_devices
