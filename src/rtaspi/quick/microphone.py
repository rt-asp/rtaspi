"""
Simplified microphone management functions.

This module provides easy-to-use functions for managing microphone devices,
abstracting away the complexity of the full API.
"""

from typing import Optional, Dict, List, Any
import logging

from rtaspi.constants import DeviceType, OutputType
from rtaspi.api import DeviceAPI, StreamAPI


def list_microphones() -> List[Dict[str, Any]]:
    """List all available microphones.

    Returns:
        List of microphone information dictionaries, each containing:
        - name: Microphone name
        - type: Microphone type (USB_MICROPHONE, BUILT_IN_MICROPHONE, etc.)
        - status: Whether the microphone is online
        - capabilities: Microphone capabilities (sample rate, etc.)
    """
    device_api = DeviceAPI()
    microphones = []

    # Get all microphone devices
    devices = device_api.list_devices(device_type=DeviceType.USB_MICROPHONE)
    devices.update(device_api.list_devices(device_type=DeviceType.BUILT_IN_MICROPHONE))

    for name, config in devices.items():
        microphones.append(
            {
                "name": name,
                "type": config["type"],
                "status": config.get("status", {}).get("online", False),
                "capabilities": config.get("capabilities", {}),
            }
        )

    return microphones


def start_microphone(
    name: Optional[str] = None,
    type: str = "USB_MICROPHONE",
    sample_rate: int = 44100,
    channels: int = 2,
    rtsp_url: Optional[str] = None,
    rtmp_url: Optional[str] = None,
    webrtc_url: Optional[str] = None,
) -> str:
    """Start a microphone stream.

    This function will:
    1. Find or create a microphone device
    2. Create a stream for the microphone
    3. Configure outputs (RTSP, RTMP, WebRTC)
    4. Start the stream

    Args:
        name: Microphone name (auto-detected if not provided)
        type: Microphone type (USB_MICROPHONE, BUILT_IN_MICROPHONE)
        sample_rate: Audio sample rate in Hz
        channels: Number of audio channels (1 for mono, 2 for stereo)
        rtsp_url: Optional RTSP output URL
        rtmp_url: Optional RTMP output URL
        webrtc_url: Optional WebRTC output URL

    Returns:
        Stream name that can be used with other functions
    """
    device_api = DeviceAPI()
    stream_api = StreamAPI()
    logger = logging.getLogger(__name__)

    # Auto-detect microphone if name not provided
    if not name:
        # Try to find first available microphone of requested type
        discovered = device_api.discover_devices(device_type=type, timeout=1.0)
        if not discovered:
            raise RuntimeError(f"No {type} microphones found")

        # Use first discovered microphone
        microphone_info = discovered[0]
        name = f"microphone_{len(list_microphones()) + 1}"

        # Add microphone device
        device_api.add_device(
            name=name,
            type=type,
            settings={
                "sample_rate": sample_rate,
                "channels": channels,
            },
        )
        logger.info(f"Auto-detected and added microphone: {name}")
    else:
        # Check if microphone exists
        if not device_api.get_device(name):
            # Add microphone device
            device_api.add_device(
                name=name,
                type=type,
                settings={
                    "sample_rate": sample_rate,
                    "channels": channels,
                },
            )
            logger.info(f"Added microphone: {name}")

    # Create stream name
    stream_name = f"{name}_stream"

    # Create stream
    stream_api.create_stream(
        name=stream_name,
        device=name,
        stream_type="audio",
        settings={
            "sample_rate": sample_rate,
            "channels": channels,
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
    logger.info(f"Started microphone stream: {stream_name}")

    return stream_name


def stop_microphone(stream_name: str) -> None:
    """Stop a microphone stream.

    Args:
        stream_name: Stream name returned by start_microphone()
    """
    stream_api = StreamAPI()
    logger = logging.getLogger(__name__)

    # Stop stream
    stream_api.stop_stream(stream_name)
    logger.info(f"Stopped microphone stream: {stream_name}")

    # Remove stream
    stream_api.remove_stream(stream_name)
    logger.info(f"Removed microphone stream: {stream_name}")
