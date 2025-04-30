"""
Base device manager implementation.
"""

import os
import json
import logging
import threading
import time
import socket
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from rtaspi_core.mcp import MCPClient

logger = logging.getLogger("rtaspi.devices.manager")


class DeviceManager(ABC):
    """Base class for device managers."""

    def __init__(self, config: Dict[str, Any], mcp_broker: Any):
        """
        Initialize device manager.

        Args:
            config (Dict[str, Any]): Manager configuration.
            mcp_broker (Any): MCP broker instance.
        """
        self.config = config
        self.mcp_broker = mcp_broker
        self.running = False
        self.scan_thread = None
        self.devices: Dict[str, Any] = {}  # device_id -> device_info
        self.streams: Dict[str, Any] = {}  # stream_id -> stream_info

        # Prepare storage directories
        self.storage_path = config.get("system", {}).get("storage_path", "storage")
        os.makedirs(self.storage_path, exist_ok=True)

        # Create MCP client
        self.mcp_client = MCPClient(mcp_broker, client_id=self._get_client_id())

    @abstractmethod
    def _get_client_id(self) -> str:
        """
        Get MCP client identifier.

        Returns:
            str: MCP client identifier.
        """
        pass

    @abstractmethod
    def _scan_devices(self) -> None:
        """Scan for devices."""
        pass

    def start_stream(self, device_id: str, stream_path: Optional[str] = None) -> bool:
        """
        Start a stream from the specified device.

        Args:
            device_id (str): The ID of the device to stream from.
            stream_path (str, optional): The specific stream path to use.

        Returns:
            bool: True if the stream was started successfully, False otherwise.
        """
        logger.info(f"Starting stream from device {device_id}")
        return True

    def start(self) -> None:
        """Start the device manager."""
        if self.running:
            return

        self.running = True
        logger.info(f"Starting device manager: {self._get_client_id()}")

        # Subscribe to MCP events
        self._subscribe_to_events()

        # Start scanning thread
        self.scan_thread = threading.Thread(target=self._scan_loop)
        self.scan_thread.daemon = True
        self.scan_thread.start()

        logger.info(f"Device manager started: {self._get_client_id()}")

    def stop(self) -> None:
        """Stop the device manager."""
        if not self.running:
            return

        self.running = False
        logger.info(f"Stopping device manager: {self._get_client_id()}")

        # Stop all streams
        for stream_id in list(self.streams.keys()):
            self.stop_stream(stream_id)

        # Stop scanning thread
        if self.scan_thread:
            self.scan_thread.join(timeout=5)

        # Unregister from MCP
        self.mcp_client.close()

        logger.info(f"Device manager stopped: {self._get_client_id()}")

    @abstractmethod
    def _subscribe_to_events(self) -> None:
        """Subscribe to MCP events."""
        pass

    def _scan_loop(self) -> None:
        """Main device scanning loop."""
        while self.running:
            logger.debug(f"Scanning devices: {self._get_client_id()}")

            try:
                # Scan devices
                self._scan_devices()

                # Publish device information
                self._publish_devices_info()

            except Exception as e:
                logger.error(f"Error during device scan: {e}")

            # Wait for next scan
            for _ in range(self._get_scan_interval()):
                if not self.running:
                    break
                time.sleep(1)

    def _get_scan_interval(self) -> int:
        """
        Get scanning interval in seconds.

        Returns:
            int: Scanning interval in seconds.
        """
        return 60  # Default interval

    @abstractmethod
    def _publish_devices_info(self) -> None:
        """Publish device information."""
        pass

    def get_devices(self) -> Dict[str, Any]:
        """
        Get list of devices.

        Returns:
            Dict[str, Any]: Dictionary of devices.
        """
        return self.devices

    def get_streams(self) -> Dict[str, Any]:
        """
        Get list of streams.

        Returns:
            Dict[str, Any]: Dictionary of streams.
        """
        return {
            stream_id: {k: v for k, v in info.items() if k != "process"}
            for stream_id, info in self.streams.items()
        }

    def stop_stream(self, stream_id: str) -> bool:
        """
        Stop a stream.

        Args:
            stream_id (str): Stream identifier.

        Returns:
            bool: True if stopped successfully, False otherwise.
        """
        if stream_id not in self.streams:
            logger.error(f"Unknown stream: {stream_id}")
            return False

        try:
            # Get stream information
            stream_info = self.streams[stream_id]

            # Stop main process
            process = stream_info.get("process")
            if process:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()

            # Stop additional processes
            for key in ["rtsp_process", "rtmp_process", "http_process", "nginx_process"]:
                proc = stream_info.get(key)
                if proc:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()

            # Remove stream from list
            self.streams.pop(stream_id)

            logger.info(f"Stopped stream {stream_id}")

            # Publish stream stop information
            self._publish_stream_stopped(stream_id, stream_info)

            return True

        except Exception as e:
            logger.error(f"Error stopping stream {stream_id}: {e}")
            return False

    @abstractmethod
    def _publish_stream_stopped(self, stream_id: str, stream_info: Dict[str, Any]) -> None:
        """
        Publish stream stop information.

        Args:
            stream_id (str): Stream identifier.
            stream_info (Dict[str, Any]): Stream information.
        """
        pass

    def find_free_port(self, start_port: int) -> int:
        """
        Find a free port starting from the specified port.

        Args:
            start_port (int): Starting port number.

        Returns:
            int: Free port number.

        Raises:
            Exception: If no free port is found.
        """
        port = start_port
        max_port = start_port + 1000  # Limit scanning range

        while port < max_port:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()

            if result != 0:  # Port is free
                return port

            port += 1

        raise Exception(f"No free port found in range {start_port}-{max_port}")
