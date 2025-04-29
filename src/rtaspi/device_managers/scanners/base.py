"""
rtaspi - Real-Time Annotation and Stream Processing
Base device scanner class
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from ...device_managers.utils.device import LocalDevice


class DeviceScanner(ABC):
    """Base class for platform-specific device scanners."""

    @abstractmethod
    def scan_video_devices(self) -> Dict[str, LocalDevice]:
        """
        Scans for video devices on the system.

        Returns:
            Dict[str, LocalDevice]: Dictionary mapping device IDs to LocalDevice objects.
        """
        pass

    @abstractmethod
    def scan_audio_devices(self) -> Dict[str, LocalDevice]:
        """
        Scans for audio devices on the system.

        Returns:
            Dict[str, LocalDevice]: Dictionary mapping device IDs to LocalDevice objects.
        """
        pass

    def scan_all_devices(self) -> Dict[str, Dict[str, LocalDevice]]:
        """
        Scans for all devices on the system.

        Returns:
            Dict[str, Dict[str, LocalDevice]]: Dictionary with 'video' and 'audio' keys,
            each mapping to a dictionary of device IDs to LocalDevice objects.
        """
        return {"video": self.scan_video_devices(), "audio": self.scan_audio_devices()}
