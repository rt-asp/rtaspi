"""
Base device scanner implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, List

from ..base import LocalDevice


class DeviceScanner(ABC):
    """Base class for platform-specific device scanners."""

    @abstractmethod
    def scan_video_devices(self) -> Dict[str, LocalDevice]:
        """
        Scan for video devices on the system.

        Returns:
            Dict[str, LocalDevice]: Dictionary mapping device IDs to LocalDevice objects.
        """
        pass

    @abstractmethod
    def scan_audio_devices(self) -> Dict[str, LocalDevice]:
        """
        Scan for audio devices on the system.

        Returns:
            Dict[str, LocalDevice]: Dictionary mapping device IDs to LocalDevice objects.
        """
        pass

    def scan_all_devices(self) -> Dict[str, Dict[str, LocalDevice]]:
        """
        Scan for all devices on the system.

        Returns:
            Dict[str, Dict[str, LocalDevice]]: Dictionary with 'video' and 'audio' keys,
            each mapping to a dictionary of device IDs to LocalDevice objects.
        """
        return {
            "video": self.scan_video_devices(),
            "audio": self.scan_audio_devices()
        }
