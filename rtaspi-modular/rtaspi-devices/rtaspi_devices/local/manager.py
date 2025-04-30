"""
Local device manager implementation.
"""

import logging
from typing import Dict, Any

from ..base import DeviceManager, LocalDevice, DeviceStatus
from ..discovery import DeviceScanner
from ..protocols import StreamingProtocol

logger = logging.getLogger("rtaspi.devices.local")


class LocalDeviceManager(DeviceManager):
    """Manages local video and audio devices."""

    def __init__(self, config: Dict[str, Any], mcp_broker: Any):
        """
        Initialize the local device manager.

        Args:
            config (Dict[str, Any]): Manager configuration.
            mcp_broker (Any): MCP broker instance.
        """
        super().__init__(config, mcp_broker)

        # Get configuration
        local_devices_config = config.get("local_devices", {})
        self.enable_video = local_devices_config.get("enable_video", True)
        self.enable_audio = local_devices_config.get("enable_audio", True)
        self.auto_start = local_devices_config.get("auto_start", False)
        self.scan_interval = local_devices_config.get("scan_interval", 60)  # seconds

        # Initialize components
        self.scanner = self._get_platform_scanner()

        # Device state
        self.devices = {
            "video": {},  # device_id -> LocalDevice
            "audio": {},  # device_id -> LocalDevice
        }

    def _get_client_id(self) -> str:
        """
        Get MCP client identifier.

        Returns:
            str: Client identifier.
        """
        return "local_devices_manager"

    def _get_scan_interval(self) -> int:
        """
        Get scanning interval in seconds.

        Returns:
            int: Scanning interval in seconds.
        """
        return self.scan_interval

    def _subscribe_to_events(self) -> None:
        """Subscribe to MCP events."""
        self.mcp_client.subscribe(
            "command/local_devices/#",
            self._handle_command
        )

    def _scan_devices(self) -> None:
        """Scan for local devices."""
        # Scan video devices if enabled
        if self.enable_video:
            self.devices["video"] = self.scanner.scan_video_devices()

        # Scan audio devices if enabled
        if self.enable_audio:
            self.devices["audio"] = self.scanner.scan_audio_devices()

        # Publish updated device information
        self._publish_devices_info()

    def _publish_devices_info(self) -> None:
        """Publish device information."""
        devices_info = {
            "video": {
                device_id: device.to_dict()
                for device_id, device in self.devices["video"].items()
            },
            "audio": {
                device_id: device.to_dict()
                for device_id, device in self.devices["audio"].items()
            }
        }
        self.mcp_client.publish("info/local_devices", devices_info)

    def _publish_stream_stopped(self, stream_id: str, stream_info: Dict[str, Any]) -> None:
        """
        Publish stream stop information.

        Args:
            stream_id (str): Stream identifier.
            stream_info (Dict[str, Any]): Stream information.
        """
        self.mcp_client.publish(
            "event/local_devices/stream_stopped",
            {
                "stream_id": stream_id,
                "device_id": stream_info.get("device_id"),
                "type": stream_info.get("type"),
            }
        )

    def _handle_command(self, topic: str, payload: Dict[str, Any]) -> None:
        """
        Handle MCP commands.

        Args:
            topic (str): Command topic.
            payload (Dict[str, Any]): Command payload.
        """
        try:
            command = topic.split("/")[-1]
            
            if command == "start_stream":
                device_id = payload.get("device_id")
                protocol = payload.get("protocol", "rtsp")
                self.start_stream(device_id, protocol=protocol)
                
            elif command == "stop_stream":
                stream_id = payload.get("stream_id")
                self.stop_stream(stream_id)
                
            elif command == "get_devices":
                self._publish_devices_info()
                
            elif command == "get_streams":
                streams_info = {
                    stream_id: info
                    for stream_id, info in self.get_streams().items()
                }
                self.mcp_client.publish("info/local_devices/streams", streams_info)
                
            else:
                logger.warning(f"Unknown command: {command}")

        except Exception as e:
            logger.error(f"Error handling command {topic}: {e}")

    def get_device(self, device_id: str) -> LocalDevice:
        """
        Get a device by ID.

        Args:
            device_id (str): Device identifier.

        Returns:
            LocalDevice: Device object if found.

        Raises:
            ValueError: If device not found.
        """
        # Check video devices
        if device_id in self.devices["video"]:
            return self.devices["video"][device_id]

        # Check audio devices
        if device_id in self.devices["audio"]:
            return self.devices["audio"][device_id]

        raise ValueError(f"Device {device_id} not found")

    def update_device_status(self, device_id: str, status: DeviceStatus) -> None:
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
                self._publish_devices_info()
                return

        raise ValueError(f"Device {device_id} not found")

    def _get_platform_scanner(self) -> DeviceScanner:
        """
        Get platform-specific device scanner.

        Returns:
            DeviceScanner: Platform-specific scanner instance.
        """
        # This will be implemented by platform-specific modules
        # For now, return a basic scanner that returns empty device lists
        return DeviceScanner()
