"""
Network device monitor implementation.
"""

import logging
import socket
from typing import Dict, Any, List, Optional
from ..base.device import DeviceStatus
from .device import NetworkDevice

logger = logging.getLogger("rtaspi.devices.network.monitor")


class NetworkDeviceMonitor:
    """Monitors network devices and handles device discovery."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize network device monitor.

        Args:
            config (Dict[str, Any]): Monitor configuration.
        """
        self.config = config
        self.discovery_methods = config.get("network_devices", {}).get(
            "discovery_methods", ["onvif", "upnp", "mdns"]
        )

    def check_device_status(self, device: NetworkDevice) -> DeviceStatus:
        """
        Check device status.

        Args:
            device (NetworkDevice): Device to check.

        Returns:
            DeviceStatus: Current device status.
        """
        try:
            # Try to connect to device port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((device.ip, device.port))
            sock.close()

            if result == 0:
                return DeviceStatus.ONLINE
            return DeviceStatus.OFFLINE

        except Exception as e:
            logger.error(f"Error checking device {device.device_id} status: {e}")
            return DeviceStatus.UNKNOWN

    def discover_devices(self) -> List[Dict[str, Any]]:
        """
        Discover network devices using configured methods.

        Returns:
            List[Dict[str, Any]]: List of discovered devices.
        """
        discovered_devices = []

        for method in self.discovery_methods:
            try:
                if method == "onvif":
                    devices = self._discover_onvif_devices()
                elif method == "upnp":
                    devices = self._discover_upnp_devices()
                elif method == "mdns":
                    devices = self._discover_mdns_devices()
                else:
                    logger.warning(f"Unknown discovery method: {method}")
                    continue

                discovered_devices.extend(devices)
            except Exception as e:
                logger.error(f"Error during {method} discovery: {e}")

        return discovered_devices

    def process_discovered_devices(
        self, discovered: List[Dict[str, Any]], existing: Dict[str, NetworkDevice]
    ) -> List[Dict[str, Any]]:
        """
        Process discovered devices and filter out existing ones.

        Args:
            discovered (List[Dict[str, Any]]): List of discovered devices.
            existing (Dict[str, NetworkDevice]): Dictionary of existing devices.

        Returns:
            List[Dict[str, Any]]: List of new devices to add.
        """
        new_devices = []

        for device_info in discovered:
            device_id = f"{device_info['ip']}:{device_info.get('port', 554)}"
            if device_id not in existing:
                new_devices.append(device_info)

        return new_devices

    def _discover_onvif_devices(self) -> List[Dict[str, Any]]:
        """
        Discover ONVIF devices.

        Returns:
            List[Dict[str, Any]]: List of discovered ONVIF devices.
        """
        # TODO: Implement ONVIF discovery
        # Example implementation:
        # from onvif import ONVIFCamera
        # devices = []
        # # Scan network for ONVIF devices
        # # For each device found:
        # #   device_info = {
        # #       "name": device.name,
        # #       "ip": device.ip,
        # #       "port": device.port,
        # #       "type": "video",
        # #       "protocol": "rtsp",
        # #       "paths": device.stream_urls
        # #   }
        # #   devices.append(device_info)
        # return devices
        return []

    def _discover_upnp_devices(self) -> List[Dict[str, Any]]:
        """
        Discover UPnP devices.

        Returns:
            List[Dict[str, Any]]: List of discovered UPnP devices.
        """
        # TODO: Implement UPnP discovery
        # Example implementation:
        # import upnpy
        # devices = []
        # upnp = upnpy.UPnP()
        # # Discover UPnP devices
        # # For each device found:
        # #   if device.type in ["urn:schemas-upnp-org:device:MediaServer:1"]:
        # #       device_info = {
        # #           "name": device.friendly_name,
        # #           "ip": device.ip,
        # #           "port": device.port,
        # #           "type": "video",
        # #           "protocol": "rtsp"
        # #       }
        # #       devices.append(device_info)
        # return devices
        return []

    def _discover_mdns_devices(self) -> List[Dict[str, Any]]:
        """
        Discover mDNS devices.

        Returns:
            List[Dict[str, Any]]: List of discovered mDNS devices.
        """
        # TODO: Implement mDNS discovery
        # Example implementation:
        # from zeroconf import ServiceBrowser, Zeroconf
        # devices = []
        # # Browse for _rtsp._tcp.local. services
        # # For each service found:
        # #   device_info = {
        # #       "name": service.name,
        # #       "ip": service.ip,
        # #       "port": service.port,
        # #       "type": "video",
        # #       "protocol": "rtsp"
        # #   }
        # #   devices.append(device_info)
        # return devices
        return []

    def get_discovery_modules(self) -> List[str]:
        """
        Get list of available discovery modules.

        Returns:
            List[str]: List of discovery module names.
        """
        return ["onvif", "upnp", "mdns"]
