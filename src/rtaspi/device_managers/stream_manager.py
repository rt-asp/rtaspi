"""
rtaspi - Real-Time Annotation and Stream Processing
Stream manager for handling device streams
"""

import logging
import os
import uuid
from typing import Dict, Optional

from ..streaming.rtsp import RTSPServer
from ..streaming.rtmp import RTMPServer
from ..streaming.webrtc import WebRTCServer
from .utils.device import LocalDevice

logger = logging.getLogger("StreamManager")


class StreamManager:
    """Manages streaming for local devices."""

    def __init__(self, config: dict, storage_path: str):
        """
        Initialize the stream manager.

        Args:
            config (dict): Configuration dictionary.
            storage_path (str): Base path for storing stream data.
        """
        # Get configuration
        local_devices_config = config.get("local_devices", {})
        self.rtsp_port_start = local_devices_config.get("rtsp_port_start", 8554)
        self.rtmp_port_start = local_devices_config.get("rtmp_port_start", 1935)
        self.webrtc_port_start = local_devices_config.get("webrtc_port_start", 8080)

        # Initialize streaming servers
        self.rtsp_server = RTSPServer(config)
        self.rtmp_server = RTMPServer(config)
        self.webrtc_server = WebRTCServer(config)

        # Stream storage
        self.storage_path = storage_path
        self.local_streams_path = os.path.join(storage_path, "local_streams")
        os.makedirs(self.local_streams_path, exist_ok=True)

        # Active streams
        self.streams: Dict[str, dict] = {}

    async def start_stream(
        self, device: LocalDevice, protocol: str = "rtsp"
    ) -> Optional[str]:
        """
        Start streaming from a device.

        Args:
            device (LocalDevice): The device to stream from.
            protocol (str): Streaming protocol ('rtsp', 'rtmp', or 'webrtc').

        Returns:
            Optional[str]: Stream URL if successful, None otherwise.

        Raises:
            ValueError: If protocol is not supported or device is invalid.
            RuntimeError: If stream cannot be started.
        """
        # Validate device
        if not device or not isinstance(device, LocalDevice):
            raise ValueError("Invalid device")

        # Validate protocol
        if protocol not in ["rtsp", "rtmp", "webrtc"]:
            raise ValueError(f"Unsupported protocol: {protocol}")

        # Check if device already has a stream
        for stream_info in self.streams.values():
            if stream_info["device_id"] == device.device_id:
                logger.info(f"Stream already exists for device {device.device_id}")
                return stream_info["url"]

        # Create stream ID and output directory
        stream_id = str(uuid.uuid4())
        output_dir = os.path.join(self.local_streams_path, stream_id)
        os.makedirs(output_dir, exist_ok=True)

        try:
            # Start stream with appropriate server
            if protocol == "rtsp":
                url = await self.rtsp_server.start_stream(device, stream_id, output_dir)
            elif protocol == "rtmp":
                url = await self.rtmp_server.start_stream(device, stream_id, output_dir)
            else:  # protocol == 'webrtc'
                url = await self.webrtc_server.start_stream(
                    device, stream_id, output_dir
                )

            if not url:
                raise RuntimeError(
                    f"Could not start {protocol} stream for device {device.device_id}"
                )

            logger.info(
                f"Started {protocol} stream for device {device.device_id}: {url}"
            )

            # Store stream info
            stream_info = {
                "stream_id": stream_id,
                "device_id": device.device_id,
                "type": device.type,
                "protocol": protocol,
                "url": url,
            }
            self.streams[stream_id] = stream_info
            return url

        except Exception as e:
            logger.error(
                f"Error starting {protocol} stream for device {device.device_id}: {e}"
            )
            raise

    async def stop_stream(self, stream_id: str) -> bool:
        """
        Stop a stream.

        Args:
            stream_id (str): ID of the stream to stop.

        Returns:
            bool: True if stream was stopped successfully, False otherwise.

        Raises:
            RuntimeError: If there is an error stopping the stream.
        """
        if stream_id not in self.streams:
            logger.warning(f"Attempt to stop non-existent stream: {stream_id}")
            return False

        stream_info = self.streams[stream_id]
        protocol = stream_info["protocol"]

        try:
            # Stop stream with appropriate server
            if protocol == "rtsp":
                success = await self.rtsp_server.stop_stream(stream_id)
            elif protocol == "rtmp":
                success = await self.rtmp_server.stop_stream(stream_id)
            elif protocol == "webrtc":
                success = await self.webrtc_server.stop_stream(stream_id)
            else:
                raise ValueError(f"Unsupported protocol: {protocol}")

            if success:
                # Remove stream info
                del self.streams[stream_id]
                return True
            return False

        except Exception as e:
            logger.error(f"Error stopping stream: {e}")
            raise RuntimeError(f"Error stopping stream: {e}")

    def get_streams(self) -> Dict[str, dict]:
        """
        Get information about all active streams.

        Returns:
            Dict[str, dict]: Dictionary mapping stream IDs to stream information.
        """
        return self.streams.copy()

    def get_stream_info(self, stream_id: str) -> Optional[dict]:
        """
        Get information about a specific stream.

        Args:
            stream_id (str): ID of the stream.

        Returns:
            Optional[dict]: Stream information if found, None otherwise.
        """
        return self.streams.get(stream_id)
