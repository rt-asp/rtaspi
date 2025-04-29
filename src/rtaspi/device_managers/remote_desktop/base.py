"""Base class for remote desktop protocol devices."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple

from ..base import BaseDevice
from ...streaming import StreamOutput


class RemoteDesktopDevice(BaseDevice, ABC):
    """Abstract base class for remote desktop protocol devices."""

    def __init__(self, device_id: str, config: Dict[str, Any]):
        """Initialize remote desktop device.
        
        Args:
            device_id: Unique device identifier
            config: Device configuration dictionary
        """
        super().__init__(device_id, config)
        self.host = config.get('host', 'localhost')
        self.port = config.get('port')
        self.username = config.get('username')
        self.password = config.get('password')
        self._stream_output: Optional[StreamOutput] = None
        self._connected = False

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the remote desktop server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the remote desktop server."""
        pass

    @abstractmethod
    def get_frame(self) -> Optional[bytes]:
        """Get current frame from remote desktop.
        
        Returns:
            Optional[bytes]: Frame data if available, None otherwise
        """
        pass

    @abstractmethod
    def send_mouse_event(self, x: int, y: int, button: int = 0, pressed: bool = True) -> None:
        """Send mouse event to remote desktop.
        
        Args:
            x: Mouse X coordinate
            y: Mouse Y coordinate
            button: Mouse button (0=left, 1=middle, 2=right)
            pressed: True if button pressed, False if released
        """
        pass

    @abstractmethod
    def send_key_event(self, key_code: int, pressed: bool = True) -> None:
        """Send keyboard event to remote desktop.
        
        Args:
            key_code: Key code
            pressed: True if key pressed, False if released
        """
        pass

    @property
    def is_connected(self) -> bool:
        """Check if device is currently connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._connected

    def get_stream_output(self) -> Optional[StreamOutput]:
        """Get current stream output.
        
        Returns:
            Optional[StreamOutput]: Current stream output if available
        """
        return self._stream_output

    def set_stream_output(self, output: StreamOutput) -> None:
        """Set stream output for device.
        
        Args:
            output: Stream output to set
        """
        self._stream_output = output

    @abstractmethod
    def get_resolution(self) -> Tuple[int, int]:
        """Get current screen resolution.
        
        Returns:
            Tuple[int, int]: Width and height of remote desktop
        """
        pass

    @abstractmethod
    def set_resolution(self, width: int, height: int) -> bool:
        """Set screen resolution.
        
        Args:
            width: Desired screen width
            height: Desired screen height
            
        Returns:
            bool: True if resolution was set successfully
        """
        pass

    @abstractmethod
    def get_refresh_rate(self) -> int:
        """Get current refresh rate in Hz.
        
        Returns:
            int: Current refresh rate
        """
        pass

    @abstractmethod
    def set_refresh_rate(self, rate: int) -> bool:
        """Set refresh rate.
        
        Args:
            rate: Desired refresh rate in Hz
            
        Returns:
            bool: True if refresh rate was set successfully
        """
        pass
