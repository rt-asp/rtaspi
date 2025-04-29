"""
Constants and enumerations for device types supported by the system.
"""

from enum import Enum, auto


class DeviceType(Enum):
    """Enumeration of supported device types."""

    # Local Devices
    USB_CAMERA = auto()
    BUILT_IN_CAMERA = auto()
    CSI_CAMERA = auto()  # Raspberry Pi Camera Module, etc.
    USB_MICROPHONE = auto()
    BUILT_IN_MICROPHONE = auto()

    # Network Devices
    IP_CAMERA = auto()
    ONVIF_CAMERA = auto()
    RTSP_CAMERA = auto()
    NETWORK_MICROPHONE = auto()
    VOIP_DEVICE = auto()

    # Virtual/Special Devices
    VIRTUAL_CAMERA = auto()  # For testing/simulation
    VIRTUAL_MICROPHONE = auto()
    SCREEN_CAPTURE = auto()
    AUDIO_LOOPBACK = auto()

    @classmethod
    def local_devices(cls) -> list["DeviceType"]:
        """Return a list of local device types."""
        return [
            cls.USB_CAMERA,
            cls.BUILT_IN_CAMERA,
            cls.CSI_CAMERA,
            cls.USB_MICROPHONE,
            cls.BUILT_IN_MICROPHONE,
        ]

    @classmethod
    def network_devices(cls) -> list["DeviceType"]:
        """Return a list of network device types."""
        return [
            cls.IP_CAMERA,
            cls.ONVIF_CAMERA,
            cls.RTSP_CAMERA,
            cls.NETWORK_MICROPHONE,
            cls.VOIP_DEVICE,
        ]

    @classmethod
    def virtual_devices(cls) -> list["DeviceType"]:
        """Return a list of virtual/special device types."""
        return [
            cls.VIRTUAL_CAMERA,
            cls.VIRTUAL_MICROPHONE,
            cls.SCREEN_CAPTURE,
            cls.AUDIO_LOOPBACK,
        ]

    @classmethod
    def video_devices(cls) -> list["DeviceType"]:
        """Return a list of video capture devices."""
        return [
            cls.USB_CAMERA,
            cls.BUILT_IN_CAMERA,
            cls.CSI_CAMERA,
            cls.IP_CAMERA,
            cls.ONVIF_CAMERA,
            cls.RTSP_CAMERA,
            cls.VIRTUAL_CAMERA,
            cls.SCREEN_CAPTURE,
        ]

    @classmethod
    def audio_devices(cls) -> list["DeviceType"]:
        """Return a list of audio capture devices."""
        return [
            cls.USB_MICROPHONE,
            cls.BUILT_IN_MICROPHONE,
            cls.NETWORK_MICROPHONE,
            cls.VOIP_DEVICE,
            cls.VIRTUAL_MICROPHONE,
            cls.AUDIO_LOOPBACK,
        ]

    def is_local_device(self) -> bool:
        """Check if this is a local device type."""
        return self in self.local_devices()

    def is_network_device(self) -> bool:
        """Check if this is a network device type."""
        return self in self.network_devices()

    def is_virtual_device(self) -> bool:
        """Check if this is a virtual/special device type."""
        return self in self.virtual_devices()

    def is_video_device(self) -> bool:
        """Check if this is a video capture device type."""
        return self in self.video_devices()

    def is_audio_device(self) -> bool:
        """Check if this is an audio capture device type."""
        return self in self.audio_devices()
