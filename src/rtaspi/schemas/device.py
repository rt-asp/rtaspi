"""Device configuration schema."""

from enum import Enum, auto
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator


from ..constants.devices import (
    DeviceType, DeviceSubType, DeviceProtocol,
    DeviceCapability, DeviceState, DeviceCategory
)


class DeviceAuth(BaseModel):
    """Device authentication configuration."""
    
    username: Optional[str] = Field(None, description="Authentication username")
    password: Optional[str] = Field(None, description="Authentication password")
    domain: Optional[str] = Field(None, description="Domain for authentication")
    token: Optional[str] = Field(None, description="Authentication token")
    key_file: Optional[str] = Field(None, description="Path to key file")
    cert_file: Optional[str] = Field(None, description="Path to certificate file")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional auth options")


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
    refresh_rate: Optional[int] = Field(
        30, description="Remote desktop refresh rate in Hz"
    )

    # Camera specific fields
    resolution: Optional[str] = Field(None, description="Camera resolution")
    framerate: Optional[int] = Field(None, description="Camera framerate")
    format: Optional[str] = Field(None, description="Camera pixel format")

    # Audio specific fields
    channels: Optional[int] = Field(None, description="Audio channels")
    sample_rate: Optional[int] = Field(None, description="Audio sample rate")
    sample_format: Optional[str] = Field(None, description="Audio sample format")

    # Additional configuration
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Additional device options"
    )
    capabilities: List[str] = Field(
        default_factory=list, description="Device capabilities"
    )

    @validator("type")
    def validate_type(cls, v):
        """Validate device type."""
        try:
            return DeviceType[v.upper()].value
        except KeyError:
            raise ValueError(f"Invalid device type: {v}")

    @validator("subtype")
    def validate_subtype(cls, v):
        """Validate device subtype."""
        try:
            return DeviceSubType[v.upper()].value
        except KeyError:
            raise ValueError(f"Invalid device subtype: {v}")

    @validator("protocol")
    def validate_protocol(cls, v):
        """Validate device protocol."""
        if v is None:
            return v
        try:
            return DeviceProtocol[v.upper()].value
        except KeyError:
            raise ValueError(f"Invalid device protocol: {v}")

    @validator("width", "height")
    def validate_dimensions(cls, v):
        """Validate screen dimensions."""
        if v is not None and v <= 0:
            raise ValueError("Dimensions must be positive")
        return v

    @validator("refresh_rate")
    def validate_refresh_rate(cls, v):
        """Validate refresh rate."""
        if v is not None and v <= 0:
            raise ValueError("Refresh rate must be positive")
        return v

    class Config:
        """Pydantic configuration."""

        extra = "allow"  # Allow extra fields


class DeviceConnection(BaseModel):
    """Device connection information."""

    host: str = Field(..., description="Device hostname/IP")
    port: Optional[int] = Field(None, description="Device port")
    protocol: Optional[str] = Field(None, description="Connection protocol")
    auth: Optional[DeviceAuth] = Field(None, description="Authentication details")
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Connection options"
    )


class DeviceStatus(BaseModel):
    """Device status information."""

    connected: bool = Field(False, description="Whether device is connected")
    active: bool = Field(False, description="Whether device is actively streaming")
    error: Optional[str] = Field(None, description="Last error message if any")
    last_seen: Optional[float] = Field(None, description="Timestamp of last contact")
    stats: Dict[str, Any] = Field(default_factory=dict, description="Device statistics")


class DeviceList(BaseModel):
    """List of device configurations."""

    devices: List[DeviceConfig] = Field(
        default_factory=list, description="List of device configurations"
    )
