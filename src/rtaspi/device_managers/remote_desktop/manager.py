"""Remote desktop device manager implementation."""

import logging
import socket
import threading
import time
from typing import Dict, List, Optional, Type
from ipaddress import IPv4Network

from ..base import DeviceManager
from .base import RemoteDesktopDevice
from .rdp import RDPDevice
from .vnc import VNCDevice
from ...constants.devices import (
    DEVICE_TYPE_REMOTE_DESKTOP,
    DEVICE_SUBTYPE_RDP,
    DEVICE_SUBTYPE_VNC,
    DEVICE_PROTOCOL_RDP,
    DEVICE_PROTOCOL_VNC,
)

logger = logging.getLogger(__name__)


class RemoteDesktopManager(DeviceManager):
    """Manager for remote desktop devices."""

    def __init__(self):
        """Initialize remote desktop manager."""
        super().__init__()
        self._devices: Dict[str, RemoteDesktopDevice] = {}
        self._discovery_thread: Optional[threading.Thread] = None
        self._stop_discovery = threading.Event()

    def start_discovery(self, networks: Optional[List[str]] = None) -> None:
        """Start remote desktop device discovery.

        Args:
            networks: List of networks to scan (e.g., ["192.168.1.0/24"])
                     If None, scan local network
        """
        if self._discovery_thread and self._discovery_thread.is_alive():
            logger.warning("Discovery already running")
            return

        self._stop_discovery.clear()
        self._discovery_thread = threading.Thread(
            target=self._discover_devices, args=(networks,)
        )
        self._discovery_thread.daemon = True
        self._discovery_thread.start()
        logger.info("Started remote desktop discovery")

    def stop_discovery(self) -> None:
        """Stop remote desktop device discovery."""
        if self._discovery_thread:
            self._stop_discovery.set()
            self._discovery_thread.join()
            self._discovery_thread = None
            logger.info("Stopped remote desktop discovery")

    def _discover_devices(self, networks: Optional[List[str]]) -> None:
        """Discover remote desktop devices on network.

        Args:
            networks: List of networks to scan
        """
        if not networks:
            # Get local network
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                networks = [f"{'.'.join(ip.split('.')[:3])}.0/24"]
            except Exception as e:
                logger.error(f"Failed to get local network: {e}")
                return
            finally:
                s.close()

        while not self._stop_discovery.is_set():
            for network in networks:
                try:
                    self._scan_network(network)
                except Exception as e:
                    logger.error(f"Error scanning network {network}: {e}")
            time.sleep(30)  # Scan every 30 seconds

    def _scan_network(self, network: str) -> None:
        """Scan network for remote desktop devices.

        Args:
            network: Network to scan (e.g., "192.168.1.0/24")
        """
        try:
            net = IPv4Network(network)
            for ip in net.hosts():
                if self._stop_discovery.is_set():
                    return

                ip_str = str(ip)

                # Check RDP (port 3389)
                if self._check_port(ip_str, 3389):
                    device_id = f"rdp-{ip_str}"
                    if device_id not in self._devices:
                        config = {
                            "id": device_id,
                            "name": f"RDP Device ({ip_str})",
                            "type": DEVICE_TYPE_REMOTE_DESKTOP,
                            "subtype": DEVICE_SUBTYPE_RDP,
                            "protocol": DEVICE_PROTOCOL_RDP,
                            "host": ip_str,
                            "port": 3389,
                        }
                        self._devices[device_id] = RDPDevice(device_id, config)
                        logger.info(f"Found RDP device at {ip_str}")

                # Check VNC (port 5900)
                if self._check_port(ip_str, 5900):
                    device_id = f"vnc-{ip_str}"
                    if device_id not in self._devices:
                        config = {
                            "id": device_id,
                            "name": f"VNC Device ({ip_str})",
                            "type": DEVICE_TYPE_REMOTE_DESKTOP,
                            "subtype": DEVICE_SUBTYPE_VNC,
                            "protocol": DEVICE_PROTOCOL_VNC,
                            "host": ip_str,
                            "port": 5900,
                        }
                        self._devices[device_id] = VNCDevice(device_id, config)
                        logger.info(f"Found VNC device at {ip_str}")

        except Exception as e:
            logger.error(f"Error scanning network {network}: {e}")

    def _check_port(self, host: str, port: int) -> bool:
        """Check if port is open on host.

        Args:
            host: Host to check
            port: Port to check

        Returns:
            bool: True if port is open
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    def get_devices(self) -> List[RemoteDesktopDevice]:
        """Get list of discovered devices.

        Returns:
            List[RemoteDesktopDevice]: List of remote desktop devices
        """
        return list(self._devices.values())

    def get_device(self, device_id: str) -> Optional[RemoteDesktopDevice]:
        """Get device by ID.

        Args:
            device_id: Device ID

        Returns:
            Optional[RemoteDesktopDevice]: Device if found, None otherwise
        """
        return self._devices.get(device_id)

    def add_device(self, config: Dict[str, str]) -> Optional[RemoteDesktopDevice]:
        """Add device manually.

        Args:
            config: Device configuration

        Returns:
            Optional[RemoteDesktopDevice]: Created device if successful
        """
        try:
            device_id = config["id"]
            if device_id in self._devices:
                logger.warning(f"Device {device_id} already exists")
                return None

            device_type = config.get("subtype", "").lower()
            if device_type == DEVICE_SUBTYPE_RDP:
                device = RDPDevice(device_id, config)
            elif device_type == DEVICE_SUBTYPE_VNC:
                device = VNCDevice(device_id, config)
            else:
                logger.error(f"Unknown device type: {device_type}")
                return None

            self._devices[device_id] = device
            logger.info(f"Added {device_type} device {device_id}")
            return device

        except Exception as e:
            logger.error(f"Failed to add device: {e}")
            return None

    def remove_device(self, device_id: str) -> bool:
        """Remove device.

        Args:
            device_id: Device ID

        Returns:
            bool: True if device was removed
        """
        if device_id in self._devices:
            device = self._devices[device_id]
            if device.is_connected:
                device.disconnect()
            del self._devices[device_id]
            logger.info(f"Removed device {device_id}")
            return True
        return False

    def cleanup(self) -> None:
        """Clean up manager resources."""
        self.stop_discovery()
        for device in self._devices.values():
            if device.is_connected:
                device.disconnect()
        self._devices.clear()
