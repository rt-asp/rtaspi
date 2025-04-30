"""
Simplified microphone management functions.

This module provides easy-to-use functions and classes for managing microphone devices,
abstracting away the complexity of the full API.
"""

from typing import Optional, Dict, List, Any
import logging
import pyaudio
import numpy as np

from rtaspi.constants import DeviceType, OutputType
from rtaspi.schemas.stream import StreamType
from rtaspi.api import DeviceAPI, StreamAPI
from rtaspi.core.config import ConfigManager
from rtaspi.core.mcp import MCPBroker

class Microphone:
    """High-level microphone interface for audio capture and streaming."""
    
    def __init__(self, device: str = "0", sample_rate: int = 44100, channels: int = 2):
        """Initialize microphone.
        
        Args:
            device: Microphone device identifier (number or path)
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels (1 for mono, 2 for stereo)
        """
        self.device = device
        self.sample_rate = sample_rate
        self.channels = channels
        
        # Initialize APIs with config and MCP broker
        self.config_manager = ConfigManager()
        self.mcp_broker = MCPBroker()
        self.device_api = DeviceAPI(config=self.config_manager.config, mcp_broker=self.mcp_broker)
        self.stream_api = StreamAPI(config=self.config_manager.config, mcp_broker=self.mcp_broker)
        
        # Initialize audio capture
        self.audio = None
        self.stream = None
        self.stream_name = None
        
    def start(self) -> None:
        """Start microphone capture."""
        # Start microphone stream
        self.stream_name = start_microphone(
            name=self.device,
            type=DeviceType.USB_MICROPHONE.value,
            sample_rate=self.sample_rate,
            channels=self.channels,
            config=self.config_manager.config,
            mcp_broker=self.mcp_broker
        )
        
        # Open audio capture
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paFloat32,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=int(self.device) if self.device.isdigit() else None,
            frames_per_buffer=1024
        )
        
    def stop(self) -> None:
        """Stop microphone capture."""
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
        if self.audio is not None:
            self.audio.terminate()
            self.audio = None
            
        if self.stream_name is not None:
            stop_microphone(
                self.stream_name,
                config=self.config_manager.config,
                mcp_broker=self.mcp_broker
            )
            self.stream_name = None
            
    def read(self) -> Optional[np.ndarray]:
        """Read audio data from the microphone.
        
        Returns:
            Audio data if successful, None otherwise
        """
        if self.stream is None:
            return None
            
        try:
            data = self.stream.read(1024, exception_on_overflow=False)
            return np.frombuffer(data, dtype=np.float32)
        except Exception:
            return None


def list_microphones(config=None, mcp_broker=None) -> List[Dict[str, Any]]:
    """List all available microphones.

    Args:
        config: Configuration dictionary
        mcp_broker: MCP broker instance

    Returns:
        List of microphone information dictionaries, each containing:
        - name: Microphone name
        - type: Microphone type (USB_MICROPHONE, BUILT_IN_MICROPHONE, etc.)
        - status: Whether the microphone is online
        - capabilities: Microphone capabilities (sample rate, etc.)
    """
    device_api = DeviceAPI(config=config, mcp_broker=mcp_broker)
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
    type: str = DeviceType.USB_MICROPHONE.value,
    sample_rate: int = 44100,
    channels: int = 2,
    rtsp_url: Optional[str] = None,
    rtmp_url: Optional[str] = None,
    webrtc_url: Optional[str] = None,
    config=None,
    mcp_broker=None,
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
    device_api = DeviceAPI(config=config, mcp_broker=mcp_broker)
    stream_api = StreamAPI(config=config, mcp_broker=mcp_broker)
    logger = logging.getLogger(__name__)

    # Auto-detect microphone if name not provided or is "default"
    if not name or name == "default":
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
        stream_type=StreamType.AUDIO.value,
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
            output_type=OutputType.RTSP.value,
            output_name=f"{stream_name}_rtsp",
            settings={"url": rtsp_url},
        )
        output_count += 1

    if rtmp_url:
        stream_api.add_output(
            name=stream_name,
            output_type=OutputType.RTMP.value,
            output_name=f"{stream_name}_rtmp",
            settings={"url": rtmp_url},
        )
        output_count += 1

    if webrtc_url:
        stream_api.add_output(
            name=stream_name,
            output_type=OutputType.WEBRTC.value,
            output_name=f"{stream_name}_webrtc",
            settings={"url": webrtc_url},
        )
        output_count += 1

    # Add default RTSP output if no outputs specified
    if output_count == 0:
        default_url = f"rtsp://localhost:8554/{stream_name}"
        stream_api.add_output(
            name=stream_name,
            output_type=OutputType.RTSP.value,
            output_name=f"{stream_name}_rtsp",
            settings={"url": default_url},
        )
        logger.info(f"Added default RTSP output: {default_url}")

    # Start stream
    stream_api.start_stream(stream_name)
    logger.info(f"Started microphone stream: {stream_name}")

    return stream_name


def stop_microphone(stream_name: str, config=None, mcp_broker=None) -> None:
    """Stop a microphone stream.

    Args:
        stream_name: Stream name returned by start_microphone()
        config: Configuration dictionary
        mcp_broker: MCP broker instance
    """
    stream_api = StreamAPI(config=config, mcp_broker=mcp_broker)
    logger = logging.getLogger(__name__)

    # Stop stream
    stream_api.stop_stream(stream_name)
    logger.info(f"Stopped microphone stream: {stream_name}")

    # Remove stream
    stream_api.remove_stream(stream_name)
    logger.info(f"Removed microphone stream: {stream_name}")
