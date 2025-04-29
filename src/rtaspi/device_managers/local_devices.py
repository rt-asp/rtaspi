"""
rtaspi - Real-Time Annotation and Stream Processing
Local devices manager (cameras, microphones)
"""

import logging
import os
from typing import Dict

from ..device_managers.base import DeviceManager
from ..device_managers.utils.device import LocalDevice, DeviceStatus
from .scanners import get_platform_scanner
from .stream_manager import StreamManager
from .command_handler import LocalDevicesCommandHandler

logger = logging.getLogger("LocalDevices")


class LocalDevicesManager(DeviceManager):
    """Manages local video and audio devices."""

    def __init__(self, config, mcp_broker):
        """
        Initialize the local devices manager.

        Args:
            config (dict): Manager configuration.
            mcp_broker (MCPBroker): MCP broker instance.
        """
        super().__init__(config, mcp_broker)

        # Get configuration
        local_devices_config = config.get("local_devices", {})
        self.enable_video = local_devices_config.get("enable_video", True)
        self.enable_audio = local_devices_config.get("enable_audio", True)
        self.auto_start = local_devices_config.get("auto_start", False)
        self.scan_interval = local_devices_config.get("scan_interval", 60)  # seconds

        # Initialize components
        self.scanner = get_platform_scanner()
        self.stream_manager = StreamManager(config, self.storage_path)
        self.command_handler = LocalDevicesCommandHandler(
            self.mcp_client, self.stream_manager
        )

        # Device state
        self.devices = {
            "video": {},  # device_id -> LocalDevice
            "audio": {},  # device_id -> LocalDevice
        }

    async def initialize(self):
        """Initialize the manager."""
        # Scan devices
        self._scan_devices()

        # Auto-start streams if configured
        if self.auto_start:
            await self._auto_start_streams()

    def update_device_status(self, device_id: str, status: DeviceStatus):
        """
        Update a device's status.

        Args:
            device_id (str): Device identifier.
            status (DeviceStatus): New device status.

        Raises:
            ValueError: If status is invalid or device not found.
        """
        if not isinstance(status, DeviceStatus):
            raise ValueError("Status must be a DeviceStatus enum value")

        # Check both video and audio devices
        for devices in [self.devices["video"], self.devices["audio"]]:
            if device_id in devices:
                devices[device_id].status = status
                self.command_handler.set_devices(self.devices)
                self.command_handler._publish_devices_info()
                return

        raise ValueError(f"Device {device_id} not found")

    def _get_client_id(self) -> str:
        """
        Get the MCP client ID.

        Returns:
            str: Client identifier.
        """
        return "local_devices_manager"

    def _get_scan_interval(self) -> int:
        """
        Get the device scanning interval.

        Returns:
            int: Scan interval in seconds.
        """
        return self.scan_interval

    def _subscribe_to_events(self):
        """Subscribe to MCP events."""
        self.mcp_client.subscribe(
            "command/local_devices/#", self.command_handler.handle_command
        )

    def _scan_devices(self):
        """Scan for local devices."""
        # Scan video devices if enabled
        if self.enable_video:
            self.devices["video"] = self.scanner.scan_video_devices()

        # Scan audio devices if enabled
        if self.enable_audio:
            self.devices["audio"] = self.scanner.scan_audio_devices()

        # Update command handler with new device list
        self.command_handler.set_devices(self.devices)
        self.command_handler._publish_devices_info()

    async def _auto_start_streams(self):
        """Automatically start streams for detected devices."""
        try:
            # Auto-start video streams
            if self.enable_video:
                for device_id, device in self.devices["video"].items():
                    # Check if stream already exists
                    streams = self.stream_manager.get_streams()
                    device_has_stream = any(
                        stream_info["device_id"] == device_id
                        for stream_info in streams.values()
                    )

                    # Start RTSP stream if no stream exists
                    if not device_has_stream:
                        logger.info(
                            f"Auto-starting stream for video device {device_id}"
                        )
                        await self.stream_manager.start_stream(device, protocol="rtsp")

            # Auto-start audio streams
            if self.enable_audio:
                for device_id, device in self.devices["audio"].items():
                    # Check if stream already exists
                    streams = self.stream_manager.get_streams()
                    device_has_stream = any(
                        stream_info["device_id"] == device_id
                        for stream_info in streams.values()
                    )

                    # Start RTSP stream if no stream exists
                    if not device_has_stream:
                        logger.info(
                            f"Auto-starting stream for audio device {device_id}"
                        )
                        await self.stream_manager.start_stream(device, protocol="rtsp")

        except Exception as e:
            logger.error(f"Error auto-starting streams: {e}")
