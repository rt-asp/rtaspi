"""
Network device implementation.
"""

from typing import Dict, Any, Optional
from ..base.device import Device, DeviceStatus


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

        Raises:
            ValueError: If any parameters are invalid.
        """
        # Call parent constructor first to validate type
        super().__init__(device_id, name, type)

        # Validate protocol
        if protocol not in ["rtsp", "rtmp", "http"]:
            raise ValueError("Protocol must be 'rtsp', 'rtmp', or 'http'")

        # Validate port
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError("Port must be between 1 and 65535")

        # Validate IP address format
        import re
        ip_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"
        if not re.match(ip_pattern, ip):
            raise ValueError("Invalid IP address format")

        # Validate IP octets
        octets = ip.split(".")
        for octet in octets:
            value = int(octet)
            if value < 0 or value > 255:
                raise ValueError("Invalid IP address: octets must be between 0 and 255")

        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.protocol = protocol
        self.streams: Dict[str, str] = {}  # stream_id -> url

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

    def add_stream(self, stream_id: str, url: str) -> None:
        """
        Add a stream URL for this device.

        Args:
            stream_id (str): Stream identifier.
            url (str): Stream URL.
        """
        self.streams[stream_id] = url

    def remove_stream(self, stream_id: str) -> None:
        """
        Remove a stream URL for this device.

        Args:
            stream_id (str): Stream identifier.
        """
        self.streams.pop(stream_id, None)

    def get_stream_url(self, stream_id: str) -> Optional[str]:
        """
        Get URL for a specific stream.

        Args:
            stream_id (str): Stream identifier.

        Returns:
            Optional[str]: Stream URL if found, None otherwise.
        """
        return self.streams.get(stream_id)
