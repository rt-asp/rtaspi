"""
Constants and enumerations for communication protocols supported by the system.
"""

from enum import Enum, auto


class ProtocolType(Enum):
    """Enumeration of supported communication protocols."""

    # Streaming Protocols
    HTTP = auto()
    HTTPS = auto()
    RTSP = auto()
    RTMP = auto()
    RTMPS = auto()
    WEBRTC = auto()
    HLS = auto()
    MPEG_DASH = auto()
    SRT = auto()

    # Discovery Protocols
    ONVIF = auto()
    UPNP = auto()
    MDNS = auto()
    SSDP = auto()
    WS_DISCOVERY = auto()

    # Control/Management Protocols
    SSH = auto()
    TELNET = auto()
    FTP = auto()
    SFTP = auto()
    MQTT = auto()
    WEBSOCKET = auto()
    WEBSOCKET_SECURE = auto()

    # Authentication Protocols
    BASIC_AUTH = auto()
    DIGEST_AUTH = auto()
    OAUTH2 = auto()
    JWT = auto()

    @classmethod
    def streaming_protocols(cls) -> list["ProtocolType"]:
        """Return a list of streaming protocols."""
        return [
            cls.HTTP,
            cls.HTTPS,
            cls.RTSP,
            cls.RTMP,
            cls.RTMPS,
            cls.WEBRTC,
            cls.HLS,
            cls.MPEG_DASH,
            cls.SRT,
        ]

    @classmethod
    def discovery_protocols(cls) -> list["ProtocolType"]:
        """Return a list of device discovery protocols."""
        return [
            cls.ONVIF,
            cls.UPNP,
            cls.MDNS,
            cls.SSDP,
            cls.WS_DISCOVERY,
        ]

    @classmethod
    def control_protocols(cls) -> list["ProtocolType"]:
        """Return a list of device control and management protocols."""
        return [
            cls.SSH,
            cls.TELNET,
            cls.FTP,
            cls.SFTP,
            cls.MQTT,
            cls.WEBSOCKET,
            cls.WEBSOCKET_SECURE,
        ]

    @classmethod
    def auth_protocols(cls) -> list["ProtocolType"]:
        """Return a list of authentication protocols."""
        return [
            cls.BASIC_AUTH,
            cls.DIGEST_AUTH,
            cls.OAUTH2,
            cls.JWT,
        ]

    @classmethod
    def secure_protocols(cls) -> list["ProtocolType"]:
        """Return a list of secure protocols."""
        return [
            cls.HTTPS,
            cls.RTMPS,
            cls.WEBRTC,  # WebRTC is secure by default
            cls.SSH,
            cls.SFTP,
            cls.WEBSOCKET_SECURE,
            cls.OAUTH2,
            cls.JWT,
        ]

    def is_streaming_protocol(self) -> bool:
        """Check if this is a streaming protocol."""
        return self in self.streaming_protocols()

    def is_discovery_protocol(self) -> bool:
        """Check if this is a device discovery protocol."""
        return self in self.discovery_protocols()

    def is_control_protocol(self) -> bool:
        """Check if this is a control/management protocol."""
        return self in self.control_protocols()

    def is_auth_protocol(self) -> bool:
        """Check if this is an authentication protocol."""
        return self in self.auth_protocols()

    def is_secure(self) -> bool:
        """Check if this is a secure protocol."""
        return self in self.secure_protocols()

    def requires_authentication(self) -> bool:
        """Check if this protocol typically requires authentication."""
        return self in (
            self.auth_protocols() + [self.SSH, self.SFTP, self.FTP, self.TELNET]
        )
