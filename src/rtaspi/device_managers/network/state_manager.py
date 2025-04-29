"""
rtaspi - Real-Time Annotation and Stream Processing
Network device state manager
"""

import os
import json
import logging
from typing import Dict, List, Optional

from ...device_managers.utils.device import NetworkDevice

logger = logging.getLogger("NetworkStateManager")


class NetworkStateManager:
    """Manages state persistence for network devices."""

    def __init__(self, storage_path: str):
        """
        Initialize the state manager.

        Args:
            storage_path (str): Base path for storing device data.
        """
        self.devices_file = os.path.join(storage_path, "network_devices.json")

    def save_state(
        self, devices: Dict[str, NetworkDevice], state_file: Optional[str] = None
    ) -> bool:
        """
        Save the current state of devices to a file.

        Args:
            devices (Dict[str, NetworkDevice]): Dictionary of devices to save.
            state_file (str, optional): Path to save state to. If not provided,
                                      uses the default devices_file path.

        Returns:
            bool: True if save was successful, False otherwise.
        """
        try:
            file_path = state_file or self.devices_file
            devices_data = []

            for device_id, device in devices.items():
                if isinstance(device, NetworkDevice):
                    device_data = device.to_dict()
                    device_data["id"] = device_id  # Ensure ID is included
                    device_data["username"] = device.username
                    device_data["password"] = device.password
                    device_data["streams"] = device.streams
                    devices_data.append(device_data)

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Save to file
            with open(file_path, "w") as f:
                json.dump(devices_data, f, indent=2)

            logger.info(f"Saved {len(devices_data)} devices to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving devices state: {e}")
            return False

    def load_state(self, state_file: Optional[str] = None) -> Dict[str, NetworkDevice]:
        """
        Load devices state from a file.

        Args:
            state_file (str, optional): Path to load state from. If not provided,
                                      uses the default devices_file path.

        Returns:
            Dict[str, NetworkDevice]: Dictionary of loaded devices.
        """
        devices = {}
        try:
            file_path = state_file or self.devices_file
            if not os.path.exists(file_path):
                logger.warning(f"State file not found: {file_path}")
                return devices

            with open(file_path, "r") as f:
                devices_data = json.load(f)

            # Load devices
            for device_data in devices_data:
                try:
                    device_id = device_data.get("id")
                    if not device_id:
                        continue

                    # Create device object
                    device = NetworkDevice(
                        device_id=device_id,
                        name=device_data.get("name", "Unknown Device"),
                        type=device_data.get("type", "video"),
                        ip=device_data.get("ip", ""),
                        port=device_data.get("port", 80),
                        username=device_data.get("username", ""),
                        password=device_data.get("password", ""),
                        protocol=device_data.get("protocol", "rtsp"),
                    )

                    # Add stream paths
                    if "streams" in device_data:
                        device.streams = device_data["streams"]

                    # Add device to dictionary
                    devices[device_id] = device

                except Exception as e:
                    logger.error(f"Error loading device: {e}")
                    continue

            logger.info(f"Loaded {len(devices)} devices from {file_path}")
            return devices

        except Exception as e:
            logger.error(f"Error loading devices state: {e}")
            return devices
