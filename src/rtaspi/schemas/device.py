"""Device configuration schema."""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator

from ..constants.devices import (
    DEVICE_TYPE_CAMERA, DEVICE_TYPE_MICROPHONE, DEVICE_TYPE_SCREEN, DEVICE_TYPE_REMOTE_DESKTOP,
    DEVICE_SUBTYPE_USB, DEVICE_SUBTYPE_IP, DEVICE_SUBTYPE_RDP, DEVICE_SUBTYPE_VNC,
    DEVICE_PROTOCOL_RTSP, DEVICE_PROTOCOL_ONVIF, DEVICE_PROTOCOL_RDP, DEVICE_PROTOCOL_VNC
)


class DeviceConfig(BaseModel):
    """Base device configuration."""
    
    id: str = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Human readable device name")
    type: str = Field(..., description="Device type")
    subtype: str = Field(..., description="Device subtype")
    enabled: bool = Field(True, description="Whether device is enabled")
    protocol: Optional[str] = Field(None, description="Device protocol")
    
    # Network device fields
    host: Optional[str] = Field(None, description="Device hostname/IP")
    port: Optional[int] = Field(None, description="Device port")
    username: Optional[str] = Field(None, description="Authentication username")
    password: Optional[str] = Field(None, description="Authentication password")
    
    # Remote desktop specific fields
    domain: Optional[str] = Field(None, description="Domain for RDP authentication")
    width: Optional[int] = Field(1920, description="Remote desktop width")
    height: Optional[int] = Field(1080, description="Remote desktop height")
    refresh_rate: Optional[int] = Field(30, description="Remote desktop refresh rate in Hz")
    
    # Camera specific fields
    resolution: Optional[str] = Field(None, description="Camera resolution")
    framerate: Optional[int] = Field(None, description="Camera framerate")
    format: Optional[str] = Field(None, description="Camera pixel format")
    
    # Audio specific fields
    channels: Optional[int] = Field(None, description="Audio channels")
    sample_rate: Optional[int] = Field(None, description="Audio sample rate")
    sample_format: Optional[str] = Field(None, description="Audio sample format")
    
    # Additional configuration
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional device options")
    capabilities: List[str] = Field(default_factory=list, description="Device capabilities")

    @validator('type')
    def validate_type(cls, v):
        """Validate device type."""
        valid_types = [
            DEVICE_TYPE_CAMERA,
            DEVICE_TYPE_MICROPHONE,
            DEVICE_TYPE_SCREEN,
            DEVICE_TYPE_REMOTE_DESKTOP
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid device type: {v}")
        return v

    @validator('subtype')
    def validate_subtype(cls, v):
        """Validate device subtype."""
        valid_subtypes = [
            DEVICE_SUBTYPE_USB,
            DEVICE_SUBTYPE_IP,
            DEVICE_SUBTYPE_RDP,
            DEVICE_SUBTYPE_VNC
        ]
        if v not in valid_subtypes:
            raise ValueError(f"Invalid device subtype: {v}")
        return v

    @validator('protocol')
    def validate_protocol(cls, v):
        """Validate device protocol."""
        if v is None:
            return v
        valid_protocols = [
            DEVICE_PROTOCOL_RTSP,
            DEVICE_PROTOCOL_ONVIF,
            DEVICE_PROTOCOL_RDP,
            DEVICE_PROTOCOL_VNC
        ]
        if v not in valid_protocols:
            raise ValueError(f"Invalid device protocol: {v}")
        return v

    @validator('width', 'height')
    def validate_dimensions(cls, v):
        """Validate screen dimensions."""
        if v is not None and v <= 0:
            raise ValueError("Dimensions must be positive")
        return v

    @validator('refresh_rate')
    def validate_refresh_rate(cls, v):
        """Validate refresh rate."""
        if v is not None and v <= 0:
            raise ValueError("Refresh rate must be positive")
        return v

    class Config:
        """Pydantic configuration."""
        
        extra = "allow"  # Allow extra fields
