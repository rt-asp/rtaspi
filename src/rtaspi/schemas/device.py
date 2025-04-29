"""
Schema definitions for device configurations.

This module provides Pydantic models for validating device configurations,
ensuring that all required fields are present and have the correct types.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from rtaspi.constants import DeviceType, ProtocolType


class DeviceAuth(BaseModel):
    """Authentication configuration for devices that require it."""
    
    protocol: ProtocolType = Field(
        ...,
        description="Authentication protocol to use"
    )
    username: Optional[str] = Field(
        None,
        description="Username for authentication"
    )
    password: Optional[str] = Field(
        None,
        description="Password for authentication"
    )
    token: Optional[str] = Field(
        None,
        description="Authentication token (for OAuth2, JWT, etc.)"
    )
    key_file: Optional[str] = Field(
        None,
        description="Path to key file (for SSH, etc.)"
    )
    
    @validator("protocol")
    def validate_protocol(cls, v):
        """Ensure the protocol is an authentication protocol."""
        if not v.is_auth_protocol():
            raise ValueError(f"Protocol {v} is not an authentication protocol")
        return v


class DeviceConnection(BaseModel):
    """Connection configuration for network devices."""
    
    host: str = Field(
        ...,
        description="Hostname or IP address of the device"
    )
    port: Optional[int] = Field(
        None,
        description="Port number for the connection"
    )
    protocol: ProtocolType = Field(
        ...,
        description="Protocol to use for communication"
    )
    path: Optional[str] = Field(
        None,
        description="URL path or resource identifier"
    )
    auth: Optional[DeviceAuth] = Field(
        None,
        description="Authentication configuration if required"
    )
    
    @validator("port")
    def validate_port(cls, v):
        """Ensure port number is valid if provided."""
        if v is not None and not 1 <= v <= 65535:
            raise ValueError("Port number must be between 1 and 65535")
        return v


class DeviceCapabilities(BaseModel):
    """Device capabilities and features."""
    
    supports_video: bool = Field(
        False,
        description="Whether the device supports video capture"
    )
    supports_audio: bool = Field(
        False,
        description="Whether the device supports audio capture"
    )
    video_formats: Optional[List[str]] = Field(
        None,
        description="Supported video formats (e.g., H264, MJPEG)"
    )
    audio_formats: Optional[List[str]] = Field(
        None,
        description="Supported audio formats (e.g., AAC, PCM)"
    )
    resolutions: Optional[List[str]] = Field(
        None,
        description="Supported video resolutions"
    )
    frame_rates: Optional[List[float]] = Field(
        None,
        description="Supported frame rates"
    )
    ptz_supported: bool = Field(
        False,
        description="Whether the device supports PTZ controls"
    )


class DeviceConfig(BaseModel):
    """Complete device configuration schema."""
    
    name: str = Field(
        ...,
        description="Unique name to identify the device"
    )
    type: DeviceType = Field(
        ...,
        description="Type of the device"
    )
    enabled: bool = Field(
        True,
        description="Whether the device is enabled"
    )
    connection: Optional[DeviceConnection] = Field(
        None,
        description="Connection details for network devices"
    )
    capabilities: DeviceCapabilities = Field(
        default_factory=DeviceCapabilities,
        description="Device capabilities and features"
    )
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Device-specific settings"
    )
    
    @validator("connection", always=True)
    def validate_connection(cls, v, values):
        """Ensure connection details are present for network devices."""
        device_type = values.get("type")
        if device_type and device_type.is_network_device() and not v:
            raise ValueError("Connection details required for network devices")
        return v
    
    @validator("capabilities", always=True)
    def validate_capabilities(cls, v, values):
        """Set default capabilities based on device type."""
        device_type = values.get("type")
        if device_type:
            v.supports_video = device_type.is_video_device()
            v.supports_audio = device_type.is_audio_device()
        return v


class DeviceStatus(BaseModel):
    """Current status of a device."""
    
    online: bool = Field(
        False,
        description="Whether the device is currently online"
    )
    connected: bool = Field(
        False,
        description="Whether the device is currently connected"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if device is in error state"
    )
    last_seen: Optional[str] = Field(
        None,
        description="ISO timestamp of last successful connection"
    )
    stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Device-specific statistics"
    )
