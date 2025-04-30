"""
Simplified camera management functions.

This module provides easy-to-use functions and classes for managing camera devices,
abstracting away the complexity of the full API.
"""

from typing import Optional, Dict, List, Any, Tuple
import logging
import cv2

from rtaspi.constants import DeviceType, OutputType
from rtaspi.constants.devices import (
    DeviceSubType,
    DeviceCapability
)
from rtaspi.constants.camera import (
    DEFAULT_CAMERA_DEVICE,
    DEFAULT_CAMERA_RESOLUTION,
    DEFAULT_CAMERA_FRAMERATE,
    STREAM_NAME_SUFFIX,
    RTSP_OUTPUT_SUFFIX,
    RTMP_OUTPUT_SUFFIX,
    WEBRTC_OUTPUT_SUFFIX,
    AUTO_DETECT_TIMEOUT,
    AUTO_DETECT_NAME_PREFIX,
    CV_PROP_FRAME_WIDTH,
    CV_PROP_FRAME_HEIGHT,
    CV_PROP_FPS
)
from rtaspi.constants.streaming import (
    DEFAULT_RTSP_PORT,
    DEFAULT_RTMP_PORT,
    DEFAULT_WEBRTC_PORT
)
from rtaspi.api import DeviceAPI, StreamAPI
from rtaspi.core.config import ConfigManager
from rtaspi.core.mcp import MCPBroker

class Camera:
    """High-level camera interface for video capture and streaming."""
    
    def __init__(self, device: str = DEFAULT_CAMERA_DEVICE, 
                 resolution: str = DEFAULT_CAMERA_RESOLUTION, 
                 fps: int = DEFAULT_CAMERA_FRAMERATE):
        """Initialize camera.
        
        Args:
            device: Camera device identifier (number or path)
            resolution: Resolution in WxH format (e.g. "1280x720")
            fps: Frames per second
        """
        self.device = device
        self.resolution = resolution
        self.fps = fps
        
        # Parse resolution
        width, height = map(int, resolution.split("x"))
        self.width = width
        self.height = height
        
        # Initialize APIs with config and MCP broker
        self.config_manager = ConfigManager()
        self.mcp_broker = MCPBroker()
        self.device_api = DeviceAPI(config=self.config_manager.config, mcp_broker=self.mcp_broker)
        self.stream_api = StreamAPI(config=self.config_manager.config, mcp_broker=self.mcp_broker)
        
        # Initialize video capture
        self.cap = None
        self.stream_name = None
        
    def start(self) -> None:
        """Start camera capture."""
        # Start camera stream
        self.stream_name = start_camera(
            name=self.device,
            type=DeviceType.USB_CAMERA.value,
            resolution=self.resolution,
            framerate=self.fps,
            config=self.config_manager.config,
            mcp_broker=self.mcp_broker
        )
        
        # Open video capture
        self.cap = cv2.VideoCapture(int(self.device) if self.device.isdigit() else self.device)
        self.cap.set(CV_PROP_FRAME_WIDTH, self.width)
        self.cap.set(CV_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(CV_PROP_FPS, self.fps)
        
    def stop(self) -> None:
        """Stop camera capture."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            
        if self.stream_name is not None:
            stop_camera(
                self.stream_name,
                config=self.config_manager.config,
                mcp_broker=self.mcp_broker
            )
            self.stream_name = None
            
    def read(self) -> Optional[Any]:
        """Read a frame from the camera.
        
        Returns:
            Frame data if successful, None otherwise
        """
        if self.cap is None:
            return None
            
        ret, frame = self.cap.read()
        if not ret:
            return None
            
        return frame


def list_cameras(config=None, mcp_broker=None) -> List[Dict[str, Any]]:
    """List all available cameras.

    Args:
        config: Configuration dictionary
        mcp_broker: MCP broker instance

    Returns:
        List of camera information dictionaries, each containing:
        - name: Camera name
        - type: Camera type (USB_CAMERA, BUILT_IN_CAMERA, etc.)
        - status: Whether the camera is online
        - capabilities: Camera capabilities (resolution, etc.)
    """
    device_api = DeviceAPI(config=config, mcp_broker=mcp_broker)
    cameras = []

    # Get all camera devices
    # Get all camera devices
    devices = {}
    for camera_type in [
        DeviceType.USB_CAMERA,
        DeviceType.BUILT_IN_CAMERA,
        DeviceType.CSI_CAMERA,
        DeviceType.IP_CAMERA
    ]:
        devices.update(device_api.list_devices(device_type=camera_type))

    for name, config in devices.items():
        cameras.append(
            {
                "name": name,
                "type": config["type"],
                "status": config.get("status", {}).get("online", False),
                "capabilities": config.get("capabilities", {}),
            }
        )

    return cameras


def start_camera(
    name: Optional[str] = None,
            type: str = DeviceType.USB_CAMERA.value,
    resolution: str = DEFAULT_CAMERA_RESOLUTION,
    framerate: int = DEFAULT_CAMERA_FRAMERATE,
    rtsp_url: Optional[str] = None,
    rtmp_url: Optional[str] = None,
    webrtc_url: Optional[str] = None,
    config=None,
    mcp_broker=None,
) -> str:
    """Start a camera stream.

    This function will:
    1. Find or create a camera device
    2. Create a stream for the camera
    3. Configure outputs (RTSP, RTMP, WebRTC)
    4. Start the stream

    Args:
        name: Camera name (auto-detected if not provided)
        type: Camera type (USB_CAMERA, BUILT_IN_CAMERA, CSI_CAMERA)
        resolution: Stream resolution (e.g., 1280x720)
        framerate: Stream framerate
        rtsp_url: Optional RTSP output URL
        rtmp_url: Optional RTMP output URL
        webrtc_url: Optional WebRTC output URL

    Returns:
        Stream name that can be used with other functions
    """
    device_api = DeviceAPI(config=config, mcp_broker=mcp_broker)
    stream_api = StreamAPI(config=config, mcp_broker=mcp_broker)
    logger = logging.getLogger(__name__)

    # Auto-detect camera if name not provided, is "default", or is numeric
    if not name or name == DEFAULT_CAMERA_DEVICE or name.isdigit():
        # Try to find first available camera
        discovered = device_api.discover_devices(timeout=AUTO_DETECT_TIMEOUT)
        # Filter for camera devices
        discovered = [d for d in discovered if DeviceType[d["type"]].is_camera]
        if not discovered:
            raise RuntimeError(f"No {type} cameras found")

        # Use first discovered camera
        camera_info = discovered[0]
        name = f"{AUTO_DETECT_NAME_PREFIX}{len(list_cameras()) + 1}"

        # Add camera device
        device_api.add_device(
            name=name,
            type=type,
            settings={
                "resolution": resolution,
                "framerate": framerate,
            },
        )
        logger.info(f"Auto-detected and added camera: {name}")
    else:
        # Check if camera exists
        if not device_api.get_device(name):
            # Add camera device
            device_api.add_device(
                name=name,
                type=type,
                settings={
                    "resolution": resolution,
                    "framerate": framerate,
                },
            )
            logger.info(f"Added camera: {name}")

    # Create stream name
    stream_name = f"{name}{STREAM_NAME_SUFFIX}"

    # Create stream
    stream_api.create_stream(
        name=stream_name,
        device=name,
        stream_type=DeviceCapability.VIDEO.value,
        settings={
            "resolution": resolution,
            "framerate": framerate,
        },
    )

    # Add outputs
    output_count = 0
    if rtsp_url:
        stream_api.add_output(
            name=stream_name,
            output_type=OutputType.RTSP.value,
            output_name=f"{stream_name}{RTSP_OUTPUT_SUFFIX}",
            settings={"url": rtsp_url},
        )
        output_count += 1

    if rtmp_url:
        stream_api.add_output(
            name=stream_name,
            output_type=OutputType.RTMP.value,
            output_name=f"{stream_name}{RTMP_OUTPUT_SUFFIX}",
            settings={"url": rtmp_url},
        )
        output_count += 1

    if webrtc_url:
        stream_api.add_output(
            name=stream_name,
            output_type=OutputType.WEBRTC.value,
            output_name=f"{stream_name}{WEBRTC_OUTPUT_SUFFIX}",
            settings={"url": webrtc_url},
        )
        output_count += 1

    # Add default RTSP output if no outputs specified
    if output_count == 0:
        default_url = f"rtsp://localhost:{DEFAULT_RTSP_PORT}/{stream_name}"
        stream_api.add_output(
            name=stream_name,
            output_type=OutputType.RTSP.value,
            output_name=f"{stream_name}{RTSP_OUTPUT_SUFFIX}",
            settings={"url": default_url},
        )
        logger.info(f"Added default RTSP output: {default_url}")

    # Start stream
    stream_api.start_stream(stream_name)
    logger.info(f"Started camera stream: {stream_name}")

    return stream_name


def stop_camera(stream_name: str, config=None, mcp_broker=None) -> None:
    """Stop a camera stream.

    Args:
        stream_name: Stream name returned by start_camera()
        config: Configuration dictionary
        mcp_broker: MCP broker instance
    """
    stream_api = StreamAPI(config=config, mcp_broker=mcp_broker)
    logger = logging.getLogger(__name__)

    # Stop stream
    stream_api.stop_stream(stream_name)
    logger.info(f"Stopped camera stream: {stream_name}")

    # Remove stream
    stream_api.remove_stream(stream_name)
    logger.info(f"Removed camera stream: {stream_name}")
