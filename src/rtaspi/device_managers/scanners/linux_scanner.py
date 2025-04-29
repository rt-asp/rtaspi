"""
rtaspi - Real-Time Annotation and Stream Processing
Linux device scanner implementation
"""

import logging
import re
import subprocess
from pathlib import Path
from typing import Dict

from ...device_managers.utils.device import LocalDevice, DeviceStatus
from .base import DeviceScanner

logger = logging.getLogger("LinuxDeviceScanner")


class LinuxDeviceScanner(DeviceScanner):
    """Scanner for Linux video and audio devices."""

    def scan_video_devices(self) -> Dict[str, LocalDevice]:
        """
        Scans for video devices in Linux using v4l2.

        Returns:
            Dict[str, LocalDevice]: Dictionary mapping device IDs to LocalDevice objects.
        """
        try:
            video_devices = {}
            dev_video_paths = sorted(Path("/dev").glob("video*"))

            for path in dev_video_paths:
                system_path = str(path)
                device_id = f"video:{system_path}"

                # Add device to list with placeholder to ensure it's added even if parsing fails
                video_devices[device_id] = None

                try:
                    # Get device information using v4l2-ctl
                    output = subprocess.check_output(
                        ["v4l2-ctl", "--device", system_path, "--all"],
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                    )

                    # Parse device name
                    name_match = re.search(r"Card type\s+:\s+(.+)", output)
                    name = (
                        name_match.group(1).strip()
                        if name_match
                        else f"Kamera {system_path}"
                    )

                    # Get supported formats
                    formats_output = subprocess.check_output(
                        ["v4l2-ctl", "--device", system_path, "--list-formats-ext"],
                        stderr=subprocess.STDOUT,
                        universal_newlines=True,
                    )
                    formats = []
                    resolutions = []

                    # Parse formats and resolutions
                    for format_match in re.finditer(
                        r"PixelFormat\s+:\s+\'(\w+)\'", formats_output
                    ):
                        formats.append(format_match.group(1))

                    for res_match in re.finditer(
                        r"Size: Discrete (\d+)x(\d+)", formats_output
                    ):
                        resolutions.append(f"{res_match.group(1)}x{res_match.group(2)}")

                    # Create device object
                    device = LocalDevice(
                        device_id=device_id,
                        name=name,
                        type="video",
                        system_path=system_path,
                        driver="v4l2",
                    )
                    device.capabilities = {
                        "formats": formats,
                        "resolutions": resolutions,
                    }
                    device.status = DeviceStatus.ONLINE

                    video_devices[device_id] = device

                except subprocess.CalledProcessError as e:
                    logger.warning(f"Error checking device {system_path}: {e}")
                    continue

            return video_devices

        except Exception as e:
            logger.error(f"Error scanning Linux video devices: {e}")
            return {}

    def scan_audio_devices(self) -> Dict[str, LocalDevice]:
        """
        Scans for audio devices in Linux using ALSA and PulseAudio.

        Returns:
            Dict[str, LocalDevice]: Dictionary mapping device IDs to LocalDevice objects.
        """
        try:
            audio_devices = {}

            # Scan ALSA devices
            try:
                output = subprocess.check_output(
                    ["arecord", "-l"], stderr=subprocess.STDOUT, universal_newlines=True
                )

                for line in output.splitlines():
                    if not line.startswith("card "):
                        continue

                    match = re.match(r"card (\d+): (.+?), device (\d+): (.+)", line)
                    if match:
                        card_id = match.group(1)
                        card_name = (
                            match.group(2).split("[")[1].split("]")[0]
                            if "[" in match.group(2)
                            else match.group(2)
                        )
                        device_num = match.group(3)

                        alsa_id = f"hw:{card_id},{device_num}"
                        device_id = f"alsa:{alsa_id}"

                        device = LocalDevice(
                            device_id=device_id,
                            name=card_name,
                            type="audio",
                            system_path=alsa_id,
                            driver="alsa",
                        )
                        device.status = DeviceStatus.ONLINE

                        audio_devices[device_id] = device

            except subprocess.CalledProcessError as e:
                logger.warning(f"Error scanning ALSA devices: {e}")

            # Scan PulseAudio devices
            try:
                output = subprocess.check_output(
                    ["pactl", "list", "sources"],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                )

                current_device = {}
                for line in output.splitlines():
                    line = line.strip()

                    if line.startswith("Source #"):
                        # Process previous device if exists
                        if current_device and "name" in current_device:
                            device_id = f"pulse:{current_device['name']}"

                            device = LocalDevice(
                                device_id=device_id,
                                name=current_device.get(
                                    "description", current_device["name"]
                                ),
                                type="audio",
                                system_path=current_device["name"],
                                driver="pulse",
                            )
                            device.status = DeviceStatus.ONLINE

                            audio_devices[device_id] = device

                        # Reset for new device
                        current_device = {}
                    elif ":" in line:
                        key, value = line.split(":", 1)
                        key = key.strip().lower()
                        value = value.strip()

                        if key == "name" or key == "description":
                            current_device[key] = value

                # Process last device
                if current_device and "name" in current_device:
                    device_id = f"pulse:{current_device['name']}"

                    device = LocalDevice(
                        device_id=device_id,
                        name=current_device.get("description", current_device["name"]),
                        type="audio",
                        system_path=current_device["name"],
                        driver="pulse",
                    )
                    device.status = DeviceStatus.ONLINE

                    audio_devices[device_id] = device

            except subprocess.CalledProcessError as e:
                logger.warning(f"Error scanning PulseAudio devices: {e}")

            return audio_devices

        except Exception as e:
            logger.error(f"Error scanning Linux audio devices: {e}")
            return {}
