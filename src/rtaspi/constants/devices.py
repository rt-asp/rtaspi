"""Device type constants."""

from enum import auto
from ..core.enums import ConfigurableEnum

# String constants for backward compatibility with tests
DEVICE_TYPE_REMOTE_DESKTOP = "remote_desktop"
DEVICE_SUBTYPE_RDP = "rdp"
DEVICE_SUBTYPE_VNC = "vnc"
DEVICE_PROTOCOL_RDP = "rdp"
DEVICE_PROTOCOL_VNC = "vnc"
CAPABILITY_VIDEO = "video"
CAPABILITY_KEYBOARD = "keyboard"
CAPABILITY_MOUSE = "mouse"


class DeviceType(ConfigurableEnum):
    """Device type enumeration."""
    USB_CAMERA = auto()
    IP_CAMERA = auto()
    CSI_CAMERA = auto()
    BUILT_IN_CAMERA = auto()
    USB_MICROPHONE = auto()
    BUILT_IN_MICROPHONE = auto()
    SCREEN = auto()
    REMOTE_DESKTOP = auto()

    @property
    def is_camera(self) -> bool:
        """Check if device type is a camera."""
        return self in (
            DeviceType.USB_CAMERA,
            DeviceType.IP_CAMERA,
            DeviceType.CSI_CAMERA,
            DeviceType.BUILT_IN_CAMERA
        )

    @property
    def is_microphone(self) -> bool:
        """Check if device type is a microphone."""
        return self in (
            DeviceType.USB_MICROPHONE,
            DeviceType.BUILT_IN_MICROPHONE
        )

    @property
    def is_local_device(self) -> bool:
        """Check if device type is local."""
        return self in (
            DeviceType.USB_CAMERA,
            DeviceType.CSI_CAMERA,
            DeviceType.BUILT_IN_CAMERA,
            DeviceType.USB_MICROPHONE,
            DeviceType.BUILT_IN_MICROPHONE,
            DeviceType.SCREEN
        )

    @property
    def is_network_device(self) -> bool:
        """Check if device type is networked."""
        return self in (
            DeviceType.IP_CAMERA,
            DeviceType.REMOTE_DESKTOP
        )


class DeviceSubType(ConfigurableEnum):
    """Device subtype enumeration."""
    USB = "usb"
    IP = "ip"
    RDP = "rdp"
    VNC = "vnc"
    VIRTUAL = "virtual"
    PHYSICAL = "physical"
    NETWORK = "network"


class DeviceCapability(ConfigurableEnum):
    """Device capability enumeration."""
    VIDEO = "video"
    AUDIO = "audio"
    PTZ = "ptz"
    MOTION = "motion"
    REMOTE_CONTROL = "remote_control"
    KEYBOARD = "keyboard"
    MOUSE = "mouse"


class DeviceState(ConfigurableEnum):
    """Device state enumeration."""
    UNKNOWN = "unknown"
    OFFLINE = "offline"
    ONLINE = "online"
    STREAMING = "streaming"
    ERROR = "error"
    CONNECTING = "connecting"
    DISCONNECTING = "disconnecting"


class DeviceProtocol(ConfigurableEnum):
    """Device protocol enumeration."""
    RTSP = "rtsp"
    ONVIF = "onvif"
    RDP = "rdp"
    VNC = "vnc"
    WEBRTC = "webrtc"
    RTMP = "rtmp"
    HLS = "hls"
    DASH = "dash"


class DeviceCategory(ConfigurableEnum):
    """Device category enumeration."""
    INPUT = "input"
    OUTPUT = "output"
    REMOTE = "remote"
