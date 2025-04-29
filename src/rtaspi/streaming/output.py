"""Stream output configuration and management."""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class StreamOutput:
    """Stream output configuration."""

    protocol: str  # e.g. 'rtsp', 'rtmp', 'webrtc'
    host: str
    port: int
    path: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

    def get_url(self) -> str:
        """Get complete stream URL.
        
        Returns:
            str: Complete stream URL including protocol, host, port and path
        """
        base_url = f"{self.protocol}://{self.host}:{self.port}"
        if self.path:
            # Remove leading slash if present to avoid double slashes
            path = self.path[1:] if self.path.startswith('/') else self.path
            base_url = f"{base_url}/{path}"
        
        # Add options as URL parameters if present
        if self.options:
            params = "&".join([f"{k}={v}" for k, v in self.options.items()])
            base_url = f"{base_url}?{params}"
        
        return base_url

    def to_dict(self) -> Dict[str, Any]:
        """Convert stream output to dictionary.
        
        Returns:
            dict: Dictionary containing stream output configuration
        """
        return {
            "protocol": self.protocol,
            "host": self.host,
            "port": self.port,
            "path": self.path,
            "options": self.options,
            "url": self.get_url()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamOutput':
        """Create stream output from dictionary.
        
        Args:
            data: Dictionary containing stream output configuration
            
        Returns:
            StreamOutput: New stream output instance
        """
        return cls(
            protocol=data["protocol"],
            host=data["host"],
            port=data["port"],
            path=data.get("path"),
            options=data.get("options")
        )
