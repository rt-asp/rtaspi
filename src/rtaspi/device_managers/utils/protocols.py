"""
protocols.py
"""

from enum import Enum, auto


class ProtocolType(Enum):
    """Type of protocol."""

    RTSP = auto()
    RTMP = auto()
    HTTP = auto()
    HTTPS = auto()
    ONVIF = auto()
    UPNP = auto()
    MDNS = auto()


class Protocol:
    """Base class for protocol implementations."""

    def __init__(self, protocol_type: ProtocolType, port: int = None):
        self.type = protocol_type
        self.port = port or self._get_default_port()

    def _get_default_port(self) -> int:
        """Get the default port for the protocol type."""
        default_ports = {
            ProtocolType.RTSP: 554,
            ProtocolType.RTMP: 1935,
            ProtocolType.HTTP: 80,
            ProtocolType.HTTPS: 443,
            ProtocolType.ONVIF: 80,
            ProtocolType.UPNP: 1900,
            ProtocolType.MDNS: 5353,
        }
        return default_ports.get(self.type)

    def get_url_prefix(self) -> str:
        """Get the URL prefix for the protocol."""
        return self.type.name.lower()
