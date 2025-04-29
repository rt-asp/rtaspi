"""
Device managers package initialization.
"""

from .base import DeviceManager
from .local_devices import LocalDevicesManager
from .network_devices import NetworkDevicesManager
from .utils.discovery import ONVIFDiscovery, UPnPDiscovery, MDNSDiscovery
from .remote_desktop import RDPDevice, VNCDevice, RemoteDesktopDevice
from .remote_desktop.manager import RemoteDesktopManager

__all__ = [
    "DeviceManager",
    "LocalDevicesManager",
    "NetworkDevicesManager",
    "ONVIFDiscovery",
    "UPnPDiscovery",
    "MDNSDiscovery",
    "RDPDevice",
    "VNCDevice",
    "RemoteDesktopDevice",
    "RemoteDesktopManager",
]
