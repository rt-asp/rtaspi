"""
rtaspi - Real-Time Annotation and Stream Processing
macOS device scanner implementation
"""

import logging
import re
import subprocess
from typing import Dict

from ...device_managers.utils.device import LocalDevice, DeviceStatus
from .base import DeviceScanner

logger = logging.getLogger("MacOSDeviceScanner")


class MacOSDeviceScanner(DeviceScanner):
    """Scanner for macOS video and audio devices using AVFoundation."""

    def scan_video_devices(self) -> Dict[str, LocalDevice]:
        """
        Scans for video devices in macOS using AVFoundation.

        Returns:
            Dict[str, LocalDevice]: Dictionary mapping device IDs to LocalDevice objects.
        """
        try:
            video_devices = {}

            # Use ffmpeg to detect cameras in macOS
            output = subprocess.check_output(
                ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )

            capture_next = False
            for line in output.splitlines():
                if "AVFoundation video devices:" in line:
                    capture_next = True
                    continue
                elif "AVFoundation audio devices:" in line:
                    break

                if capture_next and "]" in line:
                    match = re.search(r"\[(\d+)\]\s+(.+)", line)
                    if match:
                        index = match.group(1)
                        name = match.group(2).strip()
                        device_id = f"avfoundation:video:{index}"

                        # Create device object
                        device = LocalDevice(
                            device_id=device_id,
                            name=name,
                            type="video",
                            system_path=index,
                            driver="avfoundation",
                        )
                        device.status = DeviceStatus.ONLINE

                        # Add device to list
                        video_devices[device_id] = device

            return video_devices

        except Exception as e:
            logger.error(f"Error scanning macOS video devices: {e}")
            return {}

    def scan_audio_devices(self) -> Dict[str, LocalDevice]:
        """
        Scans for audio devices in macOS using AVFoundation.

        Returns:
            Dict[str, LocalDevice]: Dictionary mapping device IDs to LocalDevice objects.
        """
        try:
            audio_devices = {}

            # Use ffmpeg to detect microphones in macOS
            output = subprocess.check_output(
                ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )

            capture_next = False
            for line in output.splitlines():
                if "AVFoundation audio devices:" in line:
                    capture_next = True
                    continue

                if capture_next and "]" in line:
                    match = re.search(r"\[(\d+)\]\s+(.+)", line)
                    if match:
                        index = match.group(1)
                        name = match.group(2).strip()
                        device_id = f"avfoundation:audio:{index}"

                        # Create device object
                        device = LocalDevice(
                            device_id=device_id,
                            name=name,
                            type="audio",
                            system_path=index,
                            driver="avfoundation",
                        )
                        device.status = DeviceStatus.ONLINE

                        # Add device to list
                        audio_devices[device_id] = device

            return audio_devices

        except Exception as e:
            logger.error(f"Error scanning macOS audio devices: {e}")
            return {}
