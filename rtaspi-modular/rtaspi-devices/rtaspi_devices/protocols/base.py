"""
Base protocol interfaces for device communication.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum, auto


class ProtocolStatus(Enum):
    """Protocol connection status."""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    ERROR = auto()


class DeviceProtocol(ABC):
    """Base class for all device communication protocols."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize protocol with configuration.

        Args:
            config (Dict[str, Any]): Protocol configuration parameters.
        """
        self.config = config
        self.status = ProtocolStatus.DISCONNECTED
        self.error_message: Optional[str] = None

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the device.

        Returns:
            bool: True if connection successful, False otherwise.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the device.

        Returns:
            bool: True if disconnection successful, False otherwise.
        """
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """
        Check if protocol is currently connected.

        Returns:
            bool: True if connected, False otherwise.
        """
        pass

    @abstractmethod
    async def send_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Send a command to the device.

        Args:
            command (str): Command to send.
            **kwargs: Additional command parameters.

        Returns:
            Dict[str, Any]: Command response.
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert protocol state to dictionary.

        Returns:
            Dict[str, Any]: Protocol state as dictionary.
        """
        return {
            "status": self.status.name.lower(),
            "error": self.error_message,
            "config": {
                k: v for k, v in self.config.items()
                if k not in ["password", "secret", "key"]  # Exclude sensitive data
            }
        }


class StreamingProtocol(DeviceProtocol):
    """Base class for streaming protocols (RTSP, RTMP, etc.)."""

    @abstractmethod
    async def start_stream(self, stream_id: str) -> bool:
        """
        Start a media stream.

        Args:
            stream_id (str): Unique stream identifier.

        Returns:
            bool: True if stream started successfully, False otherwise.
        """
        pass

    @abstractmethod
    async def stop_stream(self, stream_id: str) -> bool:
        """
        Stop a media stream.

        Args:
            stream_id (str): Unique stream identifier.

        Returns:
            bool: True if stream stopped successfully, False otherwise.
        """
        pass

    @abstractmethod
    async def get_stream_info(self, stream_id: str) -> Dict[str, Any]:
        """
        Get information about a stream.

        Args:
            stream_id (str): Unique stream identifier.

        Returns:
            Dict[str, Any]: Stream information.
        """
        pass


class ControlProtocol(DeviceProtocol):
    """Base class for device control protocols."""

    @abstractmethod
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get device capabilities.

        Returns:
            Dict[str, Any]: Device capabilities.
        """
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Get device status.

        Returns:
            Dict[str, Any]: Device status information.
        """
        pass

    @abstractmethod
    async def configure(self, settings: Dict[str, Any]) -> bool:
        """
        Configure device settings.

        Args:
            settings (Dict[str, Any]): Device settings to configure.

        Returns:
            bool: True if configuration successful, False otherwise.
        """
        pass
