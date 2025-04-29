"""
rtaspi - Real-Time Annotation and Stream Processing
Windows device scanner implementation
"""

import logging
import re
import subprocess
from typing import Dict

from ...device_managers.utils.device import LocalDevice, DeviceStatus
from .base import DeviceScanner

logger = logging.getLogger("WindowsDeviceScanner")


class WindowsDeviceScanner(DeviceScanner):
    """Scanner for Windows video and audio devices using DirectShow."""

    def scan_video_devices(self) -> Dict[str, LocalDevice]:
        """
        Scans for video devices in Windows using DirectShow.

        Returns:
            Dict[str, LocalDevice]: Dictionary mapping device IDs to LocalDevice objects.
        """
        try:
            video_devices = {}

            # Use ffmpeg to detect cameras in Windows
            output = subprocess.check_output(
                ["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )

            capture_section = False
            for line in output.splitlines():
                if "DirectShow video devices" in line:
                    capture_section = True
                    continue
                elif "DirectShow audio devices" in line:
                    break

                if capture_section and "Alternative name" in line:
                    match = re.search(r'"(.+)"', line)
                    if match:
                        name = match.group(1)
                        device_id = f"dshow:video:{name}"

                        # Create device object
                        device = LocalDevice(
                            device_id=device_id,
                            name=name,
                            type="video",
                            system_path=name,
                            driver="dshow",
                        )
                        device.status = DeviceStatus.ONLINE

                        # Add device to list
                        video_devices[device_id] = device

            return video_devices

        except Exception as e:
            logger.error(f"Error scanning Windows video devices: {e}")
            return {}

    def scan_audio_devices(self) -> Dict[str, LocalDevice]:
        """
        Scans for audio devices in Windows using DirectShow.

        Returns:
            Dict[str, LocalDevice]: Dictionary mapping device IDs to LocalDevice objects.
        """
        try:
            audio_devices = {}

            # Use ffmpeg to detect microphones in Windows
            output = subprocess.check_output(
                ["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )

            capture_section = False
            for line in output.splitlines():
                if "DirectShow audio devices" in line:
                    capture_section = True
                    continue

                if capture_section and "Alternative name" in line:
                    match = re.search(r'"(.+)"', line)
                    if match:
                        name = match.group(1)
                        device_id = f"dshow:audio:{name}"

                        # Create device object
                        device = LocalDevice(
                            device_id=device_id,
                            name=name,
                            type="audio",
                            system_path=name,
                            driver="dshow",
                        )
                        device.status = DeviceStatus.ONLINE

                        # Add device to list
                        audio_devices[device_id] = device

            return audio_devices

        except Exception as e:
            logger.error(f"Error scanning Windows audio devices: {e}")
            return {}
