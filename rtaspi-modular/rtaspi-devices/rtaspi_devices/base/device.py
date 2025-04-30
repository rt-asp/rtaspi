"""
Base device classes for audio/video devices.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
import logging
from typing import Dict, Any

logger = logging.getLogger("rtaspi.devices")


class DeviceStatus(Enum):
    """Device status enumeration."""
    UNKNOWN = auto()
    ONLINE = auto()
    OFFLINE = auto()


class Device(ABC):
    """Base class for all devices."""

    def __init__(self, device_id: str, name: str, type: str):
        """
        Initialize a device.

        Args:
            device_id (str): Unique device identifier.
            name (str): Friendly device name.
            type (str): Device type ('video' or 'audio').
        """
        self.device_id = device_id
        self.name = name
        self.type = type
        self.status = DeviceStatus.UNKNOWN
        self.last_check = 0  # timestamp of last check

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert object to dictionary for serialization.

        Returns:
            Dict[str, Any]: Device representation as dictionary.
        """
        return {
            "id": self.device_id,
            "name": self.name,
            "type": self.type,
            "status": self.status.name.lower(),
        }


class LocalDevice(Device):
    """Class representing a local device (camera, microphone)."""

    def __init__(self, device_id: str, name: str, type: str, system_path: str, driver: str = "default"):
        """
        Initialize a local device.

        Args:
            device_id (str): Unique device identifier.
            name (str): Friendly device name.
            type (str): Device type ('video' or 'audio').
            system_path (str): System path to the device.
            driver (str): Device driver name.
        """
        super().__init__(device_id, name, type)
        self.system_path = system_path
        self.driver = driver
        self.formats = []
        self.resolutions = []

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert object to dictionary for serialization.

        Returns:
            Dict[str, Any]: Device representation as dictionary.
        """
        result = super().to_dict()
        result.update({
            "system_path": self.system_path,
            "driver": self.driver,
            "formats": self.formats,
            "resolutions": self.resolutions,
        })
        return result


class NetworkDevice(Device):
    """Class representing a network device (IP camera, IP microphone)."""

    def __init__(
        self, 
        device_id: str, 
        name: str, 
        type: str, 
        ip: str, 
        port: int, 
        username: str = "", 
        password: str = "", 
        protocol: str = "rtsp"
    ):
        """
        Initialize a network device.

        Args:
            device_id (str): Unique device identifier.
            name (str): Friendly device name.
            type (str): Device type ('video' or 'audio').
            ip (str): Device IP address.
            port (int): Device port.
            username (str): Authentication username.
            password (str): Authentication password.
            protocol (str): Protocol ('rtsp', 'rtmp', 'http', etc.).
        """
        super().__init__(device_id, name, type)
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.protocol = protocol
        self.streams = {}  # stream_id -> url

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert object to dictionary for serialization.

        Returns:
            Dict[str, Any]: Device representation as dictionary.
        """
        result = super().to_dict()
        result.update({
            "ip": self.ip,
            "port": self.port,
            "protocol": self.protocol,
            "streams": self.streams,
        })
        # Don't return sensitive data (username, password)
        return result

    def get_base_url(self) -> str:
        """
        Get the base URL for the device.

        Returns:
            str: Base device URL.
        """
        auth = ""
        if self.username:
            if self.password:
                auth = f"{self.username}:{self.password}@"
            else:
                auth = f"{self.username}@"

        return f"{self.protocol}://{auth}{self.ip}:{self.port}"
