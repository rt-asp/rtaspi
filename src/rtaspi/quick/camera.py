"""
Simplified camera management functions.

This module provides easy-to-use functions for managing camera devices,
abstracting away the complexity of the full API.
"""

from typing import Optional, Dict, List, Any
import logging

from rtaspi.constants import DeviceType, OutputType
from rtaspi.api import DeviceAPI, StreamAPI


def list_cameras() -> List[Dict[str, Any]]:
    """List all available cameras.

    Returns:
        List of camera information dictionaries, each containing:
        - name: Camera name
        - type: Camera type (USB_CAMERA, BUILT_IN_CAMERA, etc.)
        - status: Whether the camera is online
        - capabilities: Camera capabilities (resolution, etc.)
    """
    device_api = DeviceAPI()
    cameras = []

    # Get all camera devices
    devices = device_api.list_devices(device_type=DeviceType.USB_CAMERA)
    devices.update(device_api.list_devices(device_type=DeviceType.BUILT_IN_CAMERA))
    devices.update(device_api.list_devices(device_type=DeviceType.CSI_CAMERA))

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
    type: str = "USB_CAMERA",
    resolution: str = "1280x720",
    framerate: int = 30,
    rtsp_url: Optional[str] = None,
    rtmp_url: Optional[str] = None,
    webrtc_url: Optional[str] = None,
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
    device_api = DeviceAPI()
    stream_api = StreamAPI()
    logger = logging.getLogger(__name__)

    # Auto-detect camera if name not provided
    if not name:
        # Try to find first available camera of requested type
        discovered = device_api.discover_devices(device_type=type, timeout=1.0)
        if not discovered:
            raise RuntimeError(f"No {type} cameras found")

        # Use first discovered camera
        camera_info = discovered[0]
        name = f"camera_{len(list_cameras()) + 1}"

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
    stream_name = f"{name}_stream"

    # Create stream
    stream_api.create_stream(
        name=stream_name,
        device=name,
        stream_type="video",
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
            output_type=OutputType.RTSP,
            output_name=f"{stream_name}_rtsp",
            settings={"url": rtsp_url},
        )
        output_count += 1

    if rtmp_url:
        stream_api.add_output(
            name=stream_name,
            output_type=OutputType.RTMP,
            output_name=f"{stream_name}_rtmp",
            settings={"url": rtmp_url},
        )
        output_count += 1

    if webrtc_url:
        stream_api.add_output(
            name=stream_name,
            output_type=OutputType.WEBRTC,
            output_name=f"{stream_name}_webrtc",
            settings={"url": webrtc_url},
        )
        output_count += 1

    # Add default RTSP output if no outputs specified
    if output_count == 0:
        default_url = f"rtsp://localhost:8554/{stream_name}"
        stream_api.add_output(
            name=stream_name,
            output_type=OutputType.RTSP,
            output_name=f"{stream_name}_rtsp",
            settings={"url": default_url},
        )
        logger.info(f"Added default RTSP output: {default_url}")

    # Start stream
    stream_api.start_stream(stream_name)
    logger.info(f"Started camera stream: {stream_name}")

    return stream_name


def stop_camera(stream_name: str) -> None:
    """Stop a camera stream.

    Args:
        stream_name: Stream name returned by start_camera()
    """
    stream_api = StreamAPI()
    logger = logging.getLogger(__name__)

    # Stop stream
    stream_api.stop_stream(stream_name)
    logger.info(f"Stopped camera stream: {stream_name}")

    # Remove stream
    stream_api.remove_stream(stream_name)
    logger.info(f"Removed camera stream: {stream_name}")
