"""
rtaspi - Real-Time Annotation and Stream Processing
WebRTC streaming server
"""

import logging
import os
import json
import time
import socket
import subprocess
import shlex
from typing import Optional, Dict

from .pipeline import WebRTCPipeline
from .ui import WebRTCUI

logger = logging.getLogger(__name__)


class WebRTCServer:
    """WebRTC streaming server implementation."""

    def __init__(self, config: dict):
        """
        Initialize WebRTC server.

        Args:
            config (dict): Server configuration.
        """
        # Get configuration
        streaming_config = config.get("streaming", {}).get("webrtc", {})
        self.port_start = streaming_config.get("port_start", 8080)
        self.storage_path = config.get("system", {}).get("storage_path", "storage")
        self.stun_server = streaming_config.get(
            "stun_server", "stun://stun.l.google.com:19302"
        )
        self.turn_server = streaming_config.get("turn_server", "")
        self.turn_username = streaming_config.get("turn_username", "")
        self.turn_password = streaming_config.get("turn_password", "")

        # Initialize components
        self.pipeline_generator = WebRTCPipeline()
        self.ui_generator = WebRTCUI()

    async def start_stream(
        self, device, stream_id: str, output_dir: str
    ) -> Optional[str]:
        """
        Start WebRTC stream from local device.

        Args:
            device: Device object.
            stream_id (str): Stream identifier.
            output_dir (str): Output directory path.

        Returns:
            Optional[str]: Stream URL if successful, None otherwise.
        """
        try:
            # Find free port
            port = self._find_free_port(self.port_start)

            # Prepare GStreamer pipelines
            input_pipeline = WebRTCPipeline.create_input_pipeline(device)
            encoding_pipeline = WebRTCPipeline.create_encoding_pipeline(device)

            if not input_pipeline or not encoding_pipeline:
                logger.error(
                    f"Cannot prepare GStreamer pipeline for device {device.device_id}"
                )
                return None

            # Create GStreamer config file
            gst_config_path = os.path.join(output_dir, "webrtc_config.json")
            with open(gst_config_path, "w") as f:
                json.dump(
                    {
                        "port": port,
                        "stream_id": stream_id,
                        "device_id": device.device_id,
                        "device_type": device.type,
                        "stun_server": self.stun_server,
                        "turn_server": self.turn_server,
                        "turn_username": self.turn_username,
                        "turn_password": self.turn_password,
                    },
                    f,
                    indent=2,
                )

            # Create full GStreamer pipeline
            gst_pipeline = f"{input_pipeline} ! {encoding_pipeline} ! webrtcbin name=webrtcbin stun-server={self.stun_server}"

            # Generate and save HTML page
            html_content = WebRTCUI.generate_client_page(
                stream_id, port, self.stun_server
            )
            html_path = os.path.join(output_dir, "webrtc.html")
            with open(html_path, "w") as f:
                f.write(html_content)

            # Start HTTP server for serving WebRTC page
            http_server_cmd = [
                "python3",
                "-m",
                "http.server",
                str(port),
                "--directory",
                output_dir,
            ]
            http_process = subprocess.Popen(
                http_server_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            # Wait for HTTP server to start
            time.sleep(1)

            # Start GStreamer pipeline
            gst_cmd = ["gst-launch-1.0", "-v"] + shlex.split(gst_pipeline)
            logger.debug(f"Starting command: {' '.join(gst_cmd)}")

            process = subprocess.Popen(
                gst_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            # Check if process started successfully
            time.sleep(2)
            if process.poll() is not None:
                logger.error(
                    f"GStreamer process exited with code: {process.returncode}"
                )
                http_process.terminate()
                return None

            # Store process information
            url = f"http://localhost:{port}/webrtc.html?stream={stream_id}"
            self.streams[stream_id] = {
                "process": process,
                "http_process": http_process,
                "device_id": device.device_id,
                "type": device.type,
                "url": url,
                "protocol": "webrtc",
                "port": port,
            }

            return url

        except Exception as e:
            logger.error(f"Error starting WebRTC stream: {e}")
            return None

    async def proxy_stream(
        self,
        device,
        stream_id: str,
        source_url: str,
        output_dir: str,
        transcode: bool = False,
    ) -> Optional[str]:
        """
        Start WebRTC proxy for remote stream.

        Args:
            device: Network device object.
            stream_id (str): Stream identifier.
            source_url (str): Source stream URL.
            output_dir (str): Output directory path.
            transcode (bool): Whether to transcode the stream.

        Returns:
            Optional[str]: Stream URL if successful, None otherwise.
        """
        try:
            # Find free port
            port = self._find_free_port(self.port_start)

            # Create proxy pipeline
            gst_pipeline = WebRTCPipeline.create_proxy_pipeline(
                device, source_url, transcode
            )
            gst_pipeline += (
                f" ! webrtcbin name=webrtcbin stun-server={self.stun_server}"
            )

            # Generate and save HTML page
            html_content = WebRTCUI.generate_client_page(
                stream_id, port, self.stun_server
            )
            html_path = os.path.join(output_dir, "webrtc.html")
            with open(html_path, "w") as f:
                f.write(html_content)

            # Start HTTP server
            http_server_cmd = [
                "python3",
                "-m",
                "http.server",
                str(port),
                "--directory",
                output_dir,
            ]
            http_process = subprocess.Popen(
                http_server_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            # Wait for HTTP server to start
            time.sleep(1)

            # Start GStreamer pipeline
            gst_cmd = ["gst-launch-1.0", "-v"] + shlex.split(gst_pipeline)
            logger.debug(f"Starting WebRTC proxy command: {' '.join(gst_cmd)}")

            process = subprocess.Popen(
                gst_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

            # Check if process started successfully
            time.sleep(2)
            if process.poll() is not None:
                logger.error(
                    f"GStreamer proxy process exited with code: {process.returncode}"
                )
                http_process.terminate()
                return None

            # Create stream URL
            url = f"http://localhost:{port}/webrtc.html?stream={stream_id}"

            # Store process information
            self.streams[stream_id] = {
                "process": process,
                "http_process": http_process,
                "device_id": device.device_id,
                "type": device.type,
                "url": url,
                "protocol": "webrtc",
                "port": port,
            }

            return url

        except Exception as e:
            logger.error(f"Error starting WebRTC proxy: {e}")
            return None

    async def stop_stream(self, stream_id: str) -> bool:
        """
        Stop WebRTC stream.

        Args:
            stream_id (str): Stream identifier.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if stream_id not in self.streams:
                logger.warning(f"Stream not found: {stream_id}")
                return False

            stream_info = self.streams[stream_id]

            # Stop GStreamer process
            if stream_info["process"]:
                stream_info["process"].terminate()
                stream_info["process"].wait()

            # Stop HTTP server
            if stream_info["http_process"]:
                stream_info["http_process"].terminate()
                stream_info["http_process"].wait()

            # Remove stream info
            del self.streams[stream_id]
            return True

        except Exception as e:
            logger.error(f"Error stopping WebRTC stream: {e}")
            return False

    def _find_free_port(self, start_port: int) -> int:
        """
        Find free port starting from given port.

        Args:
            start_port (int): Starting port number.

        Returns:
            int: Free port number.

        Raises:
            Exception: If no free port found.
        """
        port = start_port
        max_port = start_port + 1000  # Limit port range

        while port < max_port:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()

            if result != 0:  # Port is free
                return port

            port += 1

        raise Exception(f"No free port found in range {start_port}-{max_port}")
